import asyncio
import json

from app.managers.database import Database

class Review:
    def __init__(self, id: int = None, chunk_id: int = None, issue_type: str = None, description: str = None, severity: str = None, suggested_fix: str = None):
        self.id = id
        self.chunk_id = chunk_id
        self.issue_type = issue_type
        self.description = description
        self.severity = severity
        self.suggested_fix = suggested_fix
    
    def flatten_reviews(self, data: dict):
        chunk_rows = []
        issue_rows = []
        for item in data:

            if isinstance(item, str):
                print(f"Skipping error: {item}")
                continue

            if not isinstance(item, dict):
                continue

            # each item is like: {chunk_id: {...}}
            for chunk_id, value in item.items():

                # -------- chunk table --------
                chunk_rows.append((
                    chunk_id,
                    value.get("purpose"),
                    value.get("module")
                ))

                # -------- issue table --------
                for issue in value.get("issues", []):
                    issue_rows.append((
                        chunk_id,
                        issue.get("severity"),
                        issue.get("category"),
                        issue.get("review"),
                        issue.get("suggested_fix")
                    ))

        return chunk_rows, issue_rows

    async def insert(self, review_data: dict):
        db = Database()

        summary, reviews = self.flatten_reviews(review_data)
        
        result = await asyncio.gather(
            db.copy_to_table("summaries", data=summary, columns=["chunk_id", "purpose", "module"]),
            db.copy_to_table("reviews", data=reviews, columns=["chunk_id", "severity", "category", "review", "suggested_fix"])
        )
        return result
    
    async def fetch_chunk_context(self, chunk_id):
        db = Database()
        result = []
        query = "SELECT public.get_function_context($1::uuid[]);"
        record = await db.fetch(query, chunk_id)

        print(f"Fetched chunk context from database for chunk_id {chunk_id}: {len(record)}")

        if record:
            for row in record:
                data = row['get_function_context']
                result.append({'id': data[0], 'message': self.build_message(json.loads(data[1]))})

            return result
        return None

    
    def build_message(self, review_data: dict):
        system_prompt = """or
Your task is to review code in the context of the entire project, not in isolation. Give purpose and module based on the project context for Every Function or Chunk.

Output should be in JSON format with the following structure:
{
  "purpose": "Purpose of the code chunk",
  "module": "What module it is connected according to project"
  "issues": [
    {
      "severity": "Critical | High | Medium | Low | None",
      "category": "Bug | Security | Performance | Maintainability | Readability | Architecture",
      "review": "Detailed review of the code.",
      "suggested_fix": "Specific suggestions for how to fix the issue."
    },
    ...
  ]
}
Output valid JSON only.
"""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{json.dumps(review_data, indent=4)}"}
        ]
    
    async def build_queue(self, review_data: list):
        db = Database()
        
        result = await db.copy_to_table('review_queue', data=review_data, columns=['chunk_id', 'priority', 'updated_at', 'status'])
        return result
    
    async def fetch_pending_reviews(self):
        db = Database()
        query = "SELECT chunk_id FROM review_queue WHERE status = 'pending' ORDER BY priority DESC, updated_at ASC LIMIT 40;"
        rows = await db.fetch(query)
        return [row['chunk_id'] for row in rows]
    
    async def delete_existing_reviews(self, chunk_ids: list):
        db = Database()
        query = "DELETE FROM reviews WHERE chunk_id = ANY($1);"
        result = await db.execute(query, chunk_ids)
        return result
    
    async def mark_reviews_completed(self, chunk_ids: list):
        db = Database()
        query = "UPDATE review_queue SET status = 'completed' WHERE chunk_id = ANY($1);"
        result = await db.execute(query, chunk_ids)
        return result
    
    async def get_review_summary(self, project_id: str):
        db = Database()
        query = """
            SELECT 
                COUNT(*) AS count,
                COUNT(*) FILTER (WHERE severity = 'High') AS critical_count,
                COUNT(*) FILTER (WHERE severity = 'Medium') AS medium_count,
                COUNT(*) FILTER (WHERE severity = 'Low') AS low_count
            FROM reviews r
            JOIN chunks c ON r.chunk_id = c.id
            JOIN files f ON c.file_id = f.id
            WHERE f.project_id = $1
        """
        rows = await db.fetch(query, project_id)
        summary = {}
        for row in rows:
            summary = {
                "total_issues": row['count'],
                "critical_issues": row['critical_count'],
                "medium_issues": row['medium_count'],
                "low_issues": row['low_count']
            }
        return summary
    
    async def get_project_reviews(self, project_id: str, page: int = 1, limit: int = 50):
        db = Database()
        query = """
SELECT
    f.path,

    jsonb_agg(
        DISTINCT jsonb_build_object(
            'purpose', s.purpose,
            'module', s.module,
            'function', c.name,
            'class', c.class_name,
            'start', c.start_line,
            'end', c.end_line,
            'parameters', c.parameters,
            'return_values', c.return_values,
            'issues', COALESCE(issues.issues, '[]'::jsonb)
        )
    ) AS chunks

FROM files f

JOIN chunks c ON c.file_id = f.id
JOIN summaries s ON s.chunk_id = c.id

LEFT JOIN LATERAL (
    SELECT jsonb_agg(
        jsonb_build_object(
            'review_id', r2.id,
            'severity', r2.severity,
            'category', r2.category,
            'review', r2.review,
            'suggested_fix', r2.suggested_fix,
            'created_at', r2.created_at
        )
    ) AS issues
    FROM reviews r2
    WHERE r2.chunk_id = c.id
) issues ON true

WHERE f.project_id = $1

GROUP BY f.path;
        """
        rows = await db.fetch(query, project_id)
        reviews = []
        for row in rows:
            reviews.append({
            "path": row['path'],
            "chunks": json.loads(row['chunks'])
        })
            
        return reviews
