from app.managers.database import Database

class Class:
    def __init__(self, id: int = None, file_id: int = None, name: str = None, start_line: int = None, end_line: int = None, docstring: str = None, attributes: list = [], inheritances: list = []):
        self.id = id
        self.file_id = file_id
        self.name = name
        self.start_line = start_line
        self.attributes = attributes
        self.end_line = end_line
        self.docstring = docstring
        self.inheritances = inheritances
