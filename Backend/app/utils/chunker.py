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

    def to_dict(self):
        return {
            "name": self.name,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "inheritances": self.inheritances,
            "hash": self.hash
        }

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

    def to_dict(self):
        return {
            'name': self.name,
            'class_id': str(self.class_id) if self.class_id else None,
            'code': self.code,
            'start': self.start,
            'end': self.end,
            'score': self.score,
            'hash': self.hash,
            'complexity': self.complexity
        }



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

        self.__logger = get_logger("Chunker")

    def get_parser(self):
        parser = Parser()
        if self.language not in LANGUAGES:
            self.__logger.error(f"Unsupported language: {self.language}")
            raise ValueError(f"Unsupported language: {self.language} for file")
        parser.language = LANGUAGES[self.language]
        return parser

    def extract_class(self, node):
        class_id = None
        if node.type in {"class_definition", "class_declaration"}:
            self.class_name = self.get_node_name(node)
            code = self.get_source_segment(node)
            code_hash = self.calculate_hash(code)

            class_id = str(uuid7())

            self.inheritances = self.extract_inheritances(node)

            self.attributes.extend(self.extract_class_attributes(node, class_id))

            self.classes.append(self.build_class(class_id, node, self.class_name, code_hash))

            self.extract_chunks(node, class_id=class_id)

            return

        elif node.type in {"import_statement", "import_from_statement"}:
            import_code = self.get_source_segment(node)

            normalized_import = normalize(import_code, self.language, file_id=self.file_id)
            self.imports.append(normalized_import[0])
            self.imports_modules.extend(normalized_import[1])

        elif node.type in TARGET_NODES:
            self.extract_chunks(node, class_id=class_id)

        for child in node.children:
            self.extract_class(child)



    def extract_chunks(self, node, class_id):
        if node.type in TARGET_NODES:
            name = self.get_node_name(node)
            code = self.get_source_segment(node)

            id = str(uuid7())

            calls, complexity = self.extract_calls(node, id)

            chunk = self.build_chunk(id, node, complexity, calls, class_id)

            self.calls.extend(calls)

            self.chunks.append(chunk)

            return

        for child in node.children:
            self.extract_chunks(child, class_id=class_id)

    def extract_class_attributes(self, class_node, class_id):

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
                            class_id,
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
                            class_id,
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
                if fn_name in {"__init__", "constructor", class_id}:

                    attributes.extend(
                        self.extract_instance_attributes(child, class_id)
                    )

        return attributes

    def extract_instance_attributes(self, init_node, class_id):
        attributes = []

        def walk(node, class_id):
            if node.type in {"expression_statement"}:

                assignment_expr = self.get_source_segment(node)
                left = node.child_by_field_name("left")
                right = node.child_by_field_name("right")

                if (left):
                    attributes.append((
                        class_id,                                             # associate attribute with its class
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
                            class_id,
                            self.get_source_segment(attr_node),
                            self.get_source_segment(type_node) if type_node else None,
                            self.get_source_segment(right) if right else None,
                            False
                        ))

            for child in node.children:
                walk(child, class_id)

        walk(init_node, class_id)

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

    def extract_calls(self, node, caller_id):

        calls = []
        complexity = 1

        COMPLEXITY_NODES = {
            "if_statement",
            "match_statement",
            "case_statement",
            "conditional_expression",
            "switch_statement",
            "for_statement",
            "while_statement",
            "boolean_operator",
            "try_statement",
        }

        CALL_NODES = { "call_expression", "call" }

        def traverse(curr):
            nonlocal complexity

            if curr.type in COMPLEXITY_NODES:
                complexity += 1

            elif curr.type in CALL_NODES:

                complexity += 1

                func_node = curr.child_by_field_name("function")

                if func_node:
                    calls.append({
                        "caller_id": caller_id,
                        "function_name": self.get_source_segment(func_node),
                        "call_line": func_node.start_point[0] + 1,
                    })

            for child in curr.children:
                traverse(child)

        traverse(node)

        return calls, complexity

    def chunk_code(self) -> dict:
        parser = self.get_parser()
        tree = parser.parse(bytes(self.source_code, "utf8"))
        root_node = tree.root_node
        self.extract_class(root_node)

        return {
            "classes": self.classes,
            "imports": self.imports,
            "chunks": self.chunks,
            "calls": self.calls,
            "attributes": self.attributes,
            "import_modules": self.imports_modules
        }

    def build_class(self, id, node, name, code_hash):
        self.__logger.info(f"Building class '{name}' with hash {code_hash}")
        cls = ClassInfo(
            id=id,
            file_id=self.file_id,
            name=name,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            inheritances=self.inheritances,
            hash=code_hash,
        )
        return cls

    def build_chunk(self, id, node, complexity, calls, class_id=None):
        code = self.get_source_segment(node)
        name = self.get_node_name(node)

        start = node.start_point[0]
        end = node.end_point[0]

        score = self.classify_function(name, start, end, complexity, len(calls))

        chunk = FunctionInfo(
            id=id,
            file_id=self.file_id,
            class_id=class_id,
            name=name,
            code=code,
            start=start,
            end=end,
            score=score,
            hash=self.calculate_hash(code),
            complexity=complexity,
        )
        return chunk

    def classify_function(self, name, start, end, complexity, calls=0):

        name_lower = name.lower()
        length = abs(end - start)

        if (
            name == "__init__"
            or name == "constructor"
            or name_lower in JS_LIFECYCLE
        ):
            return 0

        framework_bonus = 0
        if name_lower in FRAMEWORK_NAMES:
            framework_bonus = -10


        score = (complexity * 2.5) + (length * 0.5) + (calls * 3) + framework_bonus

        return score

    def calculate_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def get_node_name(self, node):
        for child in node.children:
            if child.type in {"identifier", "property_identifier", "field_identifier", "type_identifier"}:
                return self.source_code[child.start_byte:child.end_byte]
        return None

    def get_source_segment(self, node):
        return self.source_code[node.start_byte:node.end_byte]

