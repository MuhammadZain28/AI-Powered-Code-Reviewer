from app.managers.database import Database
from app.utils.tokenizer import normalize

class Import:
    def __init__(self, file_id: str = None, id: int = None, type: str = None, source: str = None, import_statement: str = None, language: str = None, modules: list = [], aliases: list = []):
        self.id = id
        self.file_id = file_id
        self.type = type
        self.source = source
        self.language = language
        self.modules = modules
        self.aliases = aliases
        self.raw_import = import_statement

    async def save(self):

        if self.id is None:
            result = await self.__import_manager.insert_import(self.file_id, self.type, self.source, self.modules, self.aliases)
            self.id = result['id']
            return True
        else:
            return True

    async def fetch_file_imports(self, file_id: str):
        if self.file_id is not None:
            return await self.__import_manager.get_imports_by_file_id(file_id)
        else:
            return []

    async def save_all_imports(self, data: list):
        columns = ['id', 'file_id', 'type', 'source']
        await self.__import_manager.copy_import_table(data, columns)

    async def save_import_modules(self, data: list):
        await self.__import_manager.copy_import_modules_table(data, ['import_id', 'module', 'alias'])