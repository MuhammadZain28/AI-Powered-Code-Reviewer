from fastapi import APIRouter, HTTPException
from app.controller.project_controller import ProjectController
from pydantic import BaseModel
from typing import List, Optional

class ProjectCreate(BaseModel):
    name: str
    description: str
    repo_path: str
    features: Optional[str] = None
    modules: Optional[str] = None
    frontend: Optional[str] = None
    backend: Optional[str] = None
    technologies: Optional[str] = None

project_router = APIRouter(prefix="/projects", tags=["projects"])

@project_router.post("/", response_model=dict)
async def create_project(project: ProjectCreate):
    try:
        controller = ProjectController()
        project = await controller.create_project(
            name=project.name,
            description=project.description,
            repo_path=project.repo_path,
            features=project.features,
            modules=project.modules,
            frontend=project.frontend,
            backend=project.backend,
            technologies=project.technologies
        )
        return {"message": "Project created successfully", "project_id": project}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@project_router.get("/{project_id}", response_model=dict)
async def select_project(project_id: str):
    try:
        controller = ProjectController()
        project = await controller.get_project(project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@project_router.get("/", response_model=list)
async def select_all_projects():
    try:
        controller = ProjectController()
        projects = await controller.get_all_projects()
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@project_router.get("/{project_id}/files", response_model=list)
async def get_project_files(project_id: str):
    try:
        controller = ProjectController()
        files = await controller.get_project_files(project_id)
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@project_router.delete("/{project_id}", response_model=dict)
async def delete_project(project_id: str):
    try:
        controller = ProjectController()
        success = await controller.delete_project(project_id)
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"message": "Project deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@project_router.get("/{project_id}/stats", response_model=dict)
async def project_stats(project_id: str):
    try:
        controller = ProjectController()
        stats = await controller.project_stats(project_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))