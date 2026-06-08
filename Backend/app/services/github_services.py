import os
import hashlib
from pathlib import Path
from git import Repo
from app.utils.logger import get_logger
import subprocess

BASE_PATH = "backend/data/repos"
class GitHubService:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.logger = get_logger("GitHubService")

    def generate_repo_id(self) -> str:
        return hashlib.sha256(self.repo_path.encode()).hexdigest()

    def get_repo_path(self) -> str:
        repo_id = self.generate_repo_id()
        repo_path = os.path.join(BASE_PATH, repo_id)
        return repo_path

    def clone_repo(self, repo_path: str) -> str:
        try:
            repo_path = self.get_repo_path()
            if not os.path.exists(repo_path):
                self.logger.info(f"Cloning repository {repo_path} to {repo_path}")
                Repo.clone_from(repo_path, repo_path)
                self.logger.info(f"Repository cloned successfully to {repo_path}")
            else:
                self.logger.info(f"Repository already exists at {repo_path}")
            return repo_path
        except Exception as e:
            self.logger.error(f"Error occurred while cloning repository: {e}")
            raise

    def get_last_commit_files(self):
        repo_root = subprocess.check_output(
            ["git", "-C", self.repo_path, "rev-parse", "--show-toplevel"],
            text=True
        ).strip()
        result = subprocess.run(
            ["git", "-C", self.repo_path, "diff", "HEAD", "--name-status"],
            capture_output=True,
            text=True
        )
        files = {'A': [], 'M': [], 'D': []}
        for f in result.stdout.strip().split("\n"):
            if f and f[0] in files and f[1] == "\t":
                status = f[0]
                file_path = f[2:]
                full_path = str(Path(repo_root) / file_path)
                files[status].append(full_path)
                self.logger.info(f"Changed file: {f}")
        return files


if __name__ == "__main__":
    repo_path = "D:\\Project\\exam-seating-planer"
    service = GitHubService(repo_path)
    files = service.get_last_commit_files()
    for status, file_list in files.items():
        print(f"Status: {status}")
        for f in file_list:
            print(f"files: {f}")