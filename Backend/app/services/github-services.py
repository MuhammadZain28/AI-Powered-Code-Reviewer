import os
import hashlib
from git import Repo
from app.utils.logger import get_logger

BASE_PATH = "backend/data/repos"
class GitHubService:
    def __init__(self, repo_url: str):
        self.repo_url = repo_url
        self.logger = get_logger("GitHubService")

    def generate_repo_id(self) -> str:
        return hashlib.sha256(self.repo_url.encode()).hexdigest()

    def get_repo_path(self) -> str:
        repo_id = self.generate_repo_id()
        repo_path = os.path.join(BASE_PATH, repo_id)
        return repo_path

    def clone_repo(self, repo_url: str) -> str:
        try:
            repo_path = self.get_repo_path()
            if not os.path.exists(repo_path):
                self.logger.info(f"Cloning repository {repo_url} to {repo_path}")
                Repo.clone_from(repo_url, repo_path)
                self.logger.info(f"Repository cloned successfully to {repo_path}")
            else:
                self.logger.info(f"Repository already exists at {repo_path}")
            return repo_path
        except Exception as e:
            self.logger.error(f"Error occurred while cloning repository: {e}")
            raise