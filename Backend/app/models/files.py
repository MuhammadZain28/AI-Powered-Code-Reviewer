from app.db_manager.files_manager import FileManager
from app.utils.logger import get_logger


class File:
    def __init__(self, id: int, project_id: int, path: str, language: str, hash: str):
        self.id = id
        self.project_id = project_id
        self.path = path
        self.language = language
        self.hash = hash
        self.__file_manager = FileManager()
        self.__logger = get_logger("File")

    def save_all(self, files: list):
        try:
            for file in files:
                self.path = file['path']
                self.language = file['language']
                self.hash = file['hash']
                self.save()
        except Exception as e:
            self.__logger.error(f"Error saving files for project {self.project_id}: {str(e)}")

    def save(self):
        if self.id is None:
            result = self.__file_manager.insert_file(self.project_id, self.path, self.language, self.hash)
            self.id = result['id']
            self.__logger.info(f"Inserted new file with ID {self.id} for project {self.project_id}")
        else:
            self.__file_manager.update_file_hash(self.id, self.hash)
            self.__logger.info(f"Updated hash for file ID {self.id} in project {self.project_id}")

    def delete(self):
        if self.id is not None:
            self.__file_manager.delete_file(self.id)
            self.__logger.info(f"Deleted file with ID {self.id} from project {self.project_id}")
        else:
            self.__logger.warning("Attempted to delete a file that does not exist in the database.")

    def fetch_file(self, file_id: int):
        if self.id is not None:
            return self.__file_manager.get_file_by_id(file_id)
        else:
            self.__logger.warning("Attempted to retrieve a file that does not exist in the database.")
            return None

    def fetch_project_files(self, project_id: int):
        if self.project_id is not None:
            return self.__file_manager.get_files_by_project_id(project_id)
        else:
            self.__logger.warning("Attempted to retrieve files for a project that does not exist in the database.")
            return []