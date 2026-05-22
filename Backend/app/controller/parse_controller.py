from app.models.imports import Import
from app.models.files import File
from app.models.chunks import Chunk
from app.models.classes import Class
from app.services.parser_service import ParserService
from app.services.embedding_service import EmbeddingService
from app.utils.logger import get_logger
from app.utils.faiss import FaissIndex


class ParseController:
    def __init__(self, repo_path: str):
        self.parser_service = ParserService(repo_path)
        self.embedding_service = EmbeddingService()
        self.faiss_index = FaissIndex(dimension=384)
        self.__logger = get_logger("ParseController")

    async def parse_project(self, project_id: str) -> dict:
        vector = []
        ids = []
        parsed_data = self.parser_service.parse_project()
        for file_path, file_data in parsed_data.items():
            file = File(id=None, project_id=project_id, path=file_path, language=file_data['language'], hash=file_data['hash'])
            await file.save()
            await self.insert_import(file_data['imports'], file_data['language'], file.id)

            if file_data['classes']:
                for cls in file_data['classes']:
                    class_id = await self.insert_class({
                        'file_id': file.id,
                        'name': cls['name'],
                        'start_line': cls['start_line'],
                        'end_line': cls['end_line'],
                        'docstring': cls['docstring'],
                        'attributes': cls.get('attributes', []),
                        'inheritances': cls.get('inheritances', [])
                    })

                    for chunk in cls['chunks']:
                        chunk_id = await self.insert_chunk(chunk_data={
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

            else:
                for chunk in file_data['chunks']:
                    chunk_id = await self.insert_chunk(chunk_data={
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
                    }, class_id=None)
                    ids.append(chunk_id)

            embeddings = self.embedding_service.embed_chunks(file_data['chunks'], file_data['language'], file=file_path)
            vector.extend(vector['vector'] for vector in embeddings)

        self.__logger.info(f"Processed file {file_path} with {len(vector)} vectors and {len(ids)} ids.")
        if len(vector) == len(ids) and len(vector) > 0:
            self.faiss_index.add_embeddings(vector, ids)
        return parsed_data

    async def insert_chunk(self, chunk_data: dict, class_id: int = None):
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
        self.__logger.info(f"Inserted new chunk {chunk.name} with ID {chunk.id} into FAISS index.")
        return chunk.id

    async def insert_class(self, class_data: dict):
        class_chunk = Class(
            id=None,
            file_id=class_data['file_id'],
            name=class_data['name'],
            start_line=class_data['start_line'],
            end_line=class_data['end_line'],
            docstring=class_data['docstring'],
            attributes=class_data.get('attributes', []),
            inheritances=class_data.get('inheritances', [])
        )
        await class_chunk.save()
        self.__logger.info(f"Inserted new class {class_chunk.name} with ID {class_chunk.id} into FAISS index.")
        return class_chunk.id

    async def insert_import(self, imports: list, language: str, file_id: str):
        import_chunk = Import(file_id=file_id)
        for import_statement in imports:
            await import_chunk.save(import_statement, language)
            self.__logger.info(f"Inserted new import {import_chunk.modules} with ID {import_chunk.id} into FAISS index.")
        return import_chunk.id

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