import os
from app.db_manager.project_manager import ProjectManager
from app.utils.logger import get_logger

class Project:
    def __init__(self, id: str, name: str, path: str, description: str):
        self.id = id
        self.name = name
        self.path = path
        self.description = description
        self.__project_manager = ProjectManager()
        self.__logger = get_logger("Project")

    async def save(self):
        if not os.path.exists(self.path):
            self.__logger.warning("Project path does not exist. Please provide a valid path.")
            return False
        if os.path.isfile(self.path):
            self.__logger.warning("Project path is a file. Please provide a valid directory path.")
            return False
        if self.id is None:
            result = await self.__project_manager.create_project(self.name, self.path, self.description)
            self.id = result['id']
            self.__logger.info(f"Inserted new project with ID {self.id}")
            return True
        else:
            await self.__project_manager.update_project(self.id, self.name, self.path, self.description)
            self.__logger.info(f"Updated project with ID {self.id}")
            return True

    async def delete(self):
        if self.id is not None:
            await self.__project_manager.delete_project(self.id)
            self.__logger.info(f"Deleted project with ID {self.id}")
            return True
        else:
            self.__logger.warning("Attempted to delete a project that does not exist in the database.")
            return False

    async def fetch(self):
        if self.id is not None:
            return await self.__project_manager.get_project_by_id(self.id)
        else:
            self.__logger.warning("Attempted to retrieve a project that does not exist in the database.")
            return None

    async def fetch_all(self):
        return await self.__project_manager.get_all_projects()
