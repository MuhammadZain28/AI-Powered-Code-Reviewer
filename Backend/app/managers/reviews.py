from app.managers.database import Database

class Review:
    def __init__(self, id: int = None, chunk_id: int = None, issue_type: str = None, description: str = None, severity: str = None, suggested_fix: str = None):
        self.id = id
        self.chunk_id = chunk_id
        self.issue_type = issue_type
        self.description = description
        self.severity = severity
        self.suggested_fix = suggested_fix

    async def insert(self, review_data: dict):
        db = Database()
        table = []
        columns = ["chunk_id", "purpose", "severity", "category", "explanation", "suggested_fix"]
        for issue in review_data:
            print(f"Inserting review issue: {issue}")
            table.append((
                issue.get("chunk_id"),
                issue.get("purpose"),
                issue.get("severity"),
                issue.get("category"),
                issue.get("explanation"),
                issue.get("suggested_fix")
            ))
        result = await db.copy_to_table("reviews", data=table, columns=columns)
        return result