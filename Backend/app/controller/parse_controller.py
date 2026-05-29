from app.models.chunks import Chunk
from app.services.parser_service import ParserService
from app.db_manager.database import Database
from app.services.embedding_service import EmbeddingService
from app.utils.logger import get_logger
from app.utils.faiss import FaissIndex
import time


class ParseController:
    def __init__(self, repo_path: str):
        self.parser_service = ParserService(repo_path)
        self.embedding_service = EmbeddingService()
        self.faiss_index = FaissIndex(dimension=384)
        self.__logger = get_logger("ParseController")

    async def parse_project(self, project_id: str) -> dict:
        self.__logger.info(f"Starting to parse project {project_id}")

        start_time = time.time()

        parsed_data = self.parser_service.parse_project(project_id=project_id)
        files = parsed_data['files']
        imports = parsed_data['imports']
        classes = parsed_data['classes']
        calls = parsed_data['calls']
        chunks = parsed_data['chunks']
        attributes = parsed_data['attributes']
        import_modules = parsed_data['import_modules']

        end_time = time.time()

        self.__logger.info(f"Finished parsing project {project_id} in {end_time - start_time:.2f} seconds. Starting to save to database...")

        start_time = time.time()

        await Database().connect()

        end_time = time.time()

        self.__logger.info(f"Connected to database in {end_time - start_time:.2f} seconds. Starting to save data...")

        start_time = time.time()

        table_data = {
            'files': { 'data': files, 'columns': ['id', 'project_id', 'path', 'language', 'hash'] },
            'imports': { 'data': imports, 'columns': ['id', 'file_id', 'type', 'source'] },
            'import_modules': { 'data': import_modules, 'columns': ['import_id', 'module', 'alias'] },
            'classes': { 'data': classes, 'columns': ['id', 'file_id', 'name', 'start_line', 'end_line', 'docstring', 'inheritance'] },
            'class_attributes': { 'data': attributes, 'columns': ['class_id', 'name', 'attribute_type', 'default_value', 'is_static'] },
            'chunks': { 'data': chunks, 'columns': ['id', 'file_id', 'class_id', 'name', 'content', 'start_line', 'end_line', 'chunk_type', 'hash', 'docstring', 'parameters', 'return_values'] },
            'calls': { 'data': calls, 'columns': ['caller_id', 'call_type', 'function_name', 'source', 'library', 'resolve_to'] }
        }

        await Database().copy_multiple_tables(table_data)

        ids, vectors = self.embedding_service.embed_chunks(chunks)

        self.__logger.info(f"Processed Chunks with {len(vectors)} vectors and {len(ids)} ids.")

        if len(vectors) == len(ids):
            self.faiss_index.add_embeddings(vectors, ids)

        end_time = time.time()

        self.__logger.info(f"Finished parsing project {project_id} in {end_time - start_time:.2f} seconds")

        return {
            "files": len(files),
            "imports": len(imports),
            "classes": len(classes),
            "calls": len(calls),
            "chunks": len(chunks),
            "attributes": len(attributes),
            "import_modules": len(import_modules)
        }

    async def search_chunks(self, query: str, k: int = 5):
        query_vector = self.embedding_service.model.encode(query, convert_to_numpy=True)
        ids, scores = self.faiss_index.search(query_vector, k)
        results = []
        for chunk_id, score in zip(ids, scores):
            chunk = await Chunk(id=chunk_id, file_id=None, chunk_type="", name="", start_line=0, end_line=0, content="").fetch()
            if chunk:
                results.append({
                    "id": chunk['id'],
                    "file_id": chunk['file_id'],
                    "chunk_type": chunk['chunk_type'],
                    "name": chunk['name'],
                    "start_line": chunk['start_line'],
                    "end_line": chunk['end_line'],
                    "content": chunk['content'],
                    "score": float(score)
                })
        return results

    def load_faiss_index(self):
        self.faiss_index.load_index()
        return self.faiss_index.index.ntotal

if __name__ == "__main__":
    import asyncio
    controller = ParseController(repo_path="D:\\Project\\NUCES")
    asyncio.run(controller.parse_project(project_id="21ccbbaa-049d-434e-bbc9-65f2e89660fa"))