import hashlib
import json
from app.utils.tokenizer import normalize
from uuid6 import uuid7
from dataclasses import dataclass, field
from typing import List, Optional
from tree_sitter import Language, Parser
import tree_sitter_cpp
import tree_sitter_java
import tree_sitter_javascript
import tree_sitter_typescript
import tree_sitter_python
from app.utils.logger import get_logger
import re
from app.utils.call_filter import classify_call


@dataclass(frozen=True)
class ClassInfo:
    id: str
    file_id: str
    name: str
    start: int
    end: int
    inheritances: List[str] = field(default_factory=list)
    hash: str = ""

    def to_dict(self):
        return {
            "name": self.name,
            "start": self.start,
            "end": self.end,
            "inheritances": self.inheritances,
            "hash": self.hash,
        }

    def to_record(self):
        return (
            self.id,
            self.file_id,
            self.name,
            self.start,
            self.end,
            self.hash,
            self.inheritances
        )


@dataclass(frozen=True)
class FunctionInfo:
    id: str
    file_id: str
    class_id: Optional[str]
    name: str
    code: str
    start: int
    end: int
    signature: str
    score: float
    hash: str
    complexity: int

    def to_dict(self):
        return {
            'name':       self.name,
            'class_id':   str(self.class_id) if self.class_id else None,
            'code':       self.code,
            'start':      self.start,
            'end':        self.end,
            'score':      self.score,
            'hash':       self.hash,
            'complexity': self.complexity,
            'signature':  self.signature,
        }

    def to_record(self):
        return (
            self.id,
            self.file_id,
            self.class_id,
            self.name,
            self.start,
            self.end,
            self.code,
            self.signature,
            self.complexity,
            self.score,
            self.hash,
        )


@dataclass(frozen=True)
class ClassAttributeInfo:
    class_id: str
    name: str
    attribute_type: Optional[str]
    default_value: Optional[str]
    line_number: int
    is_static: bool

    def to_record(self):
        return (
            self.class_id,
            self.name,
            self.attribute_type,
            self.default_value,
            self.line_number,
            self.is_static,
        )


@dataclass(frozen=True)
class CallInfo:
    caller_id: str
    function_name: str
    line_number: int

    def to_record(self):
        return (
            self.caller_id,
            self.function_name,
            self.line_number
        )

LANGUAGES = {
    "Python":             Language(tree_sitter_python.language()),
    "JavaScript":         Language(tree_sitter_javascript.language()),
    "JavaScript (React)": Language(tree_sitter_javascript.language()),
    "C++":                Language(tree_sitter_cpp.language()),
    "Java":               Language(tree_sitter_java.language()),
    "TypeScript":         Language(tree_sitter_typescript.language_typescript()),
    "TypeScript (React)": Language(tree_sitter_typescript.language_tsx()),
}

TARGET_NODES = {
    "function_definition",
    "method_definition",
    "function_declaration",
    "function_expression"
}

FRAMEWORK_NAMES = {
    "save", "delete", "update", "create", "get", "set",
    "to_json", "from_json", "to_dict", "from_dict", "__new__", "__call__",
    "render", "serialize", "deserialize", "__repr__", "__str__", "__eq__", "__hash__",
}

JS_LIFECYCLE = {
    "constructor", "componentdidmount", "componentdidupdate",
    "componentwillmount", "useeffect",
}


