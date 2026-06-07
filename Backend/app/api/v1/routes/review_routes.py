from fastapi import APIRouter, HTTPException
from app.controller.review_controller import ReviewController

review_router = APIRouter(prefix="/review", tags=["review"])

@review_router.post("/", response_model=dict)
async def review_file():
    try:
        controller = ReviewController()
        parsed_data = await controller.review_code()
        return parsed_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@review_router.get("/summary/{project_id}", response_model=dict)
async def get_reviews_summary(project_id: str):
    try:
        controller = ReviewController()
        summary = await controller.get_reviews_summary(project_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@review_router.get("/project/{project_id}", response_model=list)
async def get_project_reviews(project_id: str, page: int = 1, limit: int = 50):
    try:
        controller = ReviewController()
        reviews = await controller.get_project_reviews(project_id, page, limit)
        return reviews
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))