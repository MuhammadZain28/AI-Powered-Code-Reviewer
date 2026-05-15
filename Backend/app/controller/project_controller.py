# from app.services.parser_service import ParserService
from app.models.projects import Project

class ProjectController:
    def __init__(self):
        # self.parser_service = ParserService("")
        pass

    async def create_project(self, name: str, description: str, repo_path: str) -> Project:
        project = Project(id=None, name=name, path=repo_path, description=description)
        await project.save()
        return project

    async def get_project(self, project_id: str) -> Project:
        project = Project(id=project_id, name="", path="", description="")
        project_data = await project.fetch()
        if project_data:
            return Project(id=project_data['id'], name=project_data['name'], path=project_data['path'], description=project_data['description'])
        return None

    async def get_all_projects(self):
        project = Project(id=None, name="", path="", description="")
        projects_data = await project.fetch_all()
        return projects_data

    async def delete_project(self, project_id: str):
        project = Project(id=project_id, name="", path="", description="")
        return await project.delete()