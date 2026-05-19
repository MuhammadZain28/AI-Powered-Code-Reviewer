from app.db_manager.database import Database

class AttributeManager:
    def __init__(self):
        self.db = Database()

    async def insert_attribute(self, class_id: int, name: str, attribute_type: str, default_value: str, is_static: bool = False):
        query = """
        INSERT INTO attributes (class_id, name, attribute_type, default_value, is_static)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id;
        """
        return await self.db.fetchrow(query, class_id, name, attribute_type, default_value, is_static)

    async def get_attributes_by_class_id(self, class_id: int):
        query = "SELECT id, class_id, name, attribute_type, default_value, is_static FROM attributes WHERE class_id = $1;"
        return await self.db.fetch(query, class_id)

    async def delete_attributes_by_class_id(self, class_id: int):
        query = "DELETE FROM attributes WHERE class_id = $1;"
        await self.db.execute(query, class_id)