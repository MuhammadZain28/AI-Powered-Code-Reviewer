from fastapi import APIRouter, HTTPException
from app.controller.project_controller import ProjectController

project_router = APIRouter(prefix="/projects", tags=["projects"])

@project_router.post("/", response_model=dict)
async def create_project(name: str, description: str, repo_path: str):
    try:
        controller = ProjectController()
        project = await controller.create_project(name, description, repo_path)
        return {"id": project.id, "name": project.name, "path": project.path, "description": project.description}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@project_router.get("/{project_id}", response_model=dict)
async def select_project(project_id: str):
    try:
        controller = ProjectController()
        project = await controller.get_project(project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"id": project.id, "name": project.name, "path": project.path, "description": project.description, "files": project.files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@project_router.get("/", response_model=list)
async def select_all_projects():
    try:
        controller = ProjectController()
        projects = await controller.get_all_projects()
        return [{"id": project['id'], "name": project['name'], "path": project['path'], "description": project['description'], "files": project['files']} for project in projects]
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