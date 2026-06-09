import asyncio
from datetime import datetime, timezone
import json
from app.managers.reviews import Review
from app.managers.database import Database
from app.utils.logger import get_logger
class Chunk:
    def __init__(self, id: int = None, chunk_id: int = None, chunk_type: int = None, name: str = None, start_line: int = None, end_line: int = None, content: str = None, parameters: list = [], return_values: list = [], complexity: dict = {}, hash: str = "", docstring: str = "", calls: list = [], class_id: int = None):
        self.id = id
        self.chunk_id = chunk_id
        self.class_id = class_id
        self.chunk_type = chunk_type
        self.name = name
        self.start_line = start_line
        self.end_line = end_line
        self.content = content
        self.parameters = parameters
        self.return_values = return_values
        self.complexity = complexity
        self.hash = hash
        self.docstring = docstring
        self.calls = calls
        self.__logger = get_logger("Chunk")

    async def fetch_embedding_id(self, project_id):
        db = Database()
        query = "SELECT array_agg(embedding_id ORDER BY embedding_id) FROM chunks JOIN files ON chunks.file_id = files.id WHERE files.project_id = $1"
        result = await db.fetch_values(query, project_id)
        if result:
            return result
        return None

    async def fetch_chunk_by_id(self, chunk_id: list, score: list):
        db = Database()
        ids = []
        score_map = {}
        query = """
SELECT chunk_type, name, parameters, return_values, complexity, chunks.hash, docstring, embedding_id, content, start_line, end_line, class_id, class_name, files.id as file_id, files.path as file_path
FROM chunks JOIN files ON chunks.file_id = files.id
WHERE embedding_id = ANY($1::bigint[])
"""
        
        for c_id, s in zip(chunk_id, score):
            score_map[int(c_id)] = float(s)
            ids.append(int(c_id))

        rows = await db.fetch(query, ids)

        results = []

        for row in rows:
            row = dict(row)
            row["score"] = score_map[row["embedding_id"]]
            results.append(row)

        return results
    
    async def fetch_chunks_hash(self, files: list):
        db = Database()
        query = """
        SELECT 
            files.id, 
            files.project_id, 
            files.language, 
            files.path, 
            classes.id as class_id, 
            classes.name as class_name, 
            classes.hash as class_hash,
            chunks.id as chunk_id, 
            chunks.name, 
            chunks.hash 
        FROM files 
        LEFT JOIN chunks ON chunks.file_id = files.id 
        LEFT JOIN classes ON files.id = classes.file_id WHERE files.path = ANY($1::Text[])
        """
        rows = await db.fetch(query, files)
        class_map = {}
        chunk_map = {}
        files_in_db = {}
        for row in rows:
            chunk_map[row["name"]] = {"id": row["chunk_id"], "hash": row["hash"]}
            class_map[row["class_name"]] = {"id": row["class_id"], "hash": row["class_hash"]}
            files_in_db[row["id"]] = {"project_id": row["project_id"], "language": row["language"], "path": row["path"]}

        self.__logger.info(f"Fetched {len(chunk_map)} chunks from database for change management")
        return {"chunk_map": chunk_map, "class_map": class_map, "files_in_db": files_in_db}

    async def managed_changed_chunks(self, changed_chunks: list):
        db = Database()

        chunks = []
        ids = []
        queue = []

        for chunk in changed_chunks:
            ids.append(str(chunk[0]))
            if chunk[9] > 15:
                queue.append((chunk[0], chunk[9], datetime.now(), "pending"))

            chunks.append({
                "id": str(chunk[0]),
                "file_id": str(chunk[1]),
                "class_id": str(chunk[2]),
                "class_name": chunk[3],
                "name": chunk[4],
                "content": chunk[5],
                "start_line": chunk[6],
                "end_line": chunk[7],
                "chunk_type": chunk[8],
                "score": chunk[9],
                "hash": chunk[10],
                "docstring": chunk[11],
                "parameters": chunk[12],
                "return_values": chunk[13] if chunk[13] else [],
                "complexity": chunk[14]
            })

        query = """
INSERT INTO chunks (
    id,
    file_id,
    class_id,
    class_name,
    name,
    content,
    start_line,
    end_line,
    chunk_type,
    score,
    hash,
    docstring,
    parameters,
    return_values,
    complexity
)
SELECT *
FROM jsonb_to_recordset($1::jsonb) AS u(
    id uuid,
    file_id uuid,
    class_id uuid,
    class_name text,
    name text,
    content text,
    start_line int,
    end_line int,
    chunk_type text,
    score decimal,
    hash text,
    docstring text,
    parameters text[],
    return_values text[],
    complexity int
)
ON CONFLICT (id)
DO UPDATE
SET
    file_id       = EXCLUDED.file_id,
    class_id      = EXCLUDED.class_id,
    class_name    = EXCLUDED.class_name,
    name          = EXCLUDED.name,
    content       = EXCLUDED.content,
    start_line    = EXCLUDED.start_line,
    end_line      = EXCLUDED.end_line,
    chunk_type    = EXCLUDED.chunk_type,
    score         = EXCLUDED.score,
    hash          = EXCLUDED.hash,
    docstring     = EXCLUDED.docstring,
    parameters    = EXCLUDED.parameters,
    return_values = EXCLUDED.return_values,
    complexity    = EXCLUDED.complexity;
"""
        
        delete_related_calls_query = """
DELETE FROM calls
USING unnest($1::uuid[]) AS u(id)
WHERE calls.caller_id = u.id OR calls.callee_id = u.id;
"""

        delete_related_review_query = """
    DELETE FROM reviews
    USING unnest($1::uuid[]) AS u(id)
    WHERE reviews.chunk_id = u.id;
    """

        delete_related_summaries_query = """
    DELETE FROM summaries
    USING unnest($1::uuid[]) AS u(id)
    WHERE summaries.chunk_id = u.id;
    """

        delete_related_queue_query = """
DELETE FROM review_queue
USING unnest($1::uuid[]) AS u(id)
WHERE review_queue.chunk_id = u.id;
"""

        review_manager = Review()

        result = await asyncio.gather(
            db.execute(query, json.dumps(chunks)),
            db.execute(delete_related_calls_query, ids),
            db.execute(delete_related_review_query, ids),
            db.execute(delete_related_summaries_query, ids),
            db.execute(delete_related_queue_query, ids)
        )
        
        record = await review_manager.build_queue(queue)
    
        self.__logger.info(f"Updated {len(result)} chunks in database for change management. Queue records inserted: {record}")
        
        return result