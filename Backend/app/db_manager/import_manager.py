from app.db_manager.database import Database

class ImportManager:
    def __init__(self):
        self.db = Database()

    async def insert_import(self, file_id: int, import_type: str, module: str, name: str, alias_name: str = None):
        query = """
        INSERT INTO imports (file_id, type, modules, name, alias_name)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id;
        """
        return await self.db.fetchrow(query, file_id, import_type, module, name, alias_name)

    async def get_imports_by_file_id(self, file_id: int):
        query = "SELECT id, file_id, type, modules, name, alias_name FROM imports WHERE file_id = $1;"
        return await self.db.fetch(query, file_id)

    async def delete_imports_by_file_id(self, file_id: int):
        query = "DELETE FROM imports WHERE file_id = $1;"
        await self.db.execute(query, file_id)