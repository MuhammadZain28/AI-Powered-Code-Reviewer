from sentence_transformers import SentenceTransformer
from app.utils.logger import get_logger
import numpy as np

class EmbeddingService:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.logger = get_logger("EmbeddingService")

    def build_text(self, chunk: dict, language: str) -> str:
        name = chunk.get("name", "")
        code = chunk.get("code", "")
        chunk_type = chunk.get("type", "")

        return f"""
TYPE: {chunk_type}
LANGUAGE: {language}
NAME: {name}

TASK SUMMARY:
This code implements a {chunk_type} in {language}.

CODE PURPOSE:
{self.infer_purpose(chunk)}

KEY CONCEPTS:
{self.extract_keywords(code)}

CODE:
{code}
"""
    def embed_chunk(self, chunk: dict, language: str) -> np.ndarray:
        text = self.build_text(chunk, language)
        try:
            embedding = self.model.encode(text)
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
