import json
import os
import dotenv
from openai import AsyncOpenAI

dotenv.load_dotenv()

class LLMClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

            cls._instance.MODEL = os.getenv("MODEL")

            cls._instance.client = AsyncOpenAI(
                api_key=os.getenv("HF_TOKEN"),
                base_url="https://router.huggingface.co/v1"
            )

        return cls._instance

    async def get_completion(self, messages, id=None, temperature=0, max_tokens=800):
        try:
            response = await self.client.chat.completions.create(
                model=self.MODEL,
                response_format={"type": "json_object"},
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            if response.choices[0].message.content:
                return {id: json.loads(
                    response.choices[0].message.content
                )}

            return {id: response.choices[0].message.reasoning}
        except Exception as e:
            return f"LLM_ERROR: {str(e)}"