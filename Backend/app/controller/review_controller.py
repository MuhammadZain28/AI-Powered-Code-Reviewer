import json
import time
from app.ai.LLM_model import LLMClient
from app.managers.chunks import Chunk

system_prompt = """
You are a senior software architect and code reviewer.

Your task is to review code in the context of the entire project, not in isolation.

When reviewing code:

1. Consider architectural impact.
2. Consider interactions with called functions.
3. Consider interactions with caller functions.
4. Consider module responsibilities.
5. Consider performance implications.
6. Consider maintainability.
7. Consider security issues.
8. Consider code readability.
9. Consider naming consistency.
10. Avoid suggesting changes that conflict with existing project patterns.

Only report issues that have clear reasoning.

For each issue provide:

- Severity:
  Critical | High | Medium | Low

- Category:
  Bug | Security | Performance | Maintainability | Readability | Architecture

- Location


- Suggested Fix

If no significant issues exist, explicitly state that.

Output should be in JSON format with the following structure:
{
  "file_id": "ID of the reviewed file",
  "summary": "Overall summary of the code of file.",
  "issues": [
    {
      "chunk_id": "ID of the code chunk where the issue is located",
      "severity": "Critical | High | Medium | Low",
      "category": "Bug | Security | Performance | Maintainability | Readability | Architecture",
      "explanation": "Detailed explanation of the issue with reasoning.",
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

    async def review_code(self, file_id):
        start_time = time.time()
        chunks = await self.chunk_manager.fetch_chunk_context(file_id)
        if not chunks:
            return {"error": "No chunks found for the given file ID."}

        print(f"Fetched code chunks for file ID {file_id}: {json.dumps(chunks[0], indent=4)}")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Review the following code chunks and Give content in JSON format:\n{json.dumps(chunks[0], indent=4)}"}
        ]

        end_time = time.time()
        print(f"Prepared review context in {end_time - start_time:.2f} seconds.")

        start_time = time.time()

        review_result = self.llm_client.get_completion(messages=messages)

        end_time = time.time()

        print(f"Code review completed in {end_time - start_time:.2f} seconds.")

        return {"message": "Success", "review": review_result}