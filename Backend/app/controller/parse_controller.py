from app.models.files import File
from app.models.chunks import Chunk
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
            embeddings = self.embedding_service.embed_chunks(file_data['chunks'], file_data['language'], file=file_path.split('/')[-1])
            for chunk_data in embeddings:
                chunk = Chunk(
                    id=None,
                    file_id=file.id,
                    chunk_type=chunk_data['meta']['type'],
                    name=chunk_data['meta']['name'],
                    start_line=chunk_data['meta']['start_line'],
                    end_line=chunk_data['meta']['end_line'],
                    content=chunk_data['meta']['content'],
                )
                await chunk.save()
                vector.append(chunk_data['vector'])
                ids.append(chunk.id)
                self.__logger.info(f"Processed chunk {chunk.name} in file {file_path} with embedding ID {chunk.id}.")
        self.__logger.info(f"Processed file {file_path} with {len(vector)} vectors and {len(ids)} ids.")
        self.faiss_index.add_embeddings(vector, ids)
        return parsed_data

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