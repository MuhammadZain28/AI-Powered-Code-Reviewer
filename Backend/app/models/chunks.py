from app.db_manager.chunks_manager import ChunkManager
from app.utils.logger import get_logger

class Chunk:
    def __init__(self, id: int, file_id: int, chunk_type: int, name: str, start_line: int, end_line: int, content: str, embedding_id: str):
        self.id = id
        self.file_id = file_id
        self.chunk_type = chunk_type
        self.name = name
        self.start_line = start_line
        self.end_line = end_line
        self.content = content
        self.embedding_id = embedding_id
        self.chunk_manager = ChunkManager()
        self.logger = get_logger("Chunk")

    def save(self):
        if self.id is None:
            result = self.chunk_manager.insert_chunk(self.file_id, self.chunk_type, self.name, self.start_line, self.end_line, self.content, self.embedding_id)
            self.id = result['id']
            self.logger.info(f"Inserted new chunk with ID {self.id} for file {self.file_id}")
        else:
            self.chunk_manager.update_chunk_embedding_id(self.id, self.embedding_id)
            self.logger.info(f"Updated embedding ID for chunk with ID {self.id} in file {self.file_id}")
            pass

    def fetch_file_chunks(self, file_id: int):
        if self.file_id is not None:
            return self.chunk_manager.get_chunks_by_file_id(file_id)
        else:
            self.logger.warning("Attempted to retrieve chunks for a file that does not exist in the database.")
            return []

    def fetch_chunks_by_embedding_id(self, embedding_id: str):
        if self.embedding_id is not None:
            return self.chunk_manager.get_chunks_by_embedding_id(embedding_id)
        else:
            self.logger.warning("Attempted to retrieve chunks for an embedding that does not exist in the database.")
            return []