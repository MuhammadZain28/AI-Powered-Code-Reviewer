from sentence_transformers import SentenceTransformer
from app.utils.logger import get_logger
import numpy as np

class EmbeddingService:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.model = SentenceTransformer('./app/models/all-MiniLM-L6-v2')
        self.logger = get_logger("EmbeddingService")

    def build_text(self, chunk: dict, function_calls: dict) -> str:
        purpose = chunk['docstring'] if chunk['docstring'] else chunk['name']
        imports = function_calls.get(chunk['id'], {}).get('libraries')

        if imports is [] or imports is None:
            imports = "None"
        else:
            imports = '\n'.join(list(imports))
        parameters = chunk.get('parameters')
        if parameters is None or parameters is []:
            parameters = "None"
        else:
            parameters = '\n'.join(parameters)
        calls = function_calls.get(chunk['id'], {}).get('calls')
        if calls is None or calls is []:
            calls = "None"
        else:
            calls = '\n'.join(list(calls))
        return_values = chunk.get('return_values')
        if return_values is None or return_values is []:
            return_values = "None"
        else:
            return_values = '\n'.join(return_values)
        return f"""
NAME: {chunk['name']}

PURPOSE:
{purpose}.

CLASS NAME: {chunk['class']}

IMPORTS USED:
{imports}

PARAMETERS:
{parameters}

FUNCTION CALLS:
{calls}

RETURN VALUES:
{return_values}

CODE:
{chunk['content']}
"""
    def embed_chunk(self, texts: list) -> np.ndarray:
        try:
            embedding = self.model.encode(texts, batch_size=32, convert_to_numpy=True)
            return embedding

        except Exception as e:
            self.logger.error(f"Error embedding chunk: {e}")
            return None

    def embed_chunks(self, chunks: dict, function_calls: dict) -> list:
        vectors = []
        texts = []
        for _, file_chunks in chunks.items():
            for chunk in file_chunks['chunks']:
                text = self.build_text(chunk, function_calls)

                if text is not None:
                    texts.append(text)
        if texts:
            vectors = self.embed_chunk(texts)
        return vectors

if __name__ == "__main__":
    embedding_service = EmbeddingService()
    sample_chunk = {
        'chunk': {
            'id': 1,
            'name': 'example_function',
            'class': 'ExampleClass',
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