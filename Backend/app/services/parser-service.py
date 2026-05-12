import os
import re

class ParserService:
    ignored_dirs = {'.git', 'node_modules', 'venv', '.venv', '.next', '__pycache__', 'dist', 'build', 'target', 'out', 'bin', 'obj', 'logs', 'coverage', 'reports', 'docs', 'examples', 'samples', 'test', 'tests', 'spec', 'specs', 'mock', 'mocks', 'fixture', 'fixtures'}
    valid_extensions = {'.py', '.js', '.jsx', '.ts', '.tsx', '.cpp', '.java'}
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def is_ignored_dir(self, dir_name: str) -> bool:
        return dir_name in self.ignored_dirs

    def is_valid_extension(self, file_name: str) -> bool:
        _, ext = os.path.splitext(file_name)
        return ext in self.valid_extensions

    def scan_project(self) -> list:
        code_files = []
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not self.is_ignored_dir(d)]
            # print(f"Scanning directory: {root}")
            for file in files:
                # print(f"Found file: {file}")
                if self.is_valid_extension(file):
                    file_path = os.path.join(root, file)
                    code_files.append(file_path)
        return code_files

    def detect_language(self, file_path: str) -> str:
        _, ext = os.path.splitext(file_path)
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript (React)',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript (React)',
            '.cpp': 'C++',
            '.java': 'Java'
        }
        return language_map.get(ext, 'Unknown')
if __name__ == "__main__":
    repo_path = r"D:\Project\AI-Powered Code Reviewer"
    parser_service = ParserService(repo_path)
    code_files = parser_service.scan_project()
    for file in code_files:
        print(file)
        print(f"Language: {parser_service.detect_language(file)}")

