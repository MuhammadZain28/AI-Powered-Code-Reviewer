import hashlib
import re
from app.models.imports import Import
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
        self.class_chunk = []
        self.imports = []
        self.lines = source_code.splitlines()
        self.complexity = {"branching": 0, "loop": 0, "logical": 0, "function_call": 0, "return": 0}
        # self.__logger = get_logger("Chunker")
        self.current_class = ""
        self.chunks = []

    def get_parser(self):
        parser = Parser()
        parser.language = LANGUAGES[self.language]
        return parser

    def extract_chunks(self, node):
        if node.type in TARGET_NODES:

            if node.type == "class_definition":
                self.current_class = self.get_node_name(node)
                self.inheritances = self.extract_inheritances(node)
                self.attributes = self.extract_class_attributes(node)
                self.class_chunk.append(self.build_class(node))
                self.class_chunk[-1]['docstring'] = self.extract_docstring(node)
            else:
                chunk = self.build_chunk(node, node.type)
                chunk['params'] = self.extract_parameters(node)
                chunk['calls'], chunk["returns"] = self.extract_calls(node)
                chunk['docstring'] = self.extract_docstring(node)
                chunk['complexity'] = self.complexity
                self.complexity = {"branching": 0, "loop": 0, "logical": 0, "function_call": 0, "return": 0}
                self.chunks.append(chunk)
                if self.class_chunk and self.current_class:
                    self.class_chunk[-1]['chunks'].append(chunk)
                return

        if node.type in {"import_statement", "import_from_statement"}:
            self.imports.append(self.get_source_segment(node))

        for child in node.children:
            self.extract_chunks(child)

    def extract_class_attributes(self, class_node):

        attributes = []

        body = class_node.child_by_field_name("body")

        if not body:
            return attributes

        for child in body.children:

            # =========================
            # STATIC / CLASS ATTRIBUTES
            # =========================

            if child.type == "expression_statement":

                expr = child.children[0] if child.children else None

                if expr and expr.type == "assignment":

                    left = expr.child_by_field_name("left")
                    right = expr.child_by_field_name("right")

                    if left:

                        attr = {
                            "name": self.get_source_segment(left),
                            "type": None,
                            "default_value": self.get_source_segment(right) if right else None,
                            "is_static": True
                        }

                        attributes.append(attr)

                # typed assignment
                elif expr and expr.type == "typed_assignment":

                    left = expr.child_by_field_name("left")
                    right = expr.child_by_field_name("right")
                    type_node = expr.child_by_field_name("type")

                    if left:

                        attr = {
                            "name": self.get_source_segment(left),
                            "type": self.get_source_segment(type_node) if type_node else None,
                            "default_value": self.get_source_segment(right) if right else None,
                            "is_static": True
                        }

                        attributes.append(attr)

            # =========================
            # INSTANCE ATTRIBUTES
            # =========================

            if child.type == "function_definition":

                fn_name = self.get_node_name(child)

                if fn_name == "__init__" or fn_name == "constructor" or fn_name == "new" or fn_name == self.current_class:

                    attributes.extend(
                        self.extract_instance_attributes(child)
                    )

        return attributes

    def extract_instance_attributes(self, init_node):

        attributes = []

        def walk(node):

            if node.type == "assignment":

                left = node.child_by_field_name("left")
                right = node.child_by_field_name("right")

                if left and left.type == "attribute":

                    object_node = left.child_by_field_name("object")
                    attr_node = left.child_by_field_name("attribute")

                    if (
                        object_node and
                        attr_node and
                        self.get_source_segment(object_node) == "self"
                    ):

                        attributes.append({
                            "name": self.get_source_segment(attr_node),
                            "type": None,
                            "default_value": self.get_source_segment(right) if right else None,
                            "is_static": False
                        })

            if node.type == "typed_assignment":

                left = node.child_by_field_name("left")
                right = node.child_by_field_name("right")
                type_node = node.child_by_field_name("type")

                if left and left.type == "attribute":

                    object_node = left.child_by_field_name("object")
                    attr_node = left.child_by_field_name("attribute")

                    if (
                        object_node and
                        attr_node and
                        self.get_source_segment(object_node) == "self"
                    ):

                        attributes.append({
                            "name": self.get_source_segment(attr_node),
                            "type": self.get_source_segment(type_node) if type_node else None,
                            "default_value": self.get_source_segment(right) if right else None,
                            "is_static": False
                        })

            for child in node.children:
                walk(child)

        walk(init_node)

        return attributes

    def extract_inheritances(self, class_node):

        inheritances = []

        superclasses = class_node.child_by_field_name("superclasses")

        if not superclasses:
            return inheritances

        for child in superclasses.children:

            if child.type == "identifier":
                inheritances.append(
                    self.get_source_segment(child)
                )

        return inheritances

    def extract_docstring(self, node):
        body = node.child_by_field_name("body")
        if not body:
            return None

        for child in body.children:

            if child.type in ["{", "}", "(", ")", ","]:
                continue

            if child.type == "expression_statement":
                inner = child.children[0] if child.children else None

                if inner and inner.type == "string":
                    return self.source_code[inner.start_byte:inner.end_byte]

            if child.type == "comment":
                if child.start_point[0] == node.start_point[0] or child.start_point[0] <= node.start_point[0] + 1:
                    return self.source_code[child.start_byte:child.end_byte]

            break

        return None

    def extract_parameters(self, node):

        params = []

        parameters_node = node.child_by_field_name("parameters")
        if not parameters_node:
            return params

        for child in parameters_node.children:

            if child.type in ["(", ")", ",", "{", "}"]:
                continue

            if child.type == "identifier":
                params.append(self.get_source_segment(child))

            elif child.type == "typed_parameter":
                name_node = child.child_by_field_name("name")
                if name_node:
                    params.append(self.get_source_segment(name_node))

            elif child.type == "default_parameter":
                name_node = child.child_by_field_name("name")
                if name_node:
                    params.append(self.get_source_segment(name_node))
        return params

    def extract_calls(self, node):

        calls = []
        returns = []

        def traverse(curr):
            if curr.type in [
                "if_statement",
                "match_statement",
                "case_statement",
                "except_clause",
                "conditional_expression",
            ]:
                self.complexity["branching"] += 1
            elif curr.type in ["for_statement", "while_statement"]:
                self.complexity["loop"] += 1

            elif curr.type in ["or_expression", "and_expression"]:
                self.complexity["logical"] += 1

            elif curr.type == "call":
                func_node = curr.child_by_field_name("function")

                if func_node:
                    self.complexity["function_call"] += 1
                    call_name = self.get_source_segment(func_node)
                    calls.append(call_name)

            elif curr.type == "return_statement":
                self.complexity["return"] += 1
                return_value = self.get_source_segment(curr)
                returns.append(return_value.split("return", 1)[-1].strip())

            for child in curr.children:
                traverse(child)

        traverse(node)

        return (calls, returns)

    def chunk_code(self):
        parser = self.get_parser()
        self.source_code = self.clean_code(self.source_code)
        tree = parser.parse(bytes(self.source_code, "utf8"))
        root_node = tree.root_node
        self.extract_chunks(root_node)
        return (self.class_chunk, self.imports, self.chunks)

    def build_class(self, node):
        cls = {
            'name': self.get_node_name(node),
            'inheritances': self.inheritances,
            'attributes': self.attributes,
            'content': self.get_source_segment(node),
            'start_line': node.start_point[0] + 1,
            'end_line': node.end_point[0] + 1,
            'type': node.type,
            'chunks': []
        }
        return cls
    def build_chunk(self, node, chunk_type):
        code = self.get_source_segment(node)
        chunk = {
            'name': self.get_node_name(node),
            'content': code,
            'start_line': node.start_point[0] + 1,
            'end_line': node.end_point[0] + 1,
            'type': chunk_type,
            'hash': self.calculate_hash(code)
        }
        return chunk

    def calculate_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def get_node_name(self, node):
        for child in node.children:
            if child.type == "identifier":
                return self.source_code[child.start_byte:child.end_byte]
        return "unknown"

    def get_source_segment(self, node):
        return self.source_code[node.start_byte:node.end_byte]

    def clean_code(self, code: str) -> str:
        parser = self.get_parser()
        tree = parser.parse(bytes(code, "utf8"))
        root = tree.root_node

        removals = []

        def walk(node):
            if node.type == "comment":
                removals.append((node.start_byte, node.end_byte))
            for child in node.children:
                walk(child)

        walk(root)

        for start, end in sorted(removals, reverse=True):
            code = code[:start] + code[end:]

        code = re.sub(r'\n{3,}', '\n\n', code)
        return code.strip()

if __name__ == "__main__":
    with open("D:/Project/Test/Graphs.py", "r") as f:
        code = f.read()

    print("Clean Code:")
    
    chunker = Chunker(code, "Python", "faiss.py")
    classes, imports, chunks = chunker.chunk_code()
    imports = Import(id=None, file_id=None, import_statement=imports[0], language="python")
    print(f"imports: {imports.normalize_import()}")
    for cls in classes:
        print(f"Class: {cls['name']}")
        print(f"  Inheritances: {cls['inheritances']}")
        print(f"  Attributes: {cls['attributes']}")
        print(f"  Docstring: {cls['docstring']}")
        for chunk in cls['chunks']:
            print(f"  Chunk: {chunk['name']}")
            print(f"    Type: {chunk['type']}")
            print(f"    Start Line: {chunk['start_line']}")
            print(f"    End Line: {chunk['end_line']}")
            print(f"    Parameters: {chunk['params']}")
            print(f"    Calls: {chunk['calls']}")
            print(f"    Returns: {chunk['returns']}")
            print(f"    Complexity: {chunk['complexity']}")
            print(f"    Docstring: {chunk['docstring']}")