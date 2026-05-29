from sentence_transformers import SentenceTransformer
from app.utils.logger import get_logger
import numpy as np

class EmbeddingService:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.logger = get_logger("EmbeddingService")

    def build_text(self, chunk: tuple) -> str:
        name = chunk[3]
        code = chunk[4]
        chunk_type = chunk[7]
        docstring = chunk[9] if chunk[9] else f"{name}."
        parameters = chunk[10]
        return_values = chunk[11]

        return f"""
TYPE: {chunk_type}
NAME: {name}
PARAMETERS: {parameters}
FUNCTION CALLS: {code}
RETURN VALUES: {return_values}
TASK SUMMARY:
{docstring}.
CODE:
{code}
"""
    def embed_chunk(self, chunk: tuple) -> np.ndarray:
        text = self.build_text(chunk)
        try:
            embedding = self.model.encode(text)
            return embedding

        except Exception as e:
            self.logger.error(f"Error embedding chunk: {e}")
            return None

    def embed_chunks(self, chunks: list) -> list:
        vectors = []
        ids = []
        for chunk in chunks:
            embedding = self.embed_chunk(chunk)
            if embedding is not None:
                ids.append(chunk[0])
                vectors.append(embedding)
        return ids, vectors
