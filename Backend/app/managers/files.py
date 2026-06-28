import asyncio
from dataclasses import dataclass
from app.managers.database import Database
from app.utils.logger import get_logger


@dataclass(frozen=True)
class FileRecord:
    id: str
    project_id: str
    path: str
    language: str
    hash: str

    def to_record(self):
        return (
            self.id,
            self.project_id,
            self.path,
            self.language,
            self.hash,
        )


@dataclass(frozen=True)
class FileHashUpdate:
    id: str
    hash: str

    def to_record(self):
        return (self.id, self.hash)


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


    async def manage_deleted_files(self, project_id: str, deleted_files: list):
        db = Database()

        query = """DELETE FROM files WHERE project_id = $1 AND path = ANY($2::text[])"""
        result = await db.execute(query, project_id, deleted_files)
        self.__logger.info(f"Deleted {result} entries from files table for deleted files: {deleted_files}")
        return result


    async def manage_changed_files(self, changed_files: list):
        db = Database()
        files = {'id': [], 'hash': []}
        for file in changed_files:
            if hasattr(file, "id") and hasattr(file, "hash"):
                files['id'].append(file.id)
                files['hash'].append(file.hash)
            else:
                files['id'].append(file[0])
                files['hash'].append(file[1])

        query = """UPDATE files SET hash = v.hash FROM unnest($1::uuid[], $2::text[]) AS v(id, hash) WHERE files.id = v.id"""
        delete_related_imports_query = """DELETE FROM imports WHERE file_id = ANY($1::uuid[])"""
        queries = [
            db.execute(query, files['id'], files['hash']),
            db.execute(delete_related_imports_query, files['id'])
        ]
        result = await asyncio.gather(*queries)
        self.__logger.info(f"Updated {result} entries in files table for changed files: {changed_files}")
        return result