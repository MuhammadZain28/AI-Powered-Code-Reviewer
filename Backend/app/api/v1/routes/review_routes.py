from fastapi import APIRouter, HTTPException
from app.controller.review_controller import ReviewController

review_router = APIRouter(prefix="/review", tags=["review"])

@review_router.post("/{chunk_id}", response_model=dict)
async def review_chunk(chunk_id: str):
    try:
        controller = ReviewController()
        parsed_data = await controller.review_code(chunk_id)
        return parsed_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
