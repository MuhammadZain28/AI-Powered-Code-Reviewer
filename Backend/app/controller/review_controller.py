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

    async def review_code(self):
        start_time = time.time()
        chunk_ids = await self.review_manager.fetch_pending_reviews()
        if not chunk_ids:
            return {"message": "No pending reviews found."}
        messages = await self.review_manager.fetch_chunk_context(chunk_ids)
        if not messages:
            return {"error": "No chunk found for the given chunk ID."}

        print(f"Fetched code chunk for {chunk_ids}: {len(messages)}")
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
    
    async def get_reviews_summary(self, project_id: str):
        summary = await self.review_manager.get_review_summary(project_id)
        return summary