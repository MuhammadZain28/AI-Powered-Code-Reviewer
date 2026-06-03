from app.managers.projects import Project

class ProjectController:
    def __init__(self):
        pass

    async def create_project(self, name: str, description: str, repo_path: str, features: str = None, modules: str = None, frontend: str = None, backend: str = None, technologies: str = None) -> Project:
        features = features.split(",") if features else []
        modules = modules.split(",") if modules else []
        technologies = technologies.split(",") if technologies else []
        result = await Project().insert(name, repo_path, description, features, modules, frontend, backend, technologies)
        return result

    async def get_project(self, project_id: str) -> Project:
        project = Project(id=project_id, name="", path="", description="")
        project_data = await project.fetch()
        if project_data:
            return project_data
        return None

    async def get_all_projects(self):
        project = Project(id=None, name="", path="", description="")
        projects_data = await project.fetch_all()
        return projects_data

    async def delete_project(self, project_id: str):
        project = Project(id=project_id, name="", path="", description="")
        return await project.delete()