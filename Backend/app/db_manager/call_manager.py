from app.db_manager.database import Database
import re

CALL_PATTERNS = [
    ("::", re.compile(r"^(.*?)::([A-Za-z_][A-Za-z0-9_]*)$")),
    ("->", re.compile(r"^(.*?)->([A-Za-z_][A-Za-z0-9_]*)$")),
    (".",  re.compile(r"^(.*?)\.([A-Za-z_][A-Za-z0-9_]*)$")),
]

class CallManager:
    def __init__(self):
        self.db = Database()

    async def insert_call(self, caller_id: int, file_id: str, function: str, import_id: int = None, callee_id: int = None):
        call_type = "library function call"

        call_parts = self.extract_call_parts(function)
        parent = call_parts["parent_name"]
        function_name = call_parts["function_name"]
        operator = call_parts["call_operator"]

        query = """
        INSERT INTO calls (caller_id, file_id, function_name, parent_name, call_operator, import_id, callee_id, call_type)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id;
        """
        return await self.db.fetchrow(query, caller_id, file_id, function_name, parent, operator, import_id, callee_id, call_type)

    async def get_calls_by_chunk_id(self, chunk_id: int):
        query = "SELECT id, chunk_id, function_name FROM calls WHERE chunk_id = $1;"
        return await self.db.fetch(query, chunk_id)

    async def delete_calls_by_chunk_id(self, chunk_id: int):
        query = "DELETE FROM calls WHERE chunk_id = $1;"
        await self.db.execute(query, chunk_id)

    def extract_call_parts(self, call_expression: str):
        """
        Extract:
            parent_name
            operator
            function_name

        Examples:
            self.save
            this->run
            User::create
            func
        """

        call_expression = call_expression.strip()

        for operator, pattern in CALL_PATTERNS:
            match = pattern.match(call_expression)

            if match:
                return {
                    "parent_name": match.group(1).strip(),
                    "call_operator": operator,
                    "function_name": match.group(2).strip()
                }

        # plain function call
        return {
            "parent_name": None,
            "call_operator": None,
            "function_name": call_expression
        }