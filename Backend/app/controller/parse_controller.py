from datetime import datetime
from app.managers.classes import Class
from app.managers.chunks import Chunk
from app.managers.reviews import Review
from app.managers.files import File
from app.managers.database import Database
from app.services.parser_service import ParserService
from app.services.embedding_service import EmbeddingService
from app.services.github_services import GitHubService
from app.utils.faiss import FaissIndex
from app.utils.logger import get_logger
import time
import traceback


class ParseController:
    def __init__(self, repo_path: str):
        self.parser_service = ParserService(repo_path)
        self.github_service = GitHubService(repo_path)
        self.embedding_service = EmbeddingService()
        self.faiss_index = FaissIndex(dimension=384)
        self.__logger = get_logger("ParseController")

    async def parse_project(self, project_id: str) -> dict:
        self.__logger.info(f"Starting to parse project")

        try:
            start_time = time.time()
            parsed_data = self.parser_service.parse_project(project_id=project_id)

            self.__logger.info(f"Finished parsing project")

            files = parsed_data['files']
            imports = parsed_data['imports']
            classes = parsed_data['classes']
            calls = parsed_data['calls']
            chunks = parsed_data['chunks']
            attributes = parsed_data['attributes']
            import_symbols = parsed_data['import_symbols']

            print(f"Parsed data for project {import_symbols}:")

            end_time = time.time()

            self.__logger.info(f"Finished parsing project in {end_time - start_time:.2f} seconds. Starting to save to database...")

            await self.copy_table_to_database(files, imports, classes, calls, chunks, attributes, import_symbols, project_id)

            start_time = time.time()

            end_time = time.time()

            self.__logger.info(f"Finished embedding and saving to Faiss index for project {project_id} in {end_time - start_time:.2f} seconds")

            return {
                "files": len(files),
                "imports": len(imports),
                "classes": len(classes),
                "calls": len(calls),
                "chunks": len(chunks),
                "attributes": len(attributes),
                "import_symbols": len(import_symbols)
            }

        except Exception as e:
            self.__logger.error(traceback.format_exc())
            raise e

    async def search_chunks(self, query: str, k: int = 5):
        query_vector = self.embedding_service.model.encode(query, convert_to_numpy=True)
        ids, scores = self.faiss_index.search(query_vector, k)
        try:
            results = await Chunk().fetch_chunk_by_id(ids, scores)
        except Exception as e:
            self.__logger.error(f"Error occurred while fetching chunks: {e}")
            self.__logger.error(traceback.format_exc())
            raise
        return results

    async def manage_changes(self, project_id: str):
        file_paths = self.github_service.get_last_commit_files()
        self.__logger.info(f"Fetched changed files from GitHub for change management: {file_paths}")

        _ = await File().manage_deleted_files(project_id, file_paths['D'])

        start_time = time.time()

        parsed_data = self.parser_service.parse_project(project_id=project_id, changed_files=file_paths['A'])


        self.__logger.info(f"Finished parsing project")

        files = parsed_data['files']
        imports = parsed_data['imports']
        classes = parsed_data['classes']
        calls = parsed_data['calls']
        chunks = parsed_data['chunks']
        attributes = parsed_data['attributes']
        import_symbols = parsed_data['import_symbols']

        end_time = time.time()

        self.__logger.info(f"Finished parsing project in {end_time - start_time:.2f} seconds. Starting to save to database...")

        chunk_data = await Chunk().fetch_chunks_hash(file_paths['M'])

        print(f"Chunk data for change management: {chunk_data}")

        modified_data = self.parser_service.update_changed_chunks(chunk_map=chunk_data['chunk_map'], class_map=chunk_data['class_map'], files_in_db=chunk_data['files_in_db'])

        await self.database_updates_for_changes(modified_data['files'] + files, modified_data['classes'], modified_data['chunks'])

        imports.extend(modified_data['imports'])
        attributes.extend(modified_data['attributes'])
        import_symbols.extend(modified_data['import_symbols'])
        calls.extend(modified_data['calls'])
        await self.copy_table_to_database([], imports, classes, calls, chunks, attributes, import_symbols, project_id)

        return {
            "files": len(files),
            "imports": len(imports),
            "classes": len(classes) + len(modified_data['classes']),
            "calls": len(calls),
            "chunks": len(chunks) + len(modified_data['chunks']),
            "attributes": len(attributes),
            "import_symbols": len(import_symbols)
        }

    async def database_updates_for_changes(self, files: list, classes: list, chunks: list):
        file_result = await File().manage_changed_files(files)
        class_result = await Class().manage_change(classes)
        chunk_result = await Chunk().managed_changed_chunks(chunks)

        self.__logger.info(f"Database update results - Files: {file_result}, Classes: {class_result}, Chunks: {chunk_result}")

    async def copy_table_to_database(self, files: list, imports: list, classes: list, calls: list, chunks: list, attributes: list, import_symbols: list, project_id: str):
        start_time = time.time()

        await Database().connect()

        end_time = time.time()

        self.__logger.info(f"Connected to database in {end_time - start_time:.2f} seconds. Starting to save data...")


        table_data = {
            'files': { 'data': files, 'columns': ['id', 'project_id', 'path', 'language', 'total_lines', 'hash'] },
            'imports': { 'data': imports, 'columns': ['id', 'file_id', 'from_module', 'type'] },
            'import_symbols': { 'data': import_symbols, 'columns': ['import_id', 'symbol', 'alias'] },
            'classes': { 'data': classes, 'columns': ['id', 'file_id', 'name', 'start_line', 'end_line', 'hash', 'inheritances'] },
            'class_attributes': { 'data': attributes, 'columns': ['class_id', 'name', 'attribute_type', 'default_value', 'line_number', 'is_static'] },
            'functions': { 'data': chunks, 'columns': ['id', 'file_id', 'class_id', 'name', 'start_line', 'end_line',  'content', 'signature', 'cyclomatic_complexity', 'score', 'hash'] },
            'call_graph': { 'data': calls, 'columns': ['caller_id', 'function_name', 'call_line'] }
        }

        start_time = time.time()

        await Database().copy_multiple_tables(table_data)

        end_time = time.time()

        self.__logger.info(f"Finished saving project {project_id} in {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    import asyncio
    controller = ParseController(repo_path="D:\\Project\\Test")
    asyncio.run(controller.parse_project(project_id="13931f2a-a817-4ada-9d21-f4f4164ad1c8"))