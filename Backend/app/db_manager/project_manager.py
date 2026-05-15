from app.db_manager.database import Database

class ProjectManager:
    def __init__(self):
        self.db = Database()

    async def create_project(self, name: str, path: str, description: str):
        query = """
        INSERT INTO projects (name, path, description)
        VALUES ($1, $2, $3)
        RETURNING id;
        """
        return await self.db.fetchrow(query, name, path, description)

    async def update_project(self, project_id: str, name: str, path: str, description: str):
        query = """
        UPDATE projects
        SET name = $1, path = $2, description = $3
        WHERE id = $4;
        """
        await self.db.execute(query, name, path, description, project_id)

    async def get_project_by_id(self, project_id: str):
        query = "SELECT id, name, path, description FROM projects WHERE id = $1;"
        return await self.db.fetchrow(query, project_id)

    async def get_all_projects(self):
        query = "SELECT id, name, path, description FROM projects;"
        return await self.db.fetch(query)

    async def delete_project(self, project_id: str):
        query = "DELETE FROM projects WHERE id = $1;"
        await self.db.execute(query, project_id)

    async def close(self):
        await self.db.disconnect()
