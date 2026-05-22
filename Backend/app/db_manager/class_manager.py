from app.db_manager.database import Database

class ClassManager:
    def __init__(self):
        self.db = Database()

    async def insert_class(self, file_id: int, name: str, start_line: int, end_line: int, docstring: str = None, inheritance: str = None):
        query = """
        INSERT INTO classes (file_id, name, start_line, end_line, docstring, inheritance)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id;
        """
        return await self.db.fetchrow(query, file_id, name, start_line, end_line, docstring, inheritance)

    async def get_classes_by_file_id(self, file_id: int):
        query = "SELECT id, file_id, name, start_line, end_line, docstring, inheritance FROM classes WHERE file_id = $1;"
        return await self.db.fetch(query, file_id)

    async def delete_classes_by_file_id(self, file_id: int):
        query = "DELETE FROM classes WHERE file_id = $1;"
        await self.db.execute(query, file_id)

    async def close(self):
        await self.db.disconnect()