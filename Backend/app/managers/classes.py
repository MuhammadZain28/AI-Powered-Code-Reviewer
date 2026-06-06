import asyncio
import json

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

    async def manage_change(self, changed_classes: list):
        db = Database()
        classes = []

        for c in changed_classes:
            classes.append({
                "id": str(c[0]),
                "file_id": str(c[1]),
                "name": c[2],
                "start_line": c[3],
                "end_line": c[4],
                "docstring": c[5],
                "inheritance": [c[6]] if c[6] else [],
                "hash": c[7]
            })

        print(f"Class '{classes}'")  # Debug print for inheritance

        query = """
INSERT INTO classes (id, file_id, name, start_line, end_line, docstring, inheritance, hash)
SELECT *
FROM jsonb_to_recordset($1::jsonb) AS u(
    id uuid,
    file_id uuid,
    name text,
    start_line int,
    end_line int,
    docstring text,
    inheritance text[],
    hash text
)
ON CONFLICT (id) DO UPDATE SET
    file_id = EXCLUDED.file_id,
    name = EXCLUDED.name,
    start_line = EXCLUDED.start_line,
    end_line = EXCLUDED.end_line,
    docstring = EXCLUDED.docstring,
    inheritance = EXCLUDED.inheritance,
    hash = EXCLUDED.hash
"""

        delete_related_chunks_query = """
            DELETE FROM class_attributes ca
            USING unnest($1::uuid[]) AS u(id)
            WHERE ca.class_id = u.id;
            """
        queries = [
            db.execute(query, json.dumps(classes)),
            db.execute(delete_related_chunks_query, [cls["id"] for cls in classes])
        ]
        result = await asyncio.gather(*queries)
        return result