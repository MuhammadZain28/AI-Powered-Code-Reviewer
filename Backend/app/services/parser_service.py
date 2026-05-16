import os
import re
import hashlib
from app.utils.logger import get_logger
from app.utils.chunker import Chunker

class ParserService:
    ignored_dirs = {'.git', 'node_modules', 'venv', '.venv', '.next', '__pycache__', 'dist', 'build', 'target', 'out', 'bin', 'obj', 'logs', 'coverage', 'reports', 'docs', 'examples', 'samples', 'test', 'tests', 'spec', 'specs', 'mock', 'mocks', 'fixture', 'fixtures'}
    valid_extensions = {'.py', '.js', '.jsx', '.ts', '.tsx', '.cpp', '.java'}
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.__logger = get_logger("ParserService")

    def is_ignored_dir(self, dir_name: str) -> bool:
        return dir_name in self.ignored_dirs

    def is_valid_extension(self, file_name: str) -> bool:
        _, ext = os.path.splitext(file_name)
        return ext in self.valid_extensions

    def scan_project(self) -> list:
        code_files = []
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not self.is_ignored_dir(d)]
            self.__logger.info(f"Scanning directory: {root}")
            for file in files:
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

    def file_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def clean_code(self, code: str) -> str:
        code = re.sub(r'//.*', '', code)

        code = re.sub(r'/\*[\s\S]*?\*/', '', code)

        code = re.sub(r'#.*', '', code)

        code = re.sub(r'\n{3,}', '\n\n', code)

        return code.strip()

    def read_file(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            self.__logger.error(f"Error reading file {file_path}: {e}")
            return ""

    def chunk_code(self, code: str, language: str, file_path: str) -> list:
        chunker = Chunker(code, language, file_path)
        chunks = chunker.chunk_code()
        if not chunks:
            self.__logger.warning(f"No chunks extracted from code in language {file_path}. Returning entire file as one chunk.")
            return [{
            'embedding_id': f"{file_path}_0",
            'name': f"{file_path}_file_0",
            'content': code,
            'start_line': 1,
            'end_line': code.count('\n') + 1,
            'type': 'file'
            }]
        return chunks

    def parse_project(self) -> dict:
        code_files = self.scan_project()
        project_data = {}

        for file in code_files:
            language = self.detect_language(file)
            code = self.read_file(file)
            code = self.clean_code(code)
            code_chunks = self.chunk_code(code, language, file)
            project_data[file] = {
                'language': language,
                'hash': self.file_hash(code),
                'chunks': code_chunks
            }
        return project_data

if __name__ == "__main__":
    repo_path = r"D:\Project\NUCES"
    parser_service = ParserService(repo_path)
    parsed_data = parser_service.parse_project()

    for file_path, data in parsed_data.items():
        print(f"File: {file_path}")
        print(f"Language: {data['language']}")
        print(f"Hash: {data['hash']}")
        print("Chunks:")
        for chunk in data['chunks']:
            print(f"  - ID: {chunk['embedding_id']}, Type: {chunk['type']}, Lines: {chunk['start_line']}-{chunk['end_line']}")