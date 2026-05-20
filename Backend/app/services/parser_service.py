import os
import re
import hashlib
from app.utils.logger import get_logger
from app.utils.chunker import Chunker
from app.models.files import File
from app.models.chunks import Chunk
from app.models.classes import Class

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
            'name': f"{file_path.split('/')[-1]}",
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
            classes, imports, chunks = self.chunk_code(code, language, file)
            project_data[file] = {
                'language': language,
                'hash': self.file_hash(code),
                'classes': classes,
                'imports': imports,
                'chunks': chunks
            }
        return project_data

    # Testing in Data Insertion
async def insert_chunk(chunk_data: dict, class_id: int = None):
    chunk = Chunk(
        id=None,
        file_id=chunk_data['file_id'],
        class_id=class_id,
        chunk_type=chunk_data['chunk_type'],
        name=chunk_data['name'],
        start_line=chunk_data['start_line'],
        end_line=chunk_data['end_line'],
        content=chunk_data['content'],
        parameters=chunk_data.get('parameters', []),
        return_values=chunk_data.get('return_values', []),
        complexity=chunk_data.get('complexity', {}),
        hash=chunk_data.get('hash', ""),
        docstring=chunk_data.get('docstring', "")
    )
    await chunk.save()
    print(f"Inserted new chunk {chunk.name} with ID {chunk.id} into FAISS index.")
    return chunk.id

async def insert_class(class_data: dict):
    class_chunk = Class(
        id=None,
        file_id=class_data['file_id'],
        name=class_data['name'],
        start_line=class_data['start_line'],
        end_line=class_data['end_line'],
        docstring=class_data['docstring'],
        inheritances=class_data.get('inheritances', [])
    )
    await class_chunk.save()
    print(f"Inserted new class {class_chunk.name} with ID {class_chunk.id} into FAISS index.")
    return class_chunk.id

async def process_file(parsed_data: dict, project_id: str):
    ids = []
    for file_path, file_data in parsed_data.items():
        file = File(id=None, project_id=project_id, path=file_path, language=file_data['language'], hash=file_data['hash'])
        await file.save()
        for cls in file_data['classes']:
            class_id = await insert_class(class_data={
                'file_id': file.id,
                'name': cls['name'],
                'start_line': cls['start_line'],
                'end_line': cls['end_line'],
                'docstring': cls['docstring'],
                'inheritances': cls.get('inheritances', [])
            })
            for chunk in cls['chunks']:
                chunk_id = await insert_chunk(chunk_data={
                    'file_id': file.id,
                    'chunk_type': chunk['type'],
                    'name': chunk['name'],
                    'start_line': chunk['start_line'],
                    'end_line': chunk['end_line'],
                    'content': chunk['content'],
                    'parameters': chunk.get('params', []),
                    'return_values': chunk.get('returns', []),
                    'complexity': chunk.get('complexity', {}),
                    'hash': chunk.get('hash', ""),
                    'docstring': chunk.get('docstring', "")
                }, class_id=class_id)
                ids.append(chunk_id)



if __name__ == "__main__":
    import asyncio

    async def main():
        project_id = "1bd4a2cb-3823-4c2b-9bd6-3201d07353fa"
        repo_path = "D:/Project/Test"
        parser_service = ParserService(repo_path)
        parsed_data = parser_service.parse_project()
        await process_file(parsed_data, project_id)
    asyncio.run(main())