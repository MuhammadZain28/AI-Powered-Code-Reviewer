from app.db_manager.database import Database
from app.utils.logger import get_logger
class Chunk:
    def __init__(self, id: int = None, file_id: int = None, chunk_type: int = None, name: str = None, start_line: int = None, end_line: int = None, content: str = None, parameters: list = [], return_values: list = [], complexity: dict = {}, hash: str = "", docstring: str = "", calls: list = [], class_id: int = None):
        self.id = id
        self.file_id = file_id
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

    async def fetch_embedding_id(self):
        db = Database()
        query = "SELECT array_agg(embedding_id) FROM chunks"
        result = await db.fetch_values(query)
        if result:
            return result
        return None
