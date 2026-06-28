import pytest

from app.utils.chunker import Chunker


# ---------------------------------------------------------
# Helper
# ---------------------------------------------------------

def run_chunker(source: str):
    chunker = Chunker(
        source_code=source,
        language="Python",
        file_id="test_file"
    )
    return chunker.chunk_code()


# =========================================================
# Basic Call Extraction
# =========================================================

class TestBasicCalls:

    def test_no_calls(self):

        source = """
def foo():
    x = 1
    return x
"""

        result = run_chunker(source)

        assert result["calls"] == []

    def test_single_call(self):

        source = """
def foo():
    print("hello")
"""

        result = run_chunker(source)

        assert len(result["calls"]) == 1

        call = result["calls"][0]

        assert call["function_name"] == "print"

    def test_multiple_calls(self):

        source = """
def foo():
    print(1)
    len([1,2])
    sum([1,2])
"""

        result = run_chunker(source)

        names = {
            c["function_name"]
            for c in result["calls"]
        }

        assert names == {
            "print",
            "len",
            "sum"
        }


# =========================================================
# Method Calls
# =========================================================

class TestMethodCalls:

    def test_self_method_call(self):

        source = """
class User:

    def login(self):
        self.validate()
"""

        result = run_chunker(source)

        assert len(result["calls"]) == 1

        assert result["calls"][0]["function_name"] == "self.validate"

    def test_cls_method_call(self):

        source = """
class User:

    @classmethod
    def create(cls):
        cls.build()
"""

        result = run_chunker(source)

        assert len(result["calls"]) == 1

        assert result["calls"][0]["function_name"] == "cls.build"

    def test_object_method_call(self):

        source = """
def foo():
    user.login()
"""

        result = run_chunker(source)

        assert result["calls"][0]["function_name"] == "user.login"


# =========================================================
# Library Calls
# =========================================================

class TestLibraryCalls:

    def test_module_function(self):

        source = """
import os

def foo():
    os.getcwd()
"""

        result = run_chunker(source)

        assert result["calls"][0]["function_name"] == "os.getcwd"

    def test_numpy_call(self):

        source = """
import numpy as np

def foo():
    np.array([1,2,3])
"""

        result = run_chunker(source)

        assert result["calls"][0]["function_name"] == "np.array"

    def test_pandas_call(self):

        source = """
import pandas as pd

def foo():
    pd.read_csv("file.csv")
"""

        result = run_chunker(source)

        assert result["calls"][0]["function_name"] == "pd.read_csv"


# =========================================================
# Nested Expressions
# =========================================================

class TestNestedCalls:

    def test_call_inside_return(self):

        source = """
def foo():
    return str(len([1,2]))
"""

        result = run_chunker(source)

        names = {
            c["function_name"]
            for c in result["calls"]
        }

        assert names == {
            "str",
            "len"
        }

    def test_nested_function_calls(self):

        source = """
def foo():
    print(max(abs(-4),5))
"""

        result = run_chunker(source)

        names = {
            c["function_name"]
            for c in result["calls"]
        }

        assert names == {
            "print",
            "max",
            "abs"
        }

    def test_call_in_assignment(self):

        source = """
def foo():
    value = compute()
"""

        result = run_chunker(source)

        assert result["calls"][0]["function_name"] == "compute"


# =========================================================
# Multiple Functions
# =========================================================

class TestMultipleFunctions:

    def test_calls_from_multiple_functions(self):

        source = """
def a():
    print(1)

def b():
    len([1])

def c():
    sum([1])
"""

        result = run_chunker(source)

        names = [
            c["function_name"]
            for c in result["calls"]
        ]

        assert names == [
            "print",
            "len",
            "sum"
        ]


# =========================================================
# Duplicate Calls
# =========================================================

class TestDuplicateCalls:

    def test_same_call_multiple_times(self):

        source = """
def foo():
    print(1)
    print(2)
    print(3)
"""

        result = run_chunker(source)

        assert len(result["calls"]) == 3

        assert all(
            c["function_name"] == "print"
            for c in result["calls"]
        )


# =========================================================
# Recursive Calls
# =========================================================

class TestRecursiveCalls:

    def test_recursive_function(self):

        source = """
def factorial(n):

    if n == 0:
        return 1

    return n * factorial(n-1)
"""

        result = run_chunker(source)

        assert len(result["calls"]) == 1

        assert result["calls"][0]["function_name"] == "factorial"


# =========================================================
# Chained Calls
# =========================================================

class TestChainedCalls:

    def test_chain(self):

        source = """
def foo():
    obj.get().save()
"""

        result = run_chunker(source)

        assert len(result["calls"]) >= 1

    def test_long_chain(self):

        source = """
def foo():
    db.session.query(User).filter().first()
"""

        result = run_chunker(source)

        assert len(result["calls"]) >= 1


# =========================================================
# Call Line Numbers
# =========================================================

class TestCallLines:

    def test_single_call_line(self):

        source = """



def foo():
    print(1)
"""

        result = run_chunker(source)

        call = result["calls"][0]

        assert call["call_line"] == 5

    def test_multiple_line_numbers(self):

        source = """
def foo():

    print()

    len([])

    sum([])
"""

        result = run_chunker(source)

        lines = [
            c["call_line"]
            for c in result["calls"]
        ]

        assert lines == sorted(lines)


# =========================================================
# Calls Inside Control Flow
# =========================================================

class TestControlFlowCalls:

    def test_if_call(self):

        source = """
def foo():

    if True:
        print(1)
"""

        result = run_chunker(source)

        assert len(result["calls"]) == 1

    def test_for_call(self):

        source = """
def foo():

    for i in range(10):
        print(i)
"""

        result = run_chunker(source)

        names = {
            c["function_name"]
            for c in result["calls"]
        }

        assert names == {
            "range",
            "print"
        }

    def test_while_call(self):

        source = """
def foo():

    while check():
        update()
"""

        result = run_chunker(source)

        names = {
            c["function_name"]
            for c in result["calls"]
        }

        assert names == {
            "check",
            "update"
        }


# =========================================================
# Comprehensions
# =========================================================

class TestComprehensions:

    def test_list_comprehension(self):

        source = """
def foo():
    return [str(x) for x in values()]
"""

        result = run_chunker(source)

        names = {
            c["function_name"]
            for c in result["calls"]
        }

        assert names == {
            "str",
            "values"
        }


# =========================================================
# Integration
# =========================================================

class TestIntegration:

    def test_complete_file(self):

        source = """
import os

class User:

    def login(self):
        self.validate()
        print("login")

def helper():
    os.getcwd()
"""

        result = run_chunker(source)

        assert len(result["chunks"]) == 2
        assert len(result["calls"]) == 3

        names = {
            c["function_name"]
            for c in result["calls"]
        }

        assert names == {
            "self.validate",
            "print",
            "os.getcwd"
        }

    def test_call_graph_schema(self):

        source = """
    def foo():
        print("Hello")
    """

        result = run_chunker(source)

        assert len(result["calls"]) == 1

        call = result["calls"][0]

        assert call["caller_id"] is not None
        assert call["function_name"] == "print"
        assert call["call_line"] > 0

if __name__ == "__main__":
    pytest.main([__file__])