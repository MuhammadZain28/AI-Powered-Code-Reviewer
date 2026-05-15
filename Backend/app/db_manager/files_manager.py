from app.db_manager.database import Database

class FileManager:
    def __init__(self):
        self.db = Database()

    async def insert_file(self, project_id: str, path: str, language: str, hash: str):
        query = """
        INSERT INTO files (project_id, path, language, hash)
        VALUES ($1, $2, $3, $4)
        RETURNING id;
        """
        return await self.db.fetchrow(query, project_id, path, language, hash)

    async def get_file_by_id(self, file_id: str):
        query = "SELECT id, project_id, path, language, hash FROM files WHERE id = $1;"
        return await self.db.fetchrow(query, file_id)

    async def get_files_by_project_id(self, project_id: str):
        query = "SELECT id, project_id, path, language, hash FROM files WHERE project_id = $1;"
        return await self.db.fetch(query, project_id)

    async def get_uploaded_files(self):
        query = "SELECT id, path, language, hash FROM files WHERE project_id IS NULL;"
        return await self.db.fetch(query)

    async def delete_file(self, file_id: str):
        query = "DELETE FROM files WHERE id = $1;"
        await self.db.execute(query, file_id)

    async def update_file_hash(self, file_id: str, new_hash: str):
        query = "UPDATE files SET hash = $1 WHERE id = $2;"
        await self.db.execute(query, new_hash, file_id)

    async def close(self):
        await self.db.disconnect()