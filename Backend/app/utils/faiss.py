import faiss
import numpy as np
from pathlib import Path

base_path = Path(__file__).resolve().parents[2]

class FaissIndex:
    def __init__(self, dimension: int):
        self.dimension = dimension
        self.index_path = base_path / "app" / "storage" / "index.faiss"
        self.index = faiss.IndexIDMap(faiss.IndexFlatIP(dimension))

    def normalize_embeddings(self, vector):
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm

    def add_embeddings(self, vectors: list, ids: list):
        if isinstance(vectors[0], (int, float, np.floating)):
            vectors = [vectors]
        try:
            vecs = []
            for v in vectors:
                v = np.array(v, dtype=np.float32)
                faiss.normalize_L2(v)
                vecs.append(v)
            self.index.add_with_ids(np.array(vecs), np.array(ids))
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
        self.index = faiss.read_index(str(self.index_path))

    def search(self, query_vector: list, top_k: int = 5):
        query_vector = np.array(query_vector, dtype=np.float32)
        norm_query_vector = self.normalize_embeddings(query_vector)
        distances, indices = self.index.search(np.array([norm_query_vector]), top_k)
        return indices[0], distances[0]
