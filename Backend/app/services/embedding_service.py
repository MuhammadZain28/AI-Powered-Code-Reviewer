from sentence_transformers import SentenceTransformer
from app.utils.logger import get_logger

class EmbeddingService:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.logger = get_logger("EmbeddingService")

    def generate_embeddings(self, texts: list) -> list:
        try:
            embeddings = self.model.encode(texts)
            return embeddings
        except Exception as e:
            self.logger.error(f"Error generating embeddings: {e}")
            return []