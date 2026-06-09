import json
import os
import dotenv
from google import genai
import typing_extensions as typing

dotenv.load_dotenv()

class Issue(typing.TypedDict):
    severity: str
    category: str
    review: str
    suggested_fix: str

class FunctionReview(typing.TypedDict):
    purpose: str
    module: str
    issues: typing.List[Issue]

class LLMClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

            genai.configure(api_key=os.getenv("API_KEY"))

            cls._instance.client = genai.GenerativeModel(
                model_name=os.getenv("MODEL"),
                system_instruction=(
                    "You are an expert software architect. Review code chunks in the context of the project. "
                    "Be extremely concise and technical. Output valid JSON only."
                )
            )

        return cls._instance

    async def get_completion(self, prompt, id=None, temperature=0, max_tokens=800):
        try:
            response = await self.client.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "response_schema": FunctionReview,
                    "temperature": temperature
                }
            )
            print(f"LLM response for chunk_id {id}: {response.text}")
            if response.text:
                return {id: json.loads(
                    response.text
                )}

            return {id: "No valid response received"}
        except Exception as e:
            return f"LLM_ERROR: {str(e)}"
        
if __name__ == "__main__":
    import asyncio

    async def test():
        client = LLMClient()
        prompt = "Review the following code chunk:\n\n```python\ndef add(a, b):\n    return a + b\n```"
        response = await client.get_completion(prompt, id="test_chunk")
        print(response)

    asyncio.run(test())