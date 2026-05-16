from sentence_transformers import SentenceTransformer
from app.utils.logger import get_logger
import numpy as np

class EmbeddingService:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.logger = get_logger("EmbeddingService")

    def build_text(self, chunk: dict, language: str) -> str:
        text = f"""Type: {chunk.get('type')}\nLanguage: {language}\nCode:\n{chunk.get('code')}"""
        return text

    def embed_chunk(self, chunk: dict, language: str) -> np.ndarray:
        text = self.build_text(chunk, language)
        try:
            embedding = self.model.encode(
                text,
                convert_to_numpy=True
            )
            return embedding

        except Exception as e:
            self.logger.error(f"Error embedding chunk: {e}")
            return None

    def embed_chunks(self, chunks: list, language: str) -> list:
        embeddings = []
        for chunk in chunks:
            embedding = self.embed_chunk(chunk, language)
            if embedding is not None:
                embeddings.append({
                    'meta': {
                        'embedding_id': chunk.get('embedding_id'),
                        'type': chunk.get('type'),
                        'name': chunk.get('name'),
                        'language': language,
                        'content': chunk.get('content'),
                        'start_line': chunk.get('start_line'),
                        'end_line': chunk.get('end_line')
                    },
                    'vector': embedding
                })
        return embeddings
