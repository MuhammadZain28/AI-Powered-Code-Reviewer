import hashlib
from app.utils.tokenizer import normalize
from uuid6 import uuid7
import re
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

FRAMEWORK_NAMES = {
    "save", "delete", "update", "create", "get", "set",
    "to_json", "from_json", "to_dict", "from_dict",
    "render", "serialize", "deserialize", "__repr__", "__str__", "__eq__", "__hash__"
}

JS_LIFECYCLE = {
    "constructor", "componentdidmount", "componentdidupdate",
    "componentwillmount", "useeffect"
}
class Chunker():
    def __init__(self, source_code: str, language: str, file_id: str):
        self.source_code = source_code
        self.language = language
        self.file_id = file_id
        self.class_chunk = []
        self.imports = []
        self.imports_modules = []
        self.calls = []
        self.attributes = []
        self.chunks = []
        self.complexity = 1
        self.current_class = None
        self.class_name = None
        self.functions = {}

        self.__logger = get_logger("Chunker")

    def get_parser(self):
        parser = Parser()
        if self.language not in LANGUAGES:
            self.__logger.error(f"Unsupported language: {self.language}")
            raise ValueError(f"Unsupported language: {self.language} for file")
        parser.language = LANGUAGES[self.language]
        return parser

    def extract_chunks(self, node, chunk_map: dict = None, class_map: dict = None):
        if node.type in TARGET_NODES:
            if node.type in {"class_definition", "class_declaration"}:
                self.class_name = self.get_node_name(node)
                code = self.get_source_segment(node)
                code_hash = self.calculate_hash(code)

                if class_map:
                    self.__logger.info(f"Processing class '{self.class_name}' for change management")
                    data = class_map.get(self.class_name, {"id": None, "hash": None})
    
                    if data['id'] and data['hash'] == code_hash:
                        self.__logger.info(f"Class '{self.class_name}' is unchanged. Skipping re-chunking.")
                        del class_map[self.class_name]  # Remove from map to identify deleted classes later
                        return
                    
                    elif data['id'] and data['hash'] != code_hash:
                        self.__logger.info(f"Class '{self.class_name}' has changed. Re-chunking with existing ID.")
                        self.current_class = data['id']
                        del class_map[self.class_name]  # Remove from map to identify deleted classes later
                    
                    else:
                        self.current_class = uuid7()
                
                else:
                    self.current_class = uuid7()

                self.inheritances = self.extract_inheritances(node)
                self.attributes.extend(self.extract_class_attributes(node))
                docstring = self.extract_docstring(node)
                self.class_chunk.append(self.build_class(self.current_class, node, self.class_name, code_hash, docstring))

            else:
                name = self.get_node_name(node)
                code = self.get_source_segment(node)
                code_hash = self.calculate_hash(code)

                self.__logger.info(f"Processing chunk '{name}'")

                if chunk_map:
                    self.__logger.info(f"Processing chunk '{name}' for change management")
                    data = chunk_map.get(name, {"id": None, "hash": None})

                    if data['id'] and data['hash'] == code_hash:
                        self.__logger.info(f"Chunk '{name}' is unchanged. Skipping re-chunking.")
                        del chunk_map[name]  # Remove from map to identify deleted chunks later
                        return

                    elif data['id'] and data['hash'] != code_hash:
                        id = data['id']
                        del chunk_map[name]  # Remove from map to identify deleted chunks later

                    else:
                        id = uuid7()

                else:
                    id = uuid7()

                params = self.extract_parameters(node)
                calls, returns = self.extract_calls(node)
                docstring = self.extract_docstring(node)

                chunk = self.build_chunk(id, node, docstring=docstring, parameters=params, return_values=returns, complexity=self.complexity)

                self.calls.extend(self.classify_calls(calls, self.imports, self.imports_modules, id))

                self.chunks.append(chunk)

                return

        if node.type in {"import_statement", "import_from_statement"}:
            import_code = self.get_source_segment(node)

            normalized_import = normalize(import_code, self.language, file_id=self.file_id)
            self.imports.append(normalized_import[0])
            self.imports_modules.extend(normalized_import[1])

        for child in node.children:
            self.extract_chunks(child, chunk_map=chunk_map, class_map=class_map)

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

                        attr = (
                            self.current_class,
                            self.get_source_segment(left),
                            "function" if right_value and right_value.endswith("()") else "parameter",
                            right_value,
                            True
                        )

                        attributes.append(attr)

                # typed assignment
                elif expr and expr.type == "typed_assignment":

                    left = expr.child_by_field_name("left")
                    right = expr.child_by_field_name("right")
                    type_node = expr.child_by_field_name("type")

                    if left:

                        attr = (
                            self.current_class,
                            self.get_source_segment(left),
                            self.get_source_segment(type_node) if type_node else None,
                            self.get_source_segment(right) if right else None,
                            True
                        )

                        attributes.append(attr)

            # =========================
            # INSTANCE ATTRIBUTES
            # =========================

            if child.type in {"function_definition", "method_definition", "function_declaration", "function_expression", "constructor"}:

                fn_name = self.get_node_name(child)
                if fn_name in {"__init__", "constructor", self.current_class}:
                    
                    attributes.extend(
                        self.extract_instance_attributes(child)
                    )

        return attributes

    def extract_instance_attributes(self, init_node):
        attributes = []

        def walk(node):
            if node.type in {"expression_statement"}:

                assignment_expr = self.get_source_segment(node)
                parts = assignment_expr.split("=")
                if len(parts) != 2:
                    left = parts[0].strip()
                    right = None
                else:
                    left, right = parts[0].strip(), parts[1].strip()

                if (left):
                    attributes.append((
                        self.current_class,                                             # associate attribute with its class
                        left.strip().split(".")[-1],                                    # attribute name (e.g., "self.attribute" → "attribute")
                        "function" if right and right.endswith("()") else "parameter",  # type based on whether it looks like a function call
                        right,                                                          # default value (the right-hand side of the assignment)
                        False                                                           # instance attribute, not static
                    ))

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

                        attributes.append((
                            self.current_class,
                            self.get_source_segment(attr_node),
                            self.get_source_segment(type_node) if type_node else None,
                            self.get_source_segment(right) if right else None,
                            False
                        ))

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
            if curr.type in {
                "if_statement",
                "match_statement",
                "case_statement",
                "except_clause",
                "conditional_expression",
                "switch_statement",
                "try_statement",
                "for_statement",
                "while_statement",
                "or_expression",
                "and_expression"
            }:
                self.complexity += 1

            elif curr.type in {"call", "call_expression", "member_expression"}:
                func_node = curr.child_by_field_name("function")

                if func_node:
                    call_name = self.get_source_segment(func_node)
                    parts = call_name.split(".")
                    if parts[0] in {'db', 'database', 'session', 'Database()'} or parts[-1].lower() in {"fetch", "execute", "query", "save", "add", "update", "delete"}:
                        self.complexity += 2
                    calls.append(call_name)

            elif curr.type == "return_statement":
                return_value = self.get_source_segment(curr)
                returns.append(return_value.split("return", 1)[-1].strip())

            for child in curr.children:
                traverse(child)

        traverse(node)

        return (calls, returns)

    def chunk_code(self) -> dict:
        parser = self.get_parser()
        self.source_code = self.clean_code(self.source_code)
        tree = parser.parse(bytes(self.source_code, "utf8"))
        root_node = tree.root_node
        self.extract_chunks(root_node)
        return {
            "classes": self.class_chunk,
            "imports": self.imports,
            "chunks": self.chunks,
            "calls": self.calls,
            "attributes": self.attributes,
            "import_modules": self.imports_modules
        }

    def chunk_change_code(self, chunk_map: dict, class_map: dict) -> dict:
        parser = self.get_parser()
        self.source_code = self.clean_code(self.source_code)
        tree = parser.parse(bytes(self.source_code, "utf8"))
        root_node = tree.root_node
        self.__logger.info(f"chunk_map for change management: {len(chunk_map)} and class_map: {len(class_map)}")
        self.extract_chunks(root_node, chunk_map=chunk_map, class_map=class_map)
        self.__logger.info(f"After chunking, remaining chunk_map: {len(chunk_map)}, remaining class_map: {len(class_map)}")

        return {
            "classes": self.class_chunk,
            "imports": self.imports,
            "chunks": self.chunks,
            "calls": self.calls,
            "attributes": self.attributes,
            "import_modules": self.imports_modules,
            "class_map": class_map,
            "chunk_map": chunk_map
        }


    def build_class(self, id, node, name, code_hash, docstring=None):
        self.__logger.info(f"Building class '{name}' with hash {code_hash}")
        cls = (
            id,                                                     # unique identifier for the class
            self.file_id,                                           # associate class with its file
            name,                                                   # human-readable class name
            node.start_point[0] + 1,                                # line numbers are 0-indexed in tree-sitter
            node.end_point[0] + 1,                                  # end line of the class
            docstring,                                              # docstring for the class
            self.inheritances,                                      # list of parent classes
            code_hash                                               # hash of the class content for quick comparisons
        )
        return cls

    def build_chunk(self, id, node, docstring=None, parameters=None, return_values=None, complexity=1):
        code = self.get_source_segment(node)
        name = self.get_node_name(node)
        start = node.start_point[0] + 1
        end = node.end_point[0] + 1
        
        chunk_type, score = self.classify_function(name, start, end, complexity, len(self.calls))

        chunk = (
            id,                             # unique identifier for the chunk
            self.file_id,                   # associate chunk with its file
            self.current_class,             # associate chunk with its class (if any)
            self.class_name,                # associate class name
            name,                           # human-readable name (function name, method name, etc.)
            code,                           # actual code content of the chunk
            start,                          # start line of the chunk
            end,                            # end line of the chunk
            chunk_type,                     # type of chunk (function, method, class, etc.)
            score,                          # priority score for review
            self.calculate_hash(code),      # hash of the chunk content for quick comparisons
            docstring,                      # docstring for the chunk
            parameters,                     # list of parameters if it's a function/method
            return_values,                  # list of return values if it's a function/method
            complexity                      # complexity metrics for the chunk
        )
        self.complexity = 1
        self.functions[name] = id
        return chunk
    
    def classify_function(self, name, start, end, complexity, calls=0):
        """
        Returns: skip | wrapper | user_defined
        """

        name_lower = name.lower()
        length = abs(end - start)

        # -------------------------
        # 1. Constructor / lifecycle
        # -------------------------
        if (
            name == "__init__"
            or name == "constructor"
            or name_lower in JS_LIFECYCLE
        ):
            return "skip", 0

        # -------------------------
        # 2. Simple framework wrappers
        # -------------------------
        framework_bonus = 0
        if name_lower in FRAMEWORK_NAMES:
            framework_bonus = -10


        score = (complexity * 2.5) + (length * 0.5) + (calls * 3) + framework_bonus
        if score < 10:
            return "skip", score
        if score < 15:
            return "wrapper", score
        elif score < 30:
            return "low_priority", score
        elif score < 50:
            return "medium_priority", score
        else:
            return "high_priority", score


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

    def classify_calls(self, chunk_calls: list, imports: list, import_modules: list, chunk_id: str) -> list:
            """
            chunk_calls   = ['faiss.IndexIDMap', 'np.linalg.norm', 'get_logger', 'self.save_index']
            imports       = parsed import list from your schema
            class_methods = ['__init__', 'normalize_embeddings', 'add_embeddings', ...]
            """
            alias_map = {}
            for imp in imports:
                for module_info in import_modules:
                    module = module_info[1]
                    alias = module_info[2]
                    key = alias if alias else module
                    alias_map[key] = {
                        "source": imp[2],
                        "module": module
                    }


            result = set()

            for call in chunk_calls:
                parts = call.split(".")   # faiss.IndexIDMap → faiss
                if len(parts) == 2:
                    root, child = parts[0], parts[1]
                    if root == "self":
                        result.add((
                            chunk_id,
                            "internal_method_call",
                            call,
                            "class",
                            child,
                            None,
                            self.functions.get(child)
                        ))

                else:
                    root, child = parts[0], None

                if root in self.functions:
                    result.add((
                        chunk_id,
                        "internal_method_call",
                        call,
                        "file",
                        root,
                        None,
                        self.functions.get(root)
                    ))

                # aliased or direct external lib
                elif root in alias_map:
                    source = alias_map[root]["source"]
                    result.add((
                        chunk_id,
                        "external_lib_call",
                        call,
                        source,
                        child,
                        source,
                        None
                    ))

                    # if source has your project namespace → cross-file
                    if source.startswith("app.") or '/' in source:
                        result.add((
                            chunk_id,
                            "cross_file_call",
                            call,
                            source,
                            alias_map[root]["module"],
                            None,
                            self.functions.get(alias_map[root]["module"])  # attempt to link to a file-level function if it exists
                        ))

            return list(result)
