import json

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
SELECT chunk_type, name, parameters, return_values, complexity, hash, docstring, embedding_id, content
FROM chunks
WHERE embedding_id = ANY($1::bigint[])
"""
        for c_id, s in zip(chunk_id, score):
            score_map[int(c_id)] = float(s)
            ids.append(int(c_id))

        print(f"Fetching chunks with IDs: {ids}")
        rows = await db.fetch(query, ids)

        results = []

        for row in rows:
            row = dict(row)
            row["score"] = score_map[row["embedding_id"]]
            results.append(row)

        return results
