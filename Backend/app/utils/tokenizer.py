from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import uuid
from uuid6 import uuid7


# ═══════════════════════════════════════════════════════════════════════════════
#  TOKEN
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Token:
    type: str
    value: str

    def __repr__(self) -> str:
        return f"Token(type={self.type!r}, value={self.value!r})"

    def is_keyword(self, *values: str) -> bool:
        return self.type == "KEYWORD" and (not values or self.value in values)

    def is_type(self, token_type: str) -> bool:
        return self.type == token_type


# ═══════════════════════════════════════════════════════════════════════════════
#  NORMALIZED STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class NormalizedImport:
    source: str
    type: str
    import_modules: List[dict]
    file_id: Optional[str] = None
    id: uuid.UUID = field(default_factory=lambda: uuid7())

    def to_dict(self) -> dict:
        modules_info = []
        for mod in self.import_modules:
            modules_info.append((
                mod.get("import_id"),
                mod.get("module"),
                mod.get("alias")
            ))
        return (
            self.id,
            self.file_id,
            self.source,
            self.type
        ), modules_info

    def __repr__(self) -> str:
        return (
            f"NormalizedImport(\n"
            f"  source  = {self.source!r}\n"
            f"  type    = {self.type!r}\n"
            f"  modules = {self.import_modules!r}\n"
            f"  file_id = {self.file_id!r}\n"
            f")"
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  KEYWORD SETS  (module-level frozensets — shared, never mutated)
# ═══════════════════════════════════════════════════════════════════════════════

_PY_KEYWORDS   = frozenset({"import", "from", "as", "type"})
_JS_KEYWORDS   = frozenset({"import", "from", "as", "type", "require", "export", "default"})
_JAVA_KEYWORDS = frozenset({"import", "static"})
_C_KEYWORDS    = frozenset({"#include", "#import", "@import"})

_KEYWORDS_MAP: dict[str, frozenset] = {
    "python":     _PY_KEYWORDS,
    "javascript": _JS_KEYWORDS,
    "typescript": _JS_KEYWORDS,
    "java":       _JAVA_KEYWORDS,
    "c":          _C_KEYWORDS,
    "cpp":        _C_KEYWORDS,
}

_SINGLE_CHAR_TOKENS: dict[str, str] = {
    "{": "LBRACE",
    "}": "RBRACE",
    "(": "LPAREN",
    ")": "RPAREN",
    ",": "COMMA",
    ";": "SEMICOLON",
    "*": "STAR",
    "=": "EQUAL",
    ".": "DOT",
}


# ═══════════════════════════════════════════════════════════════════════════════
#  TOKENIZER
# ═══════════════════════════════════════════════════════════════════════════════

class ImportTokenizer:
    def __init__(self, code: str, language: str) -> None:
        self.code     = code.strip()
        self.length   = len(self.code)
        self.pos      = 0
        self.language = language.lower()
        self.keywords = _KEYWORDS_MAP.get(self.language, frozenset())
        self.tokens: List[Token] = []

    # ── public ────────────────────────────────────────────────────────────────

    def tokenize(self) -> List[Token]:
        while self.pos < self.length:
            char = self.code[self.pos]

            if char.isspace():
                self.pos += 1
                continue

            if char in _SINGLE_CHAR_TOKENS:
                self.tokens.append(Token(_SINGLE_CHAR_TOKENS[char], char))
                self.pos += 1
                continue

            if char in ("'", '"'):
                self.tokens.append(self._read_string(char))
                continue

            if char == "<" and self.language in ("c", "cpp"):
                tok = self._read_angle_string()
                if tok:
                    self.tokens.append(tok)
                continue

            if char.isalpha() or char in ("_", "#", "@"):
                self.tokens.append(self._read_identifier())
                continue

            if char.isdigit():
                self.tokens.append(self._read_number())
                continue

            self.pos += 1   # skip unknown char

        return self.tokens

    # ── private readers ───────────────────────────────────────────────────────

    def _read_string(self, quote: str) -> Token:
        self.pos += 1           # skip opening quote
        start   = self.pos
        escaped = False

        while self.pos < self.length:
            char = self.code[self.pos]
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                value = self.code[start : self.pos]
                self.pos += 1
                return Token("STRING", value)
            self.pos += 1

        return Token("STRING", self.code[start:])   # unterminated

    def _read_angle_string(self) -> Optional[Token]:
        close = self.code.find(">", self.pos + 1)
        if close == -1:
            self.pos += 1
            return None
        value    = self.code[self.pos + 1 : close]
        self.pos = close + 1
        return Token("STRING", value)

    def _read_identifier(self) -> Token:
        start = self.pos
        self.pos += 1

        while self.pos < self.length:
            char = self.code[self.pos]
            if char.isalnum() or char == "_":
                self.pos += 1
            else:
                break

        value = self.code[start : self.pos]

        if value.lower() in self.keywords or value in self.keywords:
            return Token("KEYWORD", value)

        return Token("IDENTIFIER", value)

    def _read_number(self) -> Token:
        start = self.pos
        while self.pos < self.length and self.code[self.pos].isdigit():
            self.pos += 1
        return Token("NUMBER", self.code[start : self.pos])


# ═══════════════════════════════════════════════════════════════════════════════
#  TOKEN STREAM  (cursor helper used by all parsers)
# ═══════════════════════════════════════════════════════════════════════════════

class TokenStream:
    def __init__(self, tokens: List[Token]) -> None:
        self._tokens = tokens
        self._pos    = 0

    def peek(self, offset: int = 0) -> Optional[Token]:
        idx = self._pos + offset
        return self._tokens[idx] if 0 <= idx < len(self._tokens) else None

    def consume(self) -> Optional[Token]:
        tok = self.peek()
        if tok:
            self._pos += 1
        return tok

    def consume_if_value(self, value: str) -> bool:
        if self.peek() and self.peek().value == value:
            self._pos += 1
            return True
        return False

    def consume_if_type(self, token_type: str) -> bool:
        if self.peek() and self.peek().type == token_type:
            self._pos += 1
            return True
        return False

    def skip_type(self, *types: str) -> None:
        """Skip consecutive tokens whose type is in `types`."""
        while self.peek() and self.peek().type in types:
            self._pos += 1

    def remaining(self) -> List[Token]:
        return self._tokens[self._pos:]

    def find_value(self, value: str) -> int:
        """Return index of next token with this value, or -1."""
        for i, t in enumerate(self._tokens[self._pos:]):
            if t.value == value:
                return i
        return -1


# ═══════════════════════════════════════════════════════════════════════════════
#  SHARED PARSER UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def _maybe_alias(stream: TokenStream) -> Optional[str]:
    """Consume  'as' IDENTIFIER  if present and return the alias string."""
    if stream.peek() and stream.peek().value == "as":
        stream.consume()                        # eat 'as'
        tok = stream.consume()                  # eat alias name
        return tok.value if tok else None
    return None


def _read_specifier_list(stream: TokenStream):
    """
    Parse a brace-delimited or bare specifier list up to (but not including)
    the 'from' keyword or end of stream.

    Handles:
      React, { useEffect as effect, useState }
      { Button as Btn }
      *
      * as ns
    """
    modules = []
    aliases = []

    while stream.peek() and stream.peek().value not in ("from",):
        tok = stream.consume()

        if tok is None:
            break

        # Skip punctuation that separates specifiers
        if tok.type in ("COMMA", "LBRACE", "RBRACE", "SEMICOLON"):
            continue

        # Star import  →  * as ns  or bare *
        if tok.type == "STAR":
            alias = _maybe_alias(stream)
            modules.append('*')
            if alias:
                aliases.append(alias)
            else:
                aliases.append(None)
            continue

        # Normal identifier (or keyword used as identifier, e.g. 'default')
        if tok.type in ("IDENTIFIER", "KEYWORD"):
            alias = _maybe_alias(stream)
            modules.append(tok.value)
            if alias:
                aliases.append(alias)
            else:
                aliases.append(None)
            continue

    return modules, aliases


# ═══════════════════════════════════════════════════════════════════════════════
#  LANGUAGE PARSERS
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_python(tokens: List[Token], language: str, file_id: str) -> NormalizedImport:

    stream = TokenStream(tokens)
    first  = stream.consume()
    __import__id = uuid7()
    # ── from X import Y [as Z], … ─────────────────────────────────────────────
    if first and first.value == "from":
        # source may be dotted  e.g.  from os.path  →  IDENTIFIER DOT IDENTIFIER
        source_parts: List[str] = []
        while stream.peek() and stream.peek().type in ("IDENTIFIER", "DOT"):
            tok = stream.consume()
            if tok.type == "IDENTIFIER":
                source_parts.append(tok.value)
            # DOT → keep (represents the dot in os.path)
        source = ".".join(source_parts)

        stream.consume_if_value("import")   # eat 'import'

        modules, aliases = _read_specifier_list(stream)
        return NormalizedImport(source=source, type=language, import_modules=[{"module": mod, "alias": alias, "import_id": __import__id} for mod, alias in zip(modules, aliases)], file_id=file_id, id=__import__id)

    # ── import X [as Z] ───────────────────────────────────────────────────────
    mod_tok = stream.consume()
    module  = mod_tok.value if mod_tok else ""
    alias   = _maybe_alias(stream)

    return NormalizedImport(
        source  = module,
        type    = language,
        import_modules=[{"module": module, "alias": alias, "import_id": __import__id}],
        file_id = file_id,
        id = __import__id
    )


def _parse_javascript(tokens: List[Token], language: str, file_id: str) -> NormalizedImport:
    """
    import React, { useEffect as effect } from 'react'
    import * as ns from 'mod'
    import type { Foo } from './foo'
    const fs = require('fs')
    export { Button as Btn } from './Button'
    @import UIKit;
    """
    stream = TokenStream(tokens)
    first  = stream.consume()

    __import__id = uuid7()

    # ── @import UIKit ─────────────────────────────────────────────────────────
    if first and first.value == "@import":
        stream.skip_type("SEMICOLON")
        mod_tok = stream.consume()
        mod     = mod_tok.value if mod_tok else ""
        return NormalizedImport(
            source  = mod,
            type    = language,
            import_modules=[{"module": mod, "alias": None, "import_id": __import__id}],
            file_id = file_id,
            id = __import__id
        )

    # ── const binding = require('source') ─────────────────────────────────────
    # Token shape: IDENTIFIER(const) IDENTIFIER(binding) KEYWORD(require) STRING(source)
    if any(t.value == "require" for t in tokens):
        s = TokenStream(tokens)
        s.consume()                         # skip 'const' / 'let' / 'var'
        binding_tok = s.consume()           # local binding name
        binding     = binding_tok.value if binding_tok else ""
        # skip until require
        while s.peek() and s.peek().value != "require":
            s.consume()
        s.consume()                         # eat 'require'
        source_tok = s.consume()
        source     = source_tok.value if source_tok else ""
        return NormalizedImport(
            source  = source,
            type    = language,
            import_modules=[{"module": source, "alias": binding, "import_id": __import__id} if binding else {"module": source, "alias": None, "import_id": __import__id}],
            file_id = file_id,
            id = __import__id
        )

    # ── import [type] … from 'source'   /   export { … } from 'source' ───────
    # Skip optional 'type' keyword (TS type-only imports)
    stream.consume_if_value("type")

    # Collect specifiers before 'from'
    from_offset = stream.find_value("from")
    if from_offset != -1:
        specifier_tokens = stream.remaining()[:from_offset]
        s = TokenStream(specifier_tokens)
        modules, aliases = _read_specifier_list(s)

        # Advance main stream past specifiers + 'from'
        for _ in range(from_offset + 1):
            stream.consume()
        import_modules = [{"module": mod, "alias": alias, "import_id": __import__id} for mod, alias in zip(modules, aliases)]
        source_tok = stream.consume()
        source     = source_tok.value if source_tok else ""
    else:
        # No 'from' — bare  import 'side-effect-module'
        source_tok = stream.consume()
        source     = source_tok.value if source_tok else ""
        import_modules = [{"module": source, "alias": None, "import_id": __import__id}]
        file_id    = file_id

    return NormalizedImport(source=source, type=language, import_modules=import_modules, file_id=file_id, id=__import__id)


def _parse_java(tokens: List[Token], language: str, file_id: str) -> NormalizedImport:
    """
    import java.util.List;
    import static java.lang.Math.PI;
    """
    stream = TokenStream(tokens)
    stream.consume()                        # eat 'import'
    stream.consume_if_value("static")       # eat optional 'static'

    # Collect dotted path  →  IDENTIFIER (DOT IDENTIFIER)*
    parts: List[str] = []
    __import__id = uuid7()
    while stream.peek() and stream.peek().type in ("IDENTIFIER", "DOT", "SEMICOLON"):
        tok = stream.consume()
        if tok.type == "IDENTIFIER":
            parts.append(tok.value)
        elif tok.type == "SEMICOLON":
            break

    module = parts[-1] if parts else ""
    source = ".".join(parts[:-1]) if len(parts) > 1 else ".".join(parts)
    print(f"DEBUG: parts={parts}, source={source}, module={module}")
    return NormalizedImport(
        source  = source,
        type    = language,
        import_modules=[{"module": module, "alias": None, "import_id": __import__id}] if module else [],
        file_id = file_id,
        id = __import__id
    )


def _parse_c(tokens: List[Token], language: str, file_id: str) -> NormalizedImport:
    """
    #include <iostream>
    #include "myheader.h"
    #import  <Foundation/Foundation.h>
    """
    stream = TokenStream(tokens)
    stream.consume()                        # eat '#include' / '#import'
    source_tok = stream.consume()
    source     = source_tok.value if source_tok else ""
    __import__id = uuid7()

    return NormalizedImport(
        source  = source,
        type    = language,
        import_modules=[{"module": module, "alias": None, "import_id": __import__id} for module in source.split("/")[-1:]],   # module is the filename
        file_id = file_id,
        id = __import__id
    )


# ── Dispatch table (O(1) lookup) ──────────────────────────────────────────────

_PARSERS = {
    "Python":     _parse_python,
    "JavaScript": _parse_javascript,
    "JavaScript (React)": _parse_javascript,
    "TypeScript": _parse_javascript,
    "TypeScript (React)": _parse_javascript,
    "Java":       _parse_java,
    "C":          _parse_c,
    "Cpp":        _parse_c,
}


# ═══════════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def tokenize(code: str, language: str) -> List[Token]:
    """Lex a single import statement."""
    return ImportTokenizer(code, language).tokenize()


def normalize(code: str, language: str, file_id: Optional[str] = None) -> NormalizedImport:

    tokens = ImportTokenizer(code, language).tokenize()
    parser = _PARSERS.get(language)

    if parser is None:
        raise ValueError(f"Unsupported language: {language!r}")

    return parser(tokens, language, file_id).to_dict()


# ═══════════════════════════════════════════════════════════════════════════════
#  SMOKE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import json

    cases = [
        ("import os",                                          "python"),
        ("import os as operating_system",                      "python"),
        ("from collections import defaultdict as dd",          "python"),
        ("from os.path import join, exists",                   "python"),
        ("from typing import List, Optional, Dict",            "python"),
        ("import React, { useEffect as effect } from 'react'", "javascript"),
        ("import * as ns from 'lodash'",                       "javascript"),
        ("import type { Foo } from './types'",                 "typescript"),
        ("const fs = require('fs')",                           "javascript"),
        ("export { Button as Btn } from './Button'",           "javascript"),
        ("#include <iostream>",                                 "c"),
        ('#include "myheader.h"',                              "c"),
        ("@import UIKit;",                                     "javascript"),
        ("import java.util.List;",                             "java"),
        ("import static java.lang.Math.PI;",                   "java"),
    ]

    for code, lang in cases:
        result = normalize(code, lang)
        print(f"INPUT  : {code!r}  [{lang}]")
        print(f"OUTPUT : {json.dumps(result.to_dict(), indent=2)}")
        print()