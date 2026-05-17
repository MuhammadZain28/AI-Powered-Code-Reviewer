from tree_sitter import Language, Parser
import tree_sitter_cpp
import tree_sitter_java
import tree_sitter_javascript
import tree_sitter_typescript
import tree_sitter_python
# from app.utils.logger import get_logger


LANGUAGES = {
    "Python": Language(tree_sitter_python.language()),
    "JavaScript": Language(tree_sitter_javascript.language()),
    "JavaScript (React)": Language(tree_sitter_javascript.language()),
    "C++": Language(tree_sitter_cpp.language()),
    "Java": Language(tree_sitter_java.language()),
    "TypeScript": Language(tree_sitter_typescript.language_typescript()),
    "TypeScript (React)": Language(tree_sitter_typescript.language_tsx()),
}
TARGET_NODES = {
    "function_definition",
    "method_declaration",
    "function_declaration",
    "class_definition",
}
class Chunker():
    def __init__(self, source_code: str, language: str, file_path: str):
        self.source_code = source_code
        self.language = language
        self.file_path = file_path
        self.lines = source_code.splitlines()
        # self.logger = get_logger("Chunker")
        self.current_class = None
        self.chunk_id = 0
        self.chunks = []

    def get_parser(self):
        parser = Parser()
        parser.language = LANGUAGES[self.language]
        return parser

    def extract_chunks(self, node):
        if node.type in TARGET_NODES:
            if node.type == "class_definition":
                self.current_class = self.get_node_name(node)
            else:
                chunk = self.build_chunk(node, node.type)
                self.chunks.append(chunk)
                return

        for child in node.children:
            self.extract_chunks(child)

    def chunk_code(self) -> list:
        parser = self.get_parser()
        tree = parser.parse(bytes(self.source_code, "utf8"))
        root_node = tree.root_node
        self.extract_chunks(root_node)
        return self.chunks

    def build_chunk(self, node, chunk_type):
        name = ""
        if self.current_class:
            name = f"{self.current_class}.{self.get_node_name(node)}"
        else:
            name = self.get_node_name(node, chunk_type)
        chunk = {
            'embedding_id': self.chunk_id,
            'name': name,
            'content': self.get_source_segment(node),
            'start_line': node.start_point[0] + 1,
            'end_line': node.end_point[0] + 1,
            'type': chunk_type
        }
        self.chunk_id += 1
        return chunk

    def get_node_name(self, node):
        for child in node.children:
            if child.type == "identifier":
                return self.source_code[child.start_byte:child.end_byte]
        return "unknown"

    def get_source_segment(self, node):
        return self.source_code[node.start_byte:node.end_byte]

if __name__ == "__main__":
    with open("faiss.py", "r") as f:
        source_code = f.read()
    chunker = Chunker(source_code, "Python", "example.py")
    chunks = chunker.chunk_code()
    for chunk in chunks:
        print(f"Chunk Name: {chunk['name']}")
        print(f"Chunk Type: {chunk['type']}")
        print(f"Start Line: {chunk['start_line']}, End Line: {chunk['end_line']}")
        print(f"Content:\n{chunk['content']}\n{'-'*40}\n")