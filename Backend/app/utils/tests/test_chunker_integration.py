import pytest

from app.utils.chunker import Chunker


# ---------------------------------------------------------
# Helper
# ---------------------------------------------------------

def run_chunker(source: str, language="Python"):
    chunker = Chunker(
        source_code=source,
        language=language,
        file_id="integration_test"
    )
    return chunker.chunk_code()


# =========================================================
# Python Integration
# =========================================================

class TestPythonIntegration:

    def test_complete_python_file(self):

        source = """
import os
from math import sqrt

GLOBAL = 10


class User:

    version = 1

    def __init__(self):
        self.name = ""
        self.age = 20

    def login(self):
        print(self.name)
        os.getcwd()


def helper():

    return sqrt(25)
"""

        result = run_chunker(source)

        assert len(result["classes"]) == 1
        assert len(result["chunks"]) == 3
        assert len(result["imports"]) == 2
        assert len(result["attributes"]) == 3
        assert len(result["calls"]) == 3

    def test_every_chunk_has_hash(self):

        source = """
def foo():
    pass

def bar():
    pass
"""

        result = run_chunker(source)

        for chunk in result["chunks"]:
            assert chunk.hash
            assert chunk.score >= 0
            assert chunk.complexity >= 1

    def test_every_class_has_hash(self):

        source = """
class A:
    pass

class B:
    pass
"""

        result = run_chunker(source)

        for cls in result["classes"]:
            assert cls.hash


# =========================================================
# Relationships
# =========================================================

class TestRelationships:

    def test_methods_reference_class(self):

        source = """
class User:

    def login(self):
        pass

    def logout(self):
        pass
"""

        result = run_chunker(source)

        cls = result["classes"][0]

        for chunk in result["chunks"]:
            assert chunk.class_id == cls.id

    def test_global_function_has_no_class(self):

        source = """
class User:

    def login(self):
        pass


def helper():
    pass
"""

        result = run_chunker(source)

        helper = next(
            c for c in result["chunks"]
            if c.name == "helper"
        )

        assert helper.class_id is None

    def test_calls_reference_chunk(self):

        source = """
def foo():
    print("hello")
"""

        result = run_chunker(source)

        chunk = result["chunks"][0]

        for call in result["calls"]:
            assert call["caller_id"] == chunk.id


# =========================================================
# IDs
# =========================================================

class TestIDs:

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

        ids = [chunk.id for chunk in result["chunks"]]

        assert len(ids) == len(set(ids))

    def test_class_ids_unique(self):

        source = """
class A:
    pass

class B:
    pass
"""

        result = run_chunker(source)

        ids = [cls.id for cls in result["classes"]]

        assert len(ids) == len(set(ids))

    def test_chunk_hashes_unique(self):

        source = """
def a():
    pass

def b():
    pass
"""

        result = run_chunker(source)

        hashes = [chunk.hash for chunk in result["chunks"]]

        assert len(hashes) == len(set(hashes))


# =========================================================
# Empty Files
# =========================================================

class TestEmptyFiles:

    def test_empty_file(self):

        result = run_chunker("")

        assert result["chunks"] == []
        assert result["classes"] == []
        assert result["calls"] == []
        assert result["imports"] == []
        assert result["attributes"] == []

    def test_comments_only(self):

        source = """
# comment

# another comment
"""

        result = run_chunker(source)

        assert len(result["chunks"]) == 0
        assert len(result["classes"]) == 0


# =========================================================
# Multiple Classes
# =========================================================

class TestMultipleClasses:

    def test_multiple_classes(self):

        source = """
class A:

    def a(self):
        pass


class B:

    def b(self):
        pass
"""

        result = run_chunker(source)

        assert len(result["classes"]) == 2
        assert len(result["chunks"]) == 2

        class_ids = {
            cls.id
            for cls in result["classes"]
        }

        for chunk in result["chunks"]:
            assert chunk.class_id in class_ids


# =========================================================
# Realistic Example
# =========================================================

class TestRealisticExample:

    def test_service_class(self):

        source = """
import os
import json


class UserService:

    cache = {}

    def __init__(self):
        self.path = "/tmp"

    def load(self):

        os.listdir(self.path)
        json.dumps({})


def helper():

    print("done")
"""

        result = run_chunker(source)

        assert len(result["imports"]) == 2
        assert len(result["classes"]) == 1
        assert len(result["chunks"]) == 3
        assert len(result["calls"]) == 3
        assert len(result["attributes"]) == 2


# =========================================================
# Output Schema
# =========================================================

class TestOutputSchema:

    def test_expected_keys(self):

        result = run_chunker("")

        expected = {
            "chunks",
            "classes",
            "calls",
            "imports",
            "attributes",
            "import_symbols",
        }

        assert expected.issubset(result.keys())

    def test_chunk_fields(self):

        source = """
def foo():
    pass
"""

        result = run_chunker(source)

        chunk = result["chunks"][0]

        assert hasattr(chunk, "id")
        assert hasattr(chunk, "name")
        assert hasattr(chunk, "hash")
        assert hasattr(chunk, "complexity")
        assert hasattr(chunk, "score")
        assert hasattr(chunk, "code")

    def test_class_fields(self):

        source = """
class User:
    pass
"""

        result = run_chunker(source)

        cls = result["classes"][0]

        assert hasattr(cls, "id")
        assert hasattr(cls, "name")
        assert hasattr(cls, "hash")
        assert hasattr(cls, "inheritances")

if __name__ == "__main__":
    pytest.main()