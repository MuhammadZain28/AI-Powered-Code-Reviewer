import traceback
import os
import hashlib
from app.utils.logger import get_logger
from app.managers.files import File
from app.utils.chunker import Chunker
from uuid6 import uuid7

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

    async def scan_existing_project(self, project_id: str) -> list:
        files = await File(project_id=project_id).scan_project()
        code_files = []
        for file in files:
            code = self.read_file(file['path'])
            if self.file_hash(code) != file['hash']:
                code_files.append(file['path'])

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

    def chunk_code(self, code: str, language: str, file_path: str, id: str) -> list:
        chunker = Chunker(code, language, id)
        chunks = chunker.chunk_code()

        if not chunks:
            self.__logger.warning(f"No chunks extracted from code in language {file_path}. Returning entire file as one chunk.")

            return {
                "classes": [],
                "imports": [],
                "calls": [],
                "attributes": [],
                "chunks": [(
                    uuid7(),
                    id,
                    None,
                    f"{file_path.split('/')[-1]}",
                    code,
                1,
                code.count('\n') + 1,
                'file',
                self.file_hash(code),
                None,
                None,
                None
                )]}
        return chunks

    def parse_project(self, project_id, changed_files: list = None) -> dict:
        if changed_files is not None:
            code_files = [file for file in changed_files if self.is_valid_extension(file)]
        else:
            code_files = self.scan_project()
        project_files, project_classes, project_imports, project_chunks, project_calls, project_attributes, project_import_modules = [], [], [], [], [], [], []

        for file in code_files:
            language = self.detect_language(file)
            
            code = self.read_file(file)

            id = uuid7()

            chunked_code = self.chunk_code(code, language, file, id)


            project_files.append((
                id,                         # unique identifier for the file
                project_id,                 # associate file with its project
                file,                       # file path for reference
                language,                   # programming language of the file
                self.file_hash(code),       # hash of the file content for quick comparisons
            ))

            project_classes.extend(chunked_code.get('classes', []))
            project_imports.extend(chunked_code.get('imports', []))
            project_chunks.extend(chunked_code.get('chunks', []))
            project_calls.extend(chunked_code.get('calls', []))
            project_attributes.extend(chunked_code.get('attributes', []))
            project_import_modules.extend(chunked_code.get('import_modules', []))
            self.__logger.info(f"Extracted {len(chunked_code.get('chunks', []))} code chunks from {file}")
        return {
            'files': project_files,
            'classes': project_classes,
            'imports': project_imports,
            'chunks': project_chunks,
            'calls': project_calls,
            'attributes': project_attributes,
            'import_modules': project_import_modules
        }

    def update_changed_chunks(self, chunk_map: dict, class_map: dict, files_in_db: dict):
        modified_files, modified_chunks, modified_attributes, modified_import_modules, modified_classes, modified_imports, modified_calls = [], [], [], [], [], [], []

        for file_id, info in files_in_db.items():
            language = info['language']
            path = info['path']
            code = self.read_file(path)

            modified_files.append((
                file_id,
                self.file_hash(code)
            ))

            chunked_code = self.chunk_change(code, language, path, file_id, chunk_map=chunk_map, class_map=class_map)

            modified_classes.extend(chunked_code.get('classes', []))
            modified_imports.extend(chunked_code.get('imports', []))
            modified_chunks.extend(chunked_code.get('chunks', []))
            modified_calls.extend(chunked_code.get('calls', []))
            modified_attributes.extend(chunked_code.get('attributes', []))
            modified_import_modules.extend(chunked_code.get('import_modules', []))

            class_map = chunked_code.get('class_map', {})
            chunk_map = chunked_code.get('chunk_map', {})

            print(f"After processing {path}, remaining chunk_map: {len(chunk_map)}, remaining class_map: {len(class_map)}")

            self.__logger.info(f"Extracted {len(chunked_code.get('chunks', []))} code chunks from {path} for change management")
        return {
            'files': modified_files,
            'classes': modified_classes,
            'imports': modified_imports,
            'chunks': modified_chunks,
            'calls': modified_calls,
            'attributes': modified_attributes,
            'import_modules': modified_import_modules
        }

    def chunk_change(self, code: str, language: str, file_path: str, id: str, chunk_map: dict, class_map: dict) -> list:
        chunker = Chunker(code, language, id)
        self.__logger.info(f"Chunk map for change management: {len(chunk_map)} and class map: {len(class_map)}")
        chunks = chunker.chunk_change_code(chunk_map=chunk_map, class_map=class_map)

        if not chunks:
            self.__logger.warning(f"No chunks extracted from code in language {file_path}. Returning entire file as one chunk.")

            return {
                "classes": [],
                "imports": [],
                "calls": [],
                "attributes": [],
                "chunks": [(
                    uuid7(),
                    id,
                    None,
                    f"{file_path.split('/')[-1]}",
                    code,
                1,
                code.count('\n') + 1,
                'file',
                self.file_hash(code),
                None,
                None,
                None
                )]}
        return chunks
