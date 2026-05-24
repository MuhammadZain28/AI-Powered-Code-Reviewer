from app.db_manager.import_manager import ImportManager
from app.utils.tokenizer import normalize

class Import:
    def __init__(self, file_id: str, id: int = None, type: str = None, source: str = None, import_statement: str = None, language: str = None, modules: list = [], aliases: list = []):
        self.id = id
        self.file_id = file_id
        self.type = type
        self.source = source
        self.language = language
        self.modules = modules
        self.aliases = aliases
        self.raw_import = import_statement
        self.__import_manager = ImportManager()

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

    async def saving_imports(self, import_statement):
        for stmt in import_statement:
            normalized = normalize(stmt['raw'], stmt['language'])
            normalized = normalized.to_dict()
            import_obj = Import(id=None, file_id="677f1e7f-98bf-4e37-ac83-c321324525f9", type=normalized['type'], source=normalized['source'], import_statement=stmt['raw'], language=stmt['language'], modules=normalized['modules'], aliases=normalized['aliases'])
            _ = await import_obj.save()
