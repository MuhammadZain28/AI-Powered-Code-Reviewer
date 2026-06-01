from app.managers.database import Database
class Call:
    def __init__(self, id: int = None, caller_id: int = None, function_name: str = None, library: str = None, call_type: str = None, resolve_to: str = None):
        self.id = id
        self.caller_id = caller_id
        self.function_name = function_name
        self.library = library
        self.call_type = call_type
        self.resolve_to = resolve_to

    async def save(self):
        if self.id is None:
            query = "INSERT INTO calls (caller_id, call_type, function_name, source, resolve_to, library) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id"
            result = await Database().fetchrow(query, (self.caller_id, self.call_type, self.function_name, None, self.resolve_to, self.library))
            self.id = result
            return True
        else:
            return True

