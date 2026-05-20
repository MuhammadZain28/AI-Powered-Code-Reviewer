from app.db_manager.import_manager import ImportManager

class Import:
    def __init__(self, id: int, file_id: int, name: str = None, type: str = None, source: str = None, alias: str = None, import_statement: str = None, language: str = None):
        self.id = id
        self.file_id = file_id
        self.type = type
        self.source = source
        self.language = language
        self.alias = alias
        self.modules = []
        self.raw_import = import_statement
        self.__import_manager = ImportManager()

    async def save(self):
        if self.id is None:
            result = await self.__import_manager.insert_import(self.file_id, self.name, self.type, self.source, self.alias, self.modules)
            self.id = result['id']
            return True
        else:
            return True

    async def fetch_file_imports(self, file_id: int):
        if self.file_id is not None:
            return await self.__import_manager.get_imports_by_file_id(file_id)
        else:
            return []

    def normalize_import(self):
        if self.language == "python":
            self.normalize_py()
        return {
            "type": self.type,
            "source": self.source,
            "alias": self.alias,
            "modules": self.modules
        }
    def normalize_py(self):
        if self.raw_import.startswith("import "):
            self.type = "module"
            parts = self.raw_import.split()
            self.modules.append(parts[1].strip())
            if " as " in parts:
                self.alias = parts[-1].strip()
        elif self.raw_import.startswith("from "):
            self.type = "module"
            parts = self.raw_import.split()
            self.source = parts[1]
            if "import" in parts:
                self.modules = [part.strip() for part in parts[3:] if part.strip() != "as"]
                if "as" in parts:
                    self.alias = parts[-1].strip()