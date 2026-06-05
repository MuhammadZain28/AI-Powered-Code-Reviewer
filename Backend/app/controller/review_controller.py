import asyncio
import time
from app.ai.LLM_model import LLMClient
from app.managers.chunks import Chunk
from app.managers.reviews import Review


class ReviewController:
    def __init__(self):
        self.llm_client = LLMClient()
        self.chunk_manager = Chunk()
        self.review_manager = Review()
        self.semahphore = asyncio.Semaphore(5)

    async def batch_reviews(self, chunk):
        async with self.semahphore:
            return await self.llm_client.get_completion(chunk['message'], id=chunk['id'])

    async def review_code(self, file_id):
        start_time = time.time()
        messages = await self.review_manager.fetch_chunk_context(file_id)
        if not messages:
            return {"error": "No chunk found for the given chunk ID."}

        print(f"Fetched code chunk for {file_id}: {type(messages)}")
        end_time = time.time()

        print(f"Prepared review context in {end_time - start_time:.2f} seconds.")

        start_time = time.time()

        tasks = [self.batch_reviews(message) for message in messages]

        review_result = await asyncio.gather(*tasks)

        end_time = time.time()

        print(f"Code review completed in {end_time - start_time:.2f} seconds.")

        start_time = time.time()

        _ = await self.review_manager.insert(review_result)

        return {"message": "Success", "review": review_result}