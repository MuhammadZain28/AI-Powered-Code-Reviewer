from app.db_manager.database import Database

class ChunkManager:
    def __init__(self):
        self.db = Database()

    def insert_chunk(self, file_id: int, chunk_type: int, name: str, start_line: int, end_line: int, content: str):
        query = """
        INSERT INTO chunks (file_id, chunk_type, name, start_line, end_line, content)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id;
        """
        return self.db.fetchrow(query, file_id, chunk_type, name, start_line, end_line, content)
    def delete_chunks(self, file_id: int):
        query = "DELETE FROM chunks WHERE file_id = $1;"
        self.db.execute(query, file_id)

    def get_chunks_by_file_id(self, file_id: int):
        query="""SELECT id, file_id, chunk_type, name, start_line, end_line, content FROM chunks WHERE file_id = $1;"""
        return self.db.fetch(query, file_id)

    def get_chunks(self, embedding_id: str):
        query="""SELECT id, file_id, chunk_type, name, start_line, end_line, content FROM chunks WHERE id = $1;"""
        return self.db.fetch(query, embedding_id)