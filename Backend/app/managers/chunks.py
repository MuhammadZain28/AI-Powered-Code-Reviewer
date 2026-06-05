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
        query = "SELECT array_agg(embedding_id) FROM chunks JOIN chunks ON chunks.chunk_id = chunks.id WHERE chunks.project_id = $1"
        result = await db.fetch_values(query, project_id)
        if result:
            return result
        return None

    async def fetch_chunk_by_id(self, chunk_id: list, score: list):
        db = Database()
        ids = []
        score_map = {}
        query = """
SELECT chunk_type, name, parameters, return_values, complexity, hash, docstring, calls
FROM chunks
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

    async def fetch_chunk_context(self, chunk_id):
        db = Database()
        result = {}
        query = "SELECT public.get_function_context($1);"
        record = await db.fetch(query, chunk_id)

        if record:
            for row in record:
                result = json.loads(row["get_function_context"])
            return result
        return None
