from tree_sitter import Language, Parser
import tree_sitter_cpp
import tree_sitter_java
import tree_sitter_javascript
import tree_sitter_typescript
import tree_sitter_python
from app.utils.logger import get_logger


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
    "class_definition",
    "class_declaration",
    "function_declaration"
}
class Chunker():
    def __init__(self, source_code: str, language: str):
        self.source_code = source_code
        self.language = language
        self.lines = source_code.splitlines()
        self.logger = get_logger("Chunker")
        self.current_class = None
        self.chunk_id = 0
        self.chunks = []

    def get_parser(self):
        parser = Parser()
        parser.language = LANGUAGES[self.language]
        return parser

    def extract_chunks(self, node):
        if node.type in TARGET_NODES:
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
        chunk = {
            'id': self.chunk_id,
            'code': self.get_source_segment(node),
            'start_line': node.start_point[0] + 1,
            'end_line': node.end_point[0] + 1,
            'type': chunk_type
        }
        self.chunk_id += 1
        return chunk

    def get_source_segment(self, node):
        return self.source_code[node.start_byte:node.end_byte]