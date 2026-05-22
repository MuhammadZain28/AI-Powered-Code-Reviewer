from app.db_manager.chunks_manager import ChunkManager
from app.utils.logger import get_logger

class Chunk:
    def __init__(self, id: int, file_id: int, chunk_type: int, name: str, start_line: int, end_line: int, content: str, parameters: list = [], return_values: list = [], complexity: dict = {}, hash: str = "", docstring: str = "", class_id: int = None):
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
        self.__chunk_manager = ChunkManager()
        self.__logger = get_logger("Chunk")

    async def save(self):
        if self.id is None:
            result = await self.__chunk_manager.insert_chunk(self.file_id, self.chunk_type, self.name, self.start_line, self.end_line, self.content, self.parameters, self.return_values, self.complexity, self.hash, self.docstring, self.class_id)
            self.id = result['id']
            self.__logger.info(f"Inserted new chunk with ID {self.id} for file {self.file_id}")
            return True
        else:
            self.__logger.info(f"Updated embedding ID for chunk with ID {self.id} in file {self.file_id}")
            return True

    async def fetch_file_chunks(self, file_id: int):
        if self.file_id is not None:
            return await self.__chunk_manager.get_chunks_by_file_id(file_id)
        else:
            self.__logger.warning("Attempted to retrieve chunks for a file that does not exist in the database.")
            return []

    async def fetch(self):
        if self.id is not None:
            return await self.__chunk_manager.get_chunks(self.id)
        else:
            self.__logger.warning("Attempted to retrieve a chunk that does not exist in the database.")
            return None
