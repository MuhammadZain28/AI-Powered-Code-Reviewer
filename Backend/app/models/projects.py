import os
from app.db_manager.database import Database
from app.utils.logger import get_logger

class Project:
    def __init__(self, id: str, name: str, path: str, description: str, files: list = None):
        self.id = id
        self.name = name
        self.path = path
        self.description = description
        self.files = files if files is not None else []
        self.__logger = get_logger("Project")

    async def save(self):
        if not os.path.exists(self.path):
            self.__logger.warning("Project path does not exist. Please provide a valid path.")
            return False
        if os.path.isfile(self.path):
            self.__logger.warning("Project path is a file. Please provide a valid directory path.")
            return False
        if self.id is None:
            db = Database()
            query = "INSERT INTO projects (name, path, description) VALUES (%s, %s, %s) RETURNING id"
            result = await db.fetch_one(query, (self.name, self.path, self.description))
            self.id = result[0]
            self.__logger.info(f"Inserted new project with ID {self.id}")
            return True
        else:
            db = Database()
            query = "UPDATE projects SET name = %s, path = %s, description = %s WHERE id = %s"
            await db.execute(query, (self.name, self.path, self.description, self.id))
            self.__logger.info(f"Updated project with ID {self.id}")
            return True

    async def delete(self):
        if self.id is not None:
            db = Database()
            query = "DELETE FROM projects WHERE id = %s"
            await db.execute(query, (self.id,))
            self.__logger.info(f"Deleted project with ID {self.id}")
            return True
        else:
            self.__logger.warning("Attempted to delete a project that does not exist in the database.")
            return False

    async def fetch(self):
        if self.id is not None:
            db = Database()
            query = "SELECT p.id, p.name, p.path, p.description, f.path FROM projects p JOIN files f ON p.id = f.project_id WHERE p.id = %s"
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