class Chunker:
    def __init__(self, source_code: str, language: str, file_id: str):
        self.source_code     = source_code
        self.language        = language
        self.file_id         = file_id
        self.classes         = []
        self.imports         = []
        self.import_symbols  = []
        self.calls           = []
        self.attributes      = []
        self.chunks          = []

        self.class_name      = None
        self.inheritances    = []

        self.functions       = {}

        self.__logger        = get_logger("Chunker")

    def get_parser(self):
        parser = Parser()
        if self.language not in LANGUAGES:
            raise ValueError(f"Unsupported language: {self.language} for file")

        parser.language = LANGUAGES[self.language]
        return parser

    def extract_class(self, node):
        if node.type in {"class_definition", "class_declaration"}:

            self.class_name = self.get_node_name(node)
            code            = self.get_source_segment(node)
            code_hash       = self.calculate_hash(code)
            class_id        = str(uuid7())

            inheritances      = self.extract_inheritances(node)
            self.inheritances = inheritances

            self.attributes.extend(self.extract_class_attributes(node, class_id))
            self.classes.append(
                self.build_class(class_id, node, self.class_name, code_hash, inheritances)
            )

            self.extract_chunks(node, class_id=class_id)

            return

        elif node.type in {"import_statement", "import_from_statement"}:
            import_code       = self.get_source_segment(node)
            normalized_import = normalize(import_code, self.language, file_id=self.file_id)

            self.imports.append(normalized_import[0])
            self.import_symbols.extend(normalized_import[1])

        elif node.type in TARGET_NODES:
            self.extract_chunks(node, class_id=None)

        for child in node.children:
            self.extract_class(child)

    def extract_chunks(self, node, class_id):
        if node.type in TARGET_NODES:
            id   = str(uuid7())

            calls, complexity = self.extract_calls(node, id)
            chunk = self.build_chunk(id, node, complexity, calls, class_id)

            self.calls.extend(calls)
            self.chunks.append(chunk)
            return

        for child in node.children:
            self.extract_chunks(child, class_id=class_id)

    def _infer_type_from_node(self, node):
        """Infer a best-effort type string from an assignment's right-hand AST node."""
        if node is None:
            return None
        type_map = {
            "integer":             "int",
            "float":               "float",
            "string":              "str",
            "concatenated_string": "str",
            "true":                "bool",
            "false":               "bool",
            "none":                "None",
            "list":                "list",
            "dictionary":          "dict",
            "set":                 "set",
            "tuple":               "tuple",
        }
        return type_map.get(node.type, None)

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
                    left  = expr.child_by_field_name("left")
                    right = expr.child_by_field_name("right")

                    if left:
                        attributes.append(ClassAttributeInfo(
                            class_id=class_id,
                            name=self.get_source_segment(left),
                            attribute_type=self._infer_type_from_node(right),
                            default_value=self.get_source_segment(right) if right else None,
                            line_number=left.start_point[0] + 1,
                            is_static=True,
                        ).to_record())

                elif expr and expr.type == "typed_assignment":
                    left      = expr.child_by_field_name("left")
                    right     = expr.child_by_field_name("right")
                    type_node = expr.child_by_field_name("type")

                    if left:
                        attributes.append(ClassAttributeInfo(
                            class_id=class_id,
                            name=self.get_source_segment(left),
                            attribute_type=self.get_source_segment(type_node) if type_node else None,
                            default_value=self.get_source_segment(right) if right else None,
                            line_number=left.start_point[0] + 1,
                            is_static=True,
                        ).to_record())

            # =========================
            # INSTANCE ATTRIBUTES
            # =========================

            if child.type in {
                "function_definition", "method_definition",
                "function_declaration", "function_expression", "constructor",
            }:
                fn_name = self.get_node_name(child)
                if fn_name in {"__init__", "constructor", self.class_name}:
                    attributes.extend(
                        self.extract_instance_attributes(child, class_id)
                    )

        return attributes

    def extract_instance_attributes(self, init_node, class_id):
        attributes = []

        def walk(node, class_id):
            if node.type == "expression_statement":
                expr = node.children[0] if node.children else None

                if expr and expr.type == "assignment":
                    left  = expr.child_by_field_name("left")
                    right = expr.child_by_field_name("right")

                    if left and left.type == "attribute":
                        object_node = left.child_by_field_name("object")
                        attr_node   = left.child_by_field_name("attribute")

                        if (
                            object_node and attr_node and
                            self.get_source_segment(object_node) in {"self", "cls"}
                        ):
                            attributes.append(ClassAttributeInfo(
                                class_id=class_id,
                                name=self.get_source_segment(attr_node),
                                attribute_type=self._infer_type_from_node(right),
                                default_value=self.get_source_segment(right) if right else None,
                                line_number=left.start_point[0] + 1,
                                is_static=False,
                            ).to_record())

            elif node.type == "typed_assignment":
                left      = node.child_by_field_name("left")
                right     = node.child_by_field_name("right")
                type_node = node.child_by_field_name("type")

                if left and left.type == "attribute":
                    object_node = left.child_by_field_name("object")
                    attr_node   = left.child_by_field_name("attribute")

                    if (
                        object_node and attr_node and
                        self.get_source_segment(object_node) in {"self", "cls"}
                    ):
                        attributes.append(ClassAttributeInfo(
                            class_id=class_id,
                            name=self.get_source_segment(attr_node),
                            attribute_type=self.get_source_segment(type_node) if type_node else None,
                            default_value=self.get_source_segment(right) if right else None,
                            line_number=left.start_point[0] + 1,
                            is_static=False,
                        ).to_record())

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
                inheritances.append(self.get_source_segment(child))
        return inheritances

    def extract_calls(self, node, caller_id):
        calls      = set()
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

        def traverse(curr):
            nonlocal complexity

            if curr.type in COMPLEXITY_NODES:
                complexity += 1

            elif curr.type == "call":

                func_node = curr.child_by_field_name("function")
                if func_node:
                    calls.add(CallInfo(
                        caller_id=caller_id,
                        function_name=self.get_source_segment(func_node),
                        line_number=func_node.start_point[0] + 1
                    ))

            for child in curr.children:
                traverse(child)

        traverse(node)
        return list(calls), complexity

    def chunk_code(self) -> dict:
        parser    = self.get_parser()
        self.source_code = self.clean_code(self.source_code)

        tree      = parser.parse(bytes(self.source_code, "utf8"))
        root_node = tree.root_node
        self.extract_class(root_node)

        return {
            "classes":        self.classes,
            "imports":        self.imports,
            "chunks":         self.chunks,
            "calls":          classify_call(self.calls, self.language),
            "attributes":     self.attributes,
            "import_symbols": self.import_symbols,
        }

    def clean_code(self, code: str) -> str:
        code = re.sub(r"^\s*#.*$\n?", "", code, flags=re.MULTILINE)

        code = re.sub(r"^\s*//.*$\n?", "", code, flags=re.MULTILINE)

        code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)

        code = re.sub(r"[ \t]+$", "", code, flags=re.MULTILINE)

        code = re.sub(r"\n{3,}", "\n\n", code)

        return code.strip()

    def build_class(self, id, node, name, code_hash, inheritances):

        return ClassInfo(
            id=id,
            file_id=self.file_id,
            name=name,
            start=node.start_point[0] + 1,
            end=node.end_point[0] + 1,
            inheritances=inheritances,
            hash=code_hash,
        ).to_record()

    def get_function_signature(self, node, name=None) -> str:

        params_node = node.child_by_field_name("parameters")
        params_str  = self._extract_params(params_node) if params_node else "()"

        return_node = node.child_by_field_name("return_type")
        if return_node:
            return_text = self.get_source_segment(return_node).lstrip("->").strip()
            return_str  = f" -> {return_text}"
        else:
            return_str = ""

        return f"{name}{params_str}{return_str}"

    def _extract_params(self, params_node) -> str:
        params = []
        for child in params_node.children:
            if child.type in {"(", ")", ","}:
                continue
            elif child.type == "identifier":
                params.append(self.get_source_segment(child))
            elif child.type == "typed_parameter":
                p_name = child.child_by_field_name("name")
                p_type = child.child_by_field_name("type")
                name_s = self.get_source_segment(p_name) if p_name else ""
                type_s = self.get_source_segment(p_type) if p_type else ""
                params.append(f"{name_s}: {type_s}" if type_s else name_s)
            elif child.type == "default_parameter":
                p_name = child.child_by_field_name("name")
                p_def  = child.child_by_field_name("value")
                params.append(
                    f"{self.get_source_segment(p_name)}="
                    f"{self.get_source_segment(p_def) if p_def else ''}"
                )
            elif child.type == "typed_default_parameter":
                p_name = child.child_by_field_name("name")
                p_type = child.child_by_field_name("type")
                p_def  = child.child_by_field_name("value")
                params.append(
                    f"{self.get_source_segment(p_name)}: "
                    f"{self.get_source_segment(p_type) if p_type else ''} = "
                    f"{self.get_source_segment(p_def) if p_def else ''}"
                )
            elif child.type in {"list_splat_pattern", "dictionary_splat_pattern"}:
                params.append(self.get_source_segment(child))
        return "(" + ", ".join(params) + ")"

    def build_chunk(self, id, node, complexity, calls, class_id=None):
        start = node.start_point[0] + 1
        end   = node.end_point[0] + 1

        name = self.get_node_name(node)
        code = self.get_source_segment(node)

        signature = self.get_function_signature(node, name)

        score = self.classify_function(name, start, end, complexity, len(calls))

        self.functions[name] = id

        return FunctionInfo(
            id=id,
            file_id=self.file_id,
            class_id=class_id,
            name=name,
            code=code,
            start=start,
            end=end,
            signature=signature,
            score=score,
            hash=self.calculate_hash(code),
            complexity=complexity,
        ).to_record()

    def classify_function(self, name, start, end, complexity, calls=0):
        name_lower = name.lower() if name else ""
        length     = abs(end - start)

        if name in {"__init__", "constructor"} or name_lower in JS_LIFECYCLE:
            return 0

        framework_bonus = -10 if name_lower in FRAMEWORK_NAMES else 0
        return (complexity * 2.5) + (length * 0.5) + (calls * 3) + framework_bonus

    def calculate_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def get_node_name(self, node):

        name_node = node.child_by_field_name("name")

        if name_node:
            return self.get_source_segment(name_node)

        return None

    def get_source_segment(self, node):
        return self.source_code[node.start_byte:node.end_byte]


if __name__ == "__main__":

    calls = [
        CallInfo(caller_id="id1", function_name="os.path.join", line_number=10),
        CallInfo(caller_id="id2", function_name="sys.exit", line_number=20),
        CallInfo(caller_id="id1", function_name="self.foo", line_number=30),
        CallInfo(caller_id="id2", function_name="self.bar", line_number=40),
        CallInfo(caller_id="id1", function_name="self.baz", line_number=50),
        CallInfo(caller_id="id2", function_name="print", line_number=60),
    ]

    filtered_calls = classify_call(calls, "python")
    for call in filtered_calls:
        print(call.to_record())