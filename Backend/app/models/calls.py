from app.db_manager.call_manager import CallManager

class Call:
    def __init__(self, id: int = None, caller_id: int = None, function_name: str = None, library: str = None, call_type: str = None, resolve_to: str = None):
        self.id = id
        self.caller_id = caller_id
        self.function_name = function_name
        self.library = library
        self.call_type = call_type
        self.resolve_to = resolve_to
        self.__call_manager = CallManager()

    async def save(self):
        if self.id is None:
            result = await self.__call_manager.insert_call(self.caller_id, self.function_name, self.library, self.call_type, self.resolve_to)
            self.id = result['id']
            return True
        else:
            return True

    async def delete_by_chunk_id(self, chunk_id: int):
        await self.__call_manager.delete_calls_by_chunk_id(chunk_id)

    async def fetch_by_chunk_id(self, chunk_id: int):
        return await self.__call_manager.get_calls_by_chunk_id(chunk_id)

    async def save_all(self, data: list):
        await self.__call_manager.copy_calls_table(data, columns=['caller_id', 'call_type', 'function_name', 'source', 'library', 'resolve_to'])