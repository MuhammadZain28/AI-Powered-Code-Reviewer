from app.db_manager.database import Database
import re

class CallManager:
    def __init__(self):
        self.db = Database()

    async def insert_call(self, caller_id: int, function_name: str, library: str = None, call_type: str = None, resolve_to: str = None):

        query = """
        INSERT INTO calls (caller_id, function_name, library, call_type, resolve_to)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (caller_id, function_name) DO NOTHING
        RETURNING id;
        """

        return await self.db.fetchrow(query, caller_id, function_name, library, call_type, resolve_to)

    async def get_calls_by_chunk_id(self, chunk_id: int):
        query = "SELECT id, chunk_id, function_name FROM calls WHERE chunk_id = $1;"
        return await self.db.fetch(query, chunk_id)

    async def delete_calls_by_chunk_id(self, chunk_id: int):
        query = "DELETE FROM calls WHERE chunk_id = $1;"
        await self.db.execute(query, chunk_id)
