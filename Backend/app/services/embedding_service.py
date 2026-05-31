from sentence_transformers import SentenceTransformer
from app.utils.logger import get_logger
import numpy as np

class EmbeddingService:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.logger = get_logger("EmbeddingService")

    def build_text(self, chunk: dict, function_calls: dict) -> str:
        purpose = chunk['docstring'] if chunk['docstring'] else chunk['name']
        return f"""
NAME: {chunk['name']}

PURPOSE:
{chunk['docstring']}.

CLASS NAME: {chunk['class_name']}

IMPORTS USED:
{'\n'.join(function_calls.get(chunk['id'], {}).get('libraries', []))}

PARAMETERS:
{'\n'.join(chunk['parameters'])}

FUNCTION CALLS:
{'\n'.join(function_calls.get(chunk['id'], {}).get('calls', []))}

RETURN VALUES:
{'\n'.join(chunk['return_values'])}

CODE:
{chunk['content']}
"""
    def embed_chunk(self, chunk_data: dict, function_calls: dict) -> np.ndarray:
        chunk = chunk_data['chunk']
        path = chunk_data['path']
        language = chunk_data['language']
        text = self.build_text(chunk, function_calls)
        try:
            embedding = self.model.encode(text)
            return embedding

        except Exception as e:
            self.logger.error(f"Error embedding chunk: {e}")
            return None

    def embed_chunks(self, chunks: dict, function_calls: dict) -> list:
        vectors = []
        ids = []
        for file_id, file_chunks in chunks.items():
            embedding = self.embed_chunk(file_chunks, function_calls)
            if embedding is not None:
                ids.append(file_chunks['chunk']['id'])
                vectors.append(embedding)
        return ids, vectors

if __name__ == "__main__":
    embedding_service = EmbeddingService()
    sample_chunk = {
        'chunk': {
            'id': 1,
            'name': 'example_function',
            'class_name': 'ExampleClass',
            'parameters': ['param1', 'param2'],
            'return_values': ['return1'],
            'docstring': 'This is an example function.',
            'content': 'def example_function(param1, param2):\n    return param1 + param2'
        },
        'path': '/path/to/file.py',
        'language': 'python'
    }
    function_calls = {1: {'calls': ['call1', 'call2'], 'libraries': []}}
    text = embedding_service.build_text(sample_chunk['chunk'], function_calls)
    print(text)