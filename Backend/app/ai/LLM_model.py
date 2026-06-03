import json
import os
import dotenv
from openai import OpenAI

dotenv.load_dotenv()

class LLMClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.MODEL = os.getenv("MODEL")
            cls._instance.client = OpenAI(
                api_key=os.getenv("HF_TOKEN"),
                base_url="https://router.huggingface.co/v1"
            )

        return cls._instance

    def get_completion(self, messages, temperature=0.1, max_tokens=1000):
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                response_format={"type": "json_object"},
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            print(f"LLM Response: {response}")
            if response.choices[0].message.content:
                return json.loads(response.choices[0].message.content)
            return response.choices[0].message.reasoning

        except Exception as e:
            return f"LLM_ERROR: {str(e)}"

