from fastapi import APIRouter, HTTPException
from app.controller.parse_controller import ParseController

parse_router = APIRouter(prefix="/parse", tags=["parse"])

@parse_router.post("/{project_id}", response_model=dict)
async def parse_project(project_id: str, repo_path: str):
    try:
        controller = ParseController(repo_path=repo_path)
        parsed_data = await controller.parse_project(project_id)
        return parsed_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))