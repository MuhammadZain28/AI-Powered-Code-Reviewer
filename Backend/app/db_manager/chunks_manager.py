from app.db_manager.database import Database

class ChunkManager:
    def __init__(self):
        self.db = Database()

    def insert_chunk(self, file_id: int, chunk_type: int, name: str, start_line: int, end_line: int, content: str, embedding_id: str):
        query = """
        INSERT INTO chunks (file_id, chunk_type, name, start_line, end_line, content, embedding_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id;
        """
        return self.db.fetchrow(query, file_id, chunk_type, name, start_line, end_line, content, embedding_id)

    def delete_chunks(self, file_id: int):
        query = "DELETE FROM chunks WHERE file_id = $1;"
        self.db.execute(query, file_id)

    def update_chunk_embedding_id(self, chunk_id: int, new_embedding_id: str):
        query = "UPDATE chunks SET embedding_id = $1 WHERE id = $2;"
        self.db.execute(query, new_embedding_id, chunk_id)

    def get_chunks_by_file_id(self, file_id: int):
        query="""SELECT id, file_id, chunk_type, name, start_line, end_line, content, embedding_id FROM chunks WHERE file_id = $1;"""
        return self.db.fetch(query, file_id)

    def get_chunks_by_embedding_id(self, embedding_id: str):
        query="""SELECT id, file_id, chunk_type, name, start_line, end_line, content, embedding_id FROM chunks WHERE embedding_id = $1;"""
        return self.db.fetch(query, embedding_id)