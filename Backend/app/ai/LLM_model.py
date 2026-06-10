import json
import os
import dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List
import asyncio

dotenv.load_dotenv()

class Issue(BaseModel):
    severity: str = Field(description="Severity of the issue ('Critical', 'Major', 'Minor')")
    category: str = Field(description="Category of the issue (e.g., 'Security', 'Performance', 'Readability', 'Maintainability', 'Architectural')")
    review: str = Field(description="Detailed review of the issue")
    suggested_fix: str = Field(description="Suggested fix for the issue")

class Review(BaseModel):
    purpose: str = Field(description="Purpose of the review")
    module: str = Field(description="Module being reviewed")
    issues: List[Issue]

class LLMClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            
            # KEY FIX: Use 'v1beta' to support system_instruction and response_schema
            cls._instance.client = genai.Client(api_key=os.getenv("API_KEY"))
            cls._instance.model_name = "gemini-2.5-flash"

        return cls._instance

    async def get_completion(self, prompt, id=None, temperature=0):
        try:
            # Using the async client (.aio)
            config = types.GenerateContentConfig(
                system_instruction="You are a helpful assistant that reviews code not in isolation but in the context of the entire module. Provide detailed feedback on potential issues and suggest fixes. Always categorize issues by severity and type.",
                temperature=temperature,
                max_output_tokens=800,
                response_mime_type="application/json",
                response_schema=Review.model_json_schema()
            )
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )

            if response.parsed:
                return {id: response.parsed}
            
            if response.text:
                return {id: json.loads(response.text)}

            return {id: "No valid response received"}
            
        except Exception as e:
            return {id: f"LLM_ERROR: {str(e)}"}
        
async def main():
    client = LLMClient()
    result = await client.get_completion("Check this code: def add(a,b): return a+b", id="1")
    print(result)
