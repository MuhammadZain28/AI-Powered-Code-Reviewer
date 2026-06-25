import hashlib
import json
from app.utils.tokenizer import normalize
from uuid6 import uuid7
import re
from dataclasses import dataclass, field
from typing import List, Optional
from tree_sitter import Language, Parser
import tree_sitter_cpp
import tree_sitter_java
import tree_sitter_javascript
import tree_sitter_typescript
import tree_sitter_python
from app.utils.logger import get_logger


@dataclass
class ClassInfo:
    id: str
    file_id: str
    name: str
    start_line: int
    end_line: int
    inheritances: List[str] = field(default_factory=list)
    hash: str = ""

@dataclass
class FunctionInfo:
    id: str
    file_id: str
    class_id: Optional[str]
    name: str
    code: str
    start: int
    end: int
    score: float
    hash: str
    complexity: int


@dataclass(frozen=True)
class CallInfo:
    resolved_path: Optional[str] = None
    library: Optional[str] = None
    function_name: Optional[str] = None
    caller_id: Optional[str] = None
    callee_id: Optional[str] = None
    call_type: Optional[str] = None
    call_line: Optional[int] = None

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
    "variable_declarator",
    "class_definition",
    "class_declaration",
    "field_definition",
    "function_expression",
    "constructor",
}

FRAMEWORK_NAMES = {
    "save", "delete", "update", "create", "get", "set",
    "to_json", "from_json", "to_dict", "from_dict", "__new__", "__call__",
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
        self.classes = []
        self.imports = []
        self.imports_modules = []
        self.calls = []
        self.attributes = []
        self.chunks = []
        self.complexity = 1
        self.current_class = None
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

                self.current_class = str(uuid7())

                self.inheritances = self.extract_inheritances(node)
                self.attributes.extend(self.extract_class_attributes(node))
                self.classes.append(self.build_class(self.current_class, node, self.class_name, code_hash))

            else:
                name = self.get_node_name(node)
                code = self.get_source_segment(node)
                code_hash = self.calculate_hash(code)

                id = str(uuid7())

                calls = self.extract_calls(node, name=name)

                chunk = self.build_chunk(id, node, complexity=self.complexity)

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

    def extract_calls(self, node, name=None):

        calls = []

        def traverse(curr):
            if curr.type in {
                "if_statement",
                "match_statement",
                "case_statement",
                "conditional_expression",
                "switch_statement",
                "for_statement",
                "while_statement",
                "or_expression",
                "and_expression",
                "try_statement",
            }:
                self.complexity += 1

            elif curr.type in {"call", "call_expression", "member_expression"}:
                self.complexity += 1
                func_node = curr.child_by_field_name("function")

                if func_node:
                    call_name = self.get_source_segment(func_node)
                    calls.append({"function_name": call_name, "line": func_node.start_point[0] + 1})

            for child in curr.children:
                traverse(child)

        traverse(node)

        return calls

    def chunk_code(self) -> dict:
        parser = self.get_parser()
        self.source_code = self.clean_code(self.source_code)
        tree = parser.parse(bytes(self.source_code, "utf8"))
        root_node = tree.root_node
        self.extract_chunks(root_node)

        return {
            "classes": self.classes,
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

        self.extract_chunks(root_node, chunk_map=chunk_map, class_map=class_map)

        return {
            "classes": self.classes,
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
        cls = ClassInfo(
            id=id,
            file_id=self.file_id,
            name=name,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            docstring=docstring,
            inheritances=self.inheritances,
            hash=code_hash,
        )
        return cls

    def build_chunk(self, id, node, complexity):
        code = self.get_source_segment(node)
        name = self.get_node_name(node)

        start = node.start_point[0] + 1
        end = node.end_point[0] + 1

        score = self.classify_function(name, start, end, complexity, len(self.calls))

        chunk = FunctionInfo(
            id=id,
            file_id=self.file_id,
            class_id=self.current_class,
            name=name,
            code=code,
            start=start,
            end=end,
            score=score,
            hash=self.calculate_hash(code),
            complexity=complexity,
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
            return 0

        # -------------------------
        # 2. Simple framework wrappers
        # -------------------------
        framework_bonus = 0
        if name_lower in FRAMEWORK_NAMES:
            framework_bonus = -10


        score = (complexity * 2.5) + (length * 0.5) + (calls * 3) + framework_bonus
        if score < 10:
            return score
        if score < 15:
            return score
        elif score < 30:
            return score
        elif score < 50:
            return score
        else:
            return score

    def calculate_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def get_node_name(self, node):
        for child in node.children:
            if child.type in {"identifier", "property_identifier", "field_identifier", "type_identifier"}:
                return self.source_code[child.start_byte:child.end_byte]
        return "unknown"

    def get_source_segment(self, node):
        return self.source_code[node.start_byte:node.end_byte]

    def classify_calls(self, chunk_calls: list, imports: list, import_modules: list, chunk_id: str) -> list:
            alias_map = {}
            for imp in imports:
                for module_info in import_modules:
                    module = module_info[1]
                    alias = module_info[2]
                    key = alias if alias else module
                    alias_map[key] = { "source": imp[2], "module": module }

            result = set()

            for call in chunk_calls:
                parts = call['function_name'].split(".")

                if len(parts) == 2:
                    root, child = parts[0], parts[1]

                    if root == "self":
                        ci = CallInfo(
                            function_name=call['function_name'],
                            caller_id=chunk_id,
                            callee_id=self.functions.get(child),
                            call_type="internal_method_call",
                            resolved_path=child,
                            library=None
                        )
                        result.add(ci)

                    elif root in alias_map:
                        source = alias_map[root]["source"]

                        if child in self.functions:
                            ci = CallInfo(
                                function_name=call['function_name'],
                                caller_id=chunk_id,
                                callee_id=self.functions.get(child),
                                call_type="cross_file_call",
                                resolved_path=child,
                                library=source,
                                call_line=call['line']
                            )
                            result.add(ci)

                        else:
                            ci = CallInfo(
                                function_name=call['function_name'],
                                caller_id=chunk_id,
                                callee_id=None,
                                call_type="external_lib_call",
                                resolved_path=child,
                                library=source,
                                call_line=call['line']
                            )
                            result.add(ci)

                else:
                    root, child = parts[0], None

                    if root in self.functions:
                        ci = CallInfo(
                            function_name=call['function_name'],
                            caller_id=chunk_id,
                            callee_id=self.functions.get(root),
                            call_type="cross_file_call",
                            resolved_path=root,
                            library=None,
                            call_line=call['line']
                        )
                        result.add(ci)

                    elif root in alias_map:
                        source = alias_map[root]["source"]
                        ci = CallInfo(
                            function_name=call['function_name'],
                            caller_id=chunk_id,
                            callee_id=None,
                            call_type="external_lib_call",
                            resolved_path=child,
                            library=source,
                            call_line=call['line']
                        )
                        result.add(ci)

            return list(result)
