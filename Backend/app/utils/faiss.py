import faiss
import numpy as np
from pathlib import Path
from app.utils.logger import get_logger

base_path = Path(__file__).resolve().parents[2]

class FaissIndex:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(FaissIndex, cls).__new__(cls)
        return cls._instance

    def __init__(self, dimension: int):
        if hasattr(self, 'initialized') and self.initialized:
            return
        self.dimension = dimension
        self.index_path = base_path / "app" / "storage" / "index.faiss"

        self.logger = get_logger("FaissIndex")
        self.index = self.load_index()

        self.initialized = True

    def normalize_embeddings(self, vector):
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm

    def add_embeddings(self, vectors: list, ids: list):
        try:
            vectors = np.array(vectors, dtype=np.float32)
            faiss.normalize_L2(vectors)
            self.index.add_with_ids(vectors, np.array(ids, dtype=np.int64))
        except Exception as e:
            print(f"Error adding embeddings: {e}")
        self.save_index()
        return self.index.ntotal

    def save_index(self):
        try:
            faiss.write_index(self.index, str(self.index_path))
        except Exception as e:
            print(f"Error saving index: {e}")

    def load_index(self):
        if self.index_path.exists():
            self.logger.info("Loading FAISS index from disk")
            return faiss.read_index(str(self.index_path))
        else:
            self.logger.info("Creating new FAISS index")
            return faiss.IndexIDMap(faiss.IndexFlatIP(self.dimension))


    def search(self, vector, k=5):
        """Search for similar embeddings in the index"""
        vector = np.array([vector], dtype=np.float32)

        faiss.normalize_L2(vector)
        # Perform the search
        scores, ids = self.index.search(vector, k)

        self.logger.info(f"Search results - IDs: {ids[0]}, Scores: {scores[0]}")

        return (ids[0], scores[0])

if __name__ == "__main__":
    faiss_index = FaissIndex(dimension=384)
    faiss_index.load_index()
    print(f"Total embeddings in index: {faiss_index.index.ntotal}")