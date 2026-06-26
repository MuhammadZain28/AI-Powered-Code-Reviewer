import pytest
import json
from app.utils.chunker import Chunker


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def run_chunker(source: str, language="Python"):
    chunker = Chunker(
        source_code=source,
        language=language,
        file_id="test_file"
    )
    return chunker.chunk_code()


# =========================================================
# Basic Function Extraction
# =========================================================

class TestFunctionExtraction:

    def test_extract_single_function(self):
        source = """
def foo():
    pass
"""

        result = run_chunker(source)

        assert len(result["chunks"]) == 1

        chunk = result["chunks"][0]

        assert chunk.name == "foo"
        assert chunk.class_id is None

    def test_extract_multiple_functions(self):

        source = """
def foo():
    pass

def bar():
    pass

def baz():
    pass
"""

        result = run_chunker(source)

        assert len(result["chunks"]) == 3

        names = {c.name for c in result["chunks"]}

        assert names == {
            "foo",
            "bar",
            "baz"
        }

    def test_empty_file(self):

        result = run_chunker("")

        assert result["chunks"] == []
        assert result["classes"] == []

    def test_comments_only(self):

        source = """
# comment
# another comment
"""

        result = run_chunker(source)

        assert len(result["chunks"]) == 0

    def test_function_code_matches_source(self):

        source = """
def add(a,b):
    return a+b
"""

        result = run_chunker(source)

        chunk = result["chunks"][0]

        assert "return a+b" in chunk.code


# =========================================================
# Class Extraction
# =========================================================

class TestClassExtraction:

    def test_extract_single_class(self):

        source = """
class User:
    pass
"""

        result = run_chunker(source)

        assert len(result["classes"]) == 1

        cls = result["classes"][0]

        assert cls.name == "User"

    def test_extract_class_with_methods(self):

        source = """
class User:

    def login(self):
        pass

    def logout(self):
        pass
"""

        result = run_chunker(source)

        assert len(result["classes"]) == 1
        assert len(result["chunks"]) == 2

        names = {c.name for c in result["chunks"]}

        assert names == {
            "login",
            "logout"
        }

    def test_methods_belong_to_class(self):

        source = """
class Math:

    def add(self):
        pass
"""

        result = run_chunker(source)

        cls = result["classes"][0]
        method = result["chunks"][0]

        assert method.class_id == cls.id

    def test_multiple_classes(self):

        source = """
class A:
    pass

class B:
    pass
"""

        result = run_chunker(source)

        assert len(result["classes"]) == 2

        names = {c.name for c in result["classes"]}

        assert names == {
            "A",
            "B"
        }


# =========================================================
# Constructors
# =========================================================

class TestConstructors:

    def test_python_constructor_extracted(self):

        source = """
class User:

    def __init__(self):
        pass
"""

        result = run_chunker(source)

        names = [c.name for c in result["chunks"]]

        assert "__init__" in names

    def test_constructor_attached_to_class(self):

        source = """
class User:

    def __init__(self):
        self.name = ""
"""

        result = run_chunker(source)

        cls = result["classes"][0]
        ctor = result["chunks"][0]

        assert ctor.class_id == cls.id


# =========================================================
# Decorators
# =========================================================

class TestDecorators:

    def test_decorated_function(self):

        source = """
@property
def name():
    return "John"
"""

        result = run_chunker(source)

        assert len(result["chunks"]) == 1

        assert result["chunks"][0].name == "name"

    def test_multiple_decorators(self):

        source = """
@staticmethod
@cache
def compute():
    return 10
"""

        result = run_chunker(source)

        assert len(result["chunks"]) == 1

        assert result["chunks"][0].name == "compute"


# =========================================================
# Async Functions
# =========================================================

class TestAsyncFunctions:

    def test_async_function(self):

        source = """
async def fetch():
    return 1
"""

        result = run_chunker(source)

        assert len(result["chunks"]) == 1
        assert result["chunks"][0].name == "fetch"


# =========================================================
# Line Numbers
# =========================================================

class TestLineNumbers:

    def test_start_end_lines(self):

        source = """



def foo():
    x = 1
    return x
"""

        result = run_chunker(source)

        chunk = result["chunks"][0]

        assert chunk.start == 4
        assert chunk.end == 6

    def test_multiple_function_lines(self):

        source = """
def a():
    pass


def b():
    pass
"""

        result = run_chunker(source)

        first = result["chunks"][0]
        second = result["chunks"][1]

        assert first.start < second.start


# =========================================================
# Chunk IDs
# =========================================================

class TestChunkIDs:

    def test_chunk_ids_unique(self):

        source = """
def a():
    pass

def b():
    pass

def c():
    pass
"""

        result = run_chunker(source)

        ids = [c.id for c in result["chunks"]]

        assert len(ids) == len(set(ids))

    def test_class_ids_unique(self):

        source = """
class A:
    pass

class B:
    pass
"""

        result = run_chunker(source)

        ids = [c.id for c in result["classes"]]

        assert len(ids) == len(set(ids))


# =========================================================
# Mixed File
# =========================================================

class TestMixedExtraction:

    def test_functions_and_classes(self):

        source = """
def util():
    pass

class User:

    def login(self):
        pass

def helper():
    pass
"""

        result = run_chunker(source)

        assert len(result["classes"]) == 1
        assert len(result["chunks"]) == 3

        names = {c.name for c in result["chunks"]}

        assert names == {
            "util",
            "login",
            "helper"
        }

    def test_global_function_has_no_class(self):

        source = """
class A:

    def x(self):
        pass

def outside():
    pass
"""

        result = run_chunker(source)

        print(json.dumps([c.to_dict() for c in result["chunks"]], indent=4))
        outside = next(
            c for c in result["chunks"]
            if c.name == "outside"
        )

        assert outside.class_id is None

if __name__ == "__main__":
    TestMixedExtraction().test_global_function_has_no_class()