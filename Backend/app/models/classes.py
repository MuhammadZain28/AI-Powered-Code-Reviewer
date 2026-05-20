from app.db_manager.class_manager import ClassManager

class Class:
    def __init__(self, id: int, file_id: int, name: str, start_line: int, end_line: int, docstring: str, inheritances: list = []):
        self.id = id
        self.file_id = file_id
        self.name = name
        self.start_line = start_line
        self.end_line = end_line
        self.docstring = docstring
        self.inheritances = inheritances
        self.__class_manager = ClassManager()

    async def save(self):
        if self.id is None:
            result = await self.__class_manager.insert_class(self.file_id, self.name, self.start_line, self.end_line, self.docstring)
            self.id = result['id']
            return True
        else:
            return True