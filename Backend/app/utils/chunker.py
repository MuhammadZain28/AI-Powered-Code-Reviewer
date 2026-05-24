import hashlib
from app.utils.tokenizer import normalize
import re
import json
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
    "function_declaration",
    "class_definition",
    "class_declaration",
    "field_definition",
    "function_expression",
    "constructor",
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
        self.__logger = get_logger("Chunker")
        self.current_class = ""
        self.chunks = []

    def get_parser(self):
        parser = Parser()
        parser.language = LANGUAGES[self.language]
        return parser

    def extract_chunks(self, node):
        if node.type in TARGET_NODES:
            if node.type in {"class_definition", "class_declaration"}:
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

                    right_value = self.get_source_segment(right) if right else None

                    if left:

                        attr = {
                            "name": self.get_source_segment(left),
                            "type": "function" if right_value and right_value.endswith("()") else "parameter",
                            "default_value": right_value,
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

            if child.type in {"function_definition", "method_definition", "function_declaration", "function_expression", "constructor"}:

                fn_name = self.get_node_name(child)
                if fn_name in {"__init__", "constructor"}:

                    attributes.extend(
                        self.extract_instance_attributes(child)
                    )

        return attributes

    def extract_instance_attributes(self, init_node):
        attributes = []

        def walk(node):
            if node.type in {"expression_statement"}:

                assignment_expr = self.get_source_segment(node)
                left, right = assignment_expr.split("=")

                if (left):
                    attributes.append({
                        "name": left.strip().split(".")[-1],
                        "type": "function" if right and right.endswith("()") else "parameter",
                        "default_value": right,
                        "is_static": False
                    })

            elif node.type == "typed_assignment":

                left = node.child_by_field_name("left")
                right = node.child_by_field_name("right")
                type_node = node.child_by_field_name("type")

                if left and left.type == "attribute":

                    object_node = left.child_by_field_name("object")
                    attr_node = left.child_by_field_name("attribute")

                    if (
                        object_node and
                        attr_node
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
                "switch_statement",
                "try_statement"
            ]:
                self.complexity["branching"] += 1
            elif curr.type in ["for_statement", "while_statement"]:
                self.complexity["loop"] += 1

            elif curr.type in ["or_expression", "and_expression"]:
                self.complexity["logical"] += 1

            elif curr.type in {"call", "call_expression", "member_expression"}:
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
            if child.type in {"identifier", "property_identifier", "field_identifier", "type_identifier"}:
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

def classify_calls(chunk_calls: list, imports: list) -> dict:
        """
        chunk_calls   = ['faiss.IndexIDMap', 'np.linalg.norm', 'get_logger', 'self.save_index']
        imports       = parsed import list from your schema
        class_methods = ['__init__', 'normalize_embeddings', 'add_embeddings', ...]
        """

        # Step 1: Build alias → source map from imports
        # np        → numpy        (external)
        # get_logger → app.utils.logger (internal project)
        # Path      → pathlib      (stdlib)
        
        alias_map = {}
        for imp in imports:
            for module, alias in zip(imp["modules"], imp["aliases"]):
                key = alias if alias else module
                alias_map[key] = {
                    "source": imp["source"],
                    "module": module
                }

        # Step 2: Known external libraries (expand this list)
        EXTERNAL_LIBS = {"faiss", "numpy", "np", "torch", "sklearn",
                        "pandas", "pd", "requests", "flask", "fastapi"}

        STDLIB = {"pathlib", "os", "sys", "json", "re", "math",
                "collections", "itertools", "typing"}

        result = {
            "internal_calls": [],       # self.method() — same class
            "cross_file_calls": [],     # imported from your own project
            "external_lib_calls": [],   # third party libraries
            "stdlib_calls": [],         # python standard library
            "unresolved_calls": []      # couldn't classify
        }

        for call in chunk_calls:
            root = call.split(".")[0]   # faiss.IndexIDMap → faiss

            # self.method() — internal to class
            if root == "self":
                method_name = call.split(".")[1] if "." in call else call
                result["internal_calls"].append({
                    "call": call,
                    "resolves_to": method_name
                })

            # aliased or direct external lib
            elif root in EXTERNAL_LIBS:
                result["external_lib_calls"].append({
                    "call": call,
                    "library": alias_map.get(root, {}).get("source", root)
                })

            # stdlib
            elif root in STDLIB:
                result["stdlib_calls"].append({
                    "call": call,
                    "library": alias_map.get(root, {}).get("source", root)
                })

            # came from an import → could be cross-file project code
            elif root in alias_map:
                source = alias_map[root]["source"]
                # if source has your project namespace → cross-file
                if source.startswith("app.") or '/' in source:
                    result["cross_file_calls"].append({
                        "call": call,
                        "source_module": source,
                        "resolves_to": alias_map[root]["module"]
                    })
                else:
                    result["external_lib_calls"].append({
                        "call": call,
                        "library": source
                    })

            else:
                result["unresolved_calls"].append({
                    "call": call
                })

        return result

if __name__ == "__main__":
    # file = r"D:\Project\Inventory-App\backend\controller\customer.js"
    # language = "JavaScript"
    file = r"D:\Project\AI-Powered Code Reviewer\Backend\app\utils\faiss.py"
    language = "Python"
    with open(file, "r") as f:
        code = f.read()

    print("Clean Code:")

    chunker = Chunker(code, language, "faiss.py")
    classes, imports, chunks = chunker.chunk_code()
    import_statements = []
    for import_statement in imports:
        import_statement = normalize(import_statement, 'python')
        import_statements.append(import_statement.to_dict())
        print(f"Import: {json.dumps(import_statement.to_dict(), indent=2)}")
    results = []
    for cls in classes:
        print(f"Class: {cls['name']}")
        for chunk in cls['chunks']:
            print(f"  Method: {chunk['name']}")
            print(f"    Complexity: {chunk['complexity']}")
            chunk['calls'] = classify_calls(chunk['calls'], import_statements)
            for call_type, calls in chunk['calls'].items():
                for call in calls:
                    print(f"    {call_type}: {call['call'], }")