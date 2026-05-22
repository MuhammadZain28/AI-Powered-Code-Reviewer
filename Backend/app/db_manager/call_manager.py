from app.db_manager.database import Database

class CallManager:
    def __init__(self):
        self.db = Database()

    async def insert_call(self, caller_id: int, function: str, import_id: int = None, callee_id: int = None):
        if callee_id is None:
            call_type = "library function call"
        elif import_id is not None:
            call_type = "internal function call"
        else:
            call_type = "external function call"
        query = """
        INSERT INTO calls (caller_id, function, import_id, callee_id, call_type)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id;
        """
        return await self.db.fetchrow(query, caller_id, function, import_id, callee_id, call_type)

    async def get_calls_by_chunk_id(self, chunk_id: int):
        query = "SELECT id, chunk_id, function FROM calls WHERE chunk_id = $1;"
        return await self.db.fetch(query, chunk_id)

    async def delete_calls_by_chunk_id(self, chunk_id: int):
        query = "DELETE FROM calls WHERE chunk_id = $1;"
        await self.db.execute(query, chunk_id)