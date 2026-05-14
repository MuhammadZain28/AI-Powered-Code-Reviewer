import os
import re
from app.utils.logger import get_logger
from app.utils.chunker import Chunker
from app.services.embedding_service import EmbeddingService
from app.vector_store.faiss import FaissIndex

class ParserService:
    ignored_dirs = {'.git', 'node_modules', 'venv', '.venv', '.next', '__pycache__', 'dist', 'build', 'target', 'out', 'bin', 'obj', 'logs', 'coverage', 'reports', 'docs', 'examples', 'samples', 'test', 'tests', 'spec', 'specs', 'mock', 'mocks', 'fixture', 'fixtures'}
    valid_extensions = {'.py', '.js', '.jsx', '.ts', '.tsx', '.cpp', '.java'}
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.logger = get_logger("ParserService")
        self.embedding_service = EmbeddingService()
        self.faiss_index = FaissIndex(dimension=384)

    def is_ignored_dir(self, dir_name: str) -> bool:
        return dir_name in self.ignored_dirs

    def is_valid_extension(self, file_name: str) -> bool:
        _, ext = os.path.splitext(file_name)
        return ext in self.valid_extensions

    def scan_project(self) -> list:
        code_files = []
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not self.is_ignored_dir(d)]
            self.logger.info(f"Scanning directory: {root}")
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
            self.logger.error(f"Error reading file {file_path}: {e}")
            return ""

    def chunk_code(self, file_path: str, language: str) -> list:
        code = self.read_file(file_path)
        code = self.clean_code(code)
        chunker = Chunker(code, language)
        chunks = chunker.chunk_code()
        if not chunks:
            self.logger.warning(f"No chunks extracted from {file_path}")
            return [{
            'id': 0,
            'code': code,
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
            code_chunks = self.chunk_code(file, language)
            project_data[file] = {
                'language': language,
                'chunks': code_chunks
            }
        return project_data

if __name__ == "__main__":
    repo_path = r"D:\Project\NUCES"
    parser_service = ParserService(repo_path)
    parsed_data = parser_service.parse_project()

    for file, data in parsed_data.items():
        embed_chunks = parser_service.embedding_service.embed_chunks(data['chunks'], data['language'])
        print(f"Metadata for file: {embed_chunks[0]['meta']}")
        print(f"Embeddings shape: {embed_chunks[0]['vector'].shape}")
        print(f"Embeddings Vector: {embed_chunks[0]['vector'][:5]}")
        print("-" * 40)
        faiss_id = parser_service.faiss_index.add_embeddings([chunk['vector'] for chunk in embed_chunks])
        print(f"Added {len(embed_chunks)} chunks from {file} to Faiss index with ID: {faiss_id}")