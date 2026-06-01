from app.managers.database import Database
from app.utils.logger import get_logger


class File:
    def __init__(self, id: int = None, project_id: int = None, path: str = None, language: str = None, hash: str = None):
        self.id = id
        self.project_id = project_id
        self.path = path
        self.language = language
        self.hash = hash
        self.chunks = []
        self.__logger = get_logger("File")

    async def scan_project(self) -> list:
        db = Database()
        query = "SELECT path, hash FROM files WHERE project_id = $1"
        result = await db.fetch(query, self.project_id)
        return result

    async def get_changed_files(self, project_id, current_hash):
        db = Database()
        query = "SELECT path FROM files WHERE project_id = $1 and hash = ANY($2::text[])"
        result = await db.fetch(query, project_id, current_hash)
        if result:
            return dict(result)
        return None