from fastapi import APIRouter, HTTPException
from app.controller.review_controller import ReviewController

review_router = APIRouter(prefix="/review", tags=["review"])

@review_router.post("/{file_id}", response_model=dict)
async def review_file(file_id: str):
    try:
        controller = ReviewController()
        parsed_data = await controller.review_code(file_id)
        return parsed_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
