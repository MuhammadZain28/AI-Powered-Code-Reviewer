import os
from app.managers.database import Database
from app.utils.logger import get_logger

class Project:
    def __init__(self, id: str = None, name: str = "", path: str = "", description: str = ""):
        self.id = id
        self.name = name
        self.path = path
        self.description = description
        self.__logger = get_logger("Project")

    async def insert(self, name, path, description, features: str = None, modules: str = None, frontend: str = None, backend: str = None, technologies: str = None):
        if not os.path.exists(path):
            self.__logger.warning("Project path does not exist. Please provide a valid path.")
            return False
        if os.path.isfile(path):
            self.__logger.warning("Project path is a file. Please provide a valid directory path.")
            return False
        if self.id is None:
            db = Database()
            query = "INSERT INTO projects (name, path, description, features, modules, frontend, backend, technologies) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id"
            result = await db.fetchrow(query, name, path, description, features, modules, frontend, backend, technologies)
            self.id = result[0]

            self.__logger.info(f"Inserted new project with ID {self.id}")
            return True
        else:
            db = Database()
            query = "UPDATE projects SET name = $1, path = $2, description = $3, features = $4, modules = $5, frontend = $6, backend = $7, technologies = $8 WHERE id = $9"
            await db.execute(query, name, path, description, features, modules, frontend, backend, technologies, self.id)
            self.__logger.info(f"Updated project with ID {self.id}")
            return True

    async def delete(self):
        if self.id is not None:
            db = Database()
            query = "DELETE FROM projects WHERE id = $1"
            await db.execute(query, self.id)
            self.__logger.info(f"Deleted project with ID {self.id}")
            return True
        else:
            self.__logger.warning("Attempted to delete a project that does not exist in the database.")
            return False

    async def fetch(self):
        if self.id is not None:
            db = Database()
            query = "SELECT p.id, p.name, p.path, p.description, f.path FROM projects p JOIN files f ON p.id = f.project_id WHERE p.id = $1"
            result = await db.fetch(query, self.id)
            if result:
                self.id = result[0]['id']
                self.name = result[0]['name']
                self.path = result[0]['path']
                self.description = result[0]['description']
                self.files = [r['path'] for r in result]
                return self
            else:
                self.__logger.warning(f"Project with ID {self.id} not found in the database.")
                return None
        else:
            self.__logger.warning("Attempted to retrieve a project that does not exist in the database.")
            return None

    async def fetch_all(self):
        db = Database()
        query = "SELECT * FROM projects"
        result = await db.fetch(query)
        return [Project(id=p['id'], name=p['name'], path=p['path'], description=p['description']) for p in result]
