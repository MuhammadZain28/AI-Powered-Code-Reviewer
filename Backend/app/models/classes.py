from app.db_manager.class_manager import ClassManager
from app.db_manager.attribute_manager import AttributeManager

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
        self.__attribute_manager = AttributeManager()
        self.__class_manager = ClassManager()

    async def save(self):
        if self.id is None:
            result = await self.__class_manager.insert_class(self.file_id, self.name, self.start_line, self.end_line, self.docstring)
            self.id = result['id']

            for attr in self.attributes:
                await self.__attribute_manager.insert_attribute(self.id, attr['name'], attr['type'], attr['default_value'], attr.get('is_static', False))
            return True
        else:
            return True

    async def save_all(self, data: list):
        await self.__class_manager.copy_table(data, columns=['id', 'file_id', 'name', 'start_line', 'end_line', 'docstring', 'inheritance'])

    async def save_attributes(self, attributes: list):
        await self.__attribute_manager.copy_attributes_table(attributes, columns=['class_id', 'name', 'attribute_type', 'default_value', 'is_static'])