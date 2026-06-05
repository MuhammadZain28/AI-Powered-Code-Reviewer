import json
import time
from app.ai.LLM_model import LLMClient
from app.managers.chunks import Chunk
from app.managers.reviews import Review

system_prompt = """
You are a senior software architect and code reviewer.

Your task is to review code in the context of the entire project, not in isolation.

When reviewing code:

1. Consider architectural impact.
2. Consider interactions with helper functions and also review helper functions.
3. Consider module responsibilities.
4. Consider performance implications and suggest optimized version if exist.
5. Consider maintainability.
6. Consider security issues.
7. Consider code readability but not give suggestion to add comment or docstring.
8. Avoid suggesting changes that conflict with existing project patterns.

Only report issues that have clear reasoning.

Output should be in JSON format with the following structure:
{
  "purpose": "Purpose of the code chunk",
  "module": "What module it is connected according to project"
  "issues": [
    {
      "chunk_id": "ID of the code chunk where the issue is located",
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

class ReviewController:
    def __init__(self):
        self.llm_client = LLMClient()
        self.chunk_manager = Chunk()
        self.review_manager = Review()

    async def review_code(self, chunk_id):
        start_time = time.time()
        chunk = await self.chunk_manager.fetch_chunk_context(chunk_id)
        if not chunk:
            return {"error": "No chunk found for the given chunk ID."}

        print(f"Fetched code chunk for {chunk_id}: {json.dumps(chunk, indent=4)}")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Review the following code chunk and Give content in JSON format:\n{json.dumps(chunk, indent=4)}"}
        ]

        end_time = time.time()
        print(f"Prepared review context in {end_time - start_time:.2f} seconds.")

        start_time = time.time()

        review_result = self.llm_client.get_completion(messages=messages)

        end_time = time.time()

        print(f"Code review completed in {end_time - start_time:.2f} seconds.")

        start_time = time.time()

        _ = await self.review_manager.insert(review_result['issues'])

        return {"message": "Success", "review": review_result}