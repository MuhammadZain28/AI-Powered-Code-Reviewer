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
# Cyclomatic Complexity
# =========================================================

class TestComplexity:

    def test_simple_function(self):

        source = """
def foo():
    x = 1
    return x
"""

        result = run_chunker(source)

        assert result["chunks"][0].complexity == 1

    def test_single_call(self):

        source = """
def foo():
    print("hello")
"""

        result = run_chunker(source)

        assert result["chunks"][0].complexity == 2

    def test_two_calls(self):

        source = """
def foo():
    print(1)
    len([])
"""

        result = run_chunker(source)

        assert result["chunks"][0].complexity == 3

    def test_if_statement(self):

        source = """
def foo():

    if True:
        pass
"""

        result = run_chunker(source)

        assert result["chunks"][0].complexity == 2

    def test_if_with_call(self):

        source = """
def foo():

    if check():
        print("ok")
"""

        result = run_chunker(source)

        assert result["chunks"][0].complexity == 4

    def test_for_loop(self):

        source = """
def foo():

    for i in range(10):
        print(i)
"""

        result = run_chunker(source)

        assert result["chunks"][0].complexity == 4

    def test_while_loop(self):

        source = """
def foo():

    while check():
        update()
"""

        result = run_chunker(source)

        assert result["chunks"][0].complexity == 4

    def test_try_except(self):

        source = """
def foo():

    try:
        work()
    except:
        handle()
"""

        result = run_chunker(source)

        assert result["chunks"][0].complexity == 4

    def test_nested_if(self):

        source = """
def foo():

    if a:
        if b:
            print()
"""

        result = run_chunker(source)

        assert result["chunks"][0].complexity == 4

    def test_boolean_expression(self):

        source = """
def foo():

    if a and b:
        pass
"""

        result = run_chunker(source)

        assert result["chunks"][0].complexity == 3

    def test_or_expression(self):

        source = """
def foo():

    if a or b:
        pass
"""

        result = run_chunker(source)

        assert result["chunks"][0].complexity == 3

    def test_multiple_control_flow(self):

        source = """
def foo():

    if a:
        for i in range(5):
            while cond():
                print(i)
"""

        result = run_chunker(source)

        assert result["chunks"][0].complexity == 7


# =========================================================
# Function Scoring
# =========================================================

class TestScoring:

    def test_constructor_score_zero(self):

        chunker = Chunker("", "Python", "file")

        score = chunker.classify_function(
            "__init__",
            1,
            5,
            3,
            2
        )

        assert score == 0

    def test_js_constructor_score_zero(self):

        chunker = Chunker("", "Python", "file")

        score = chunker.classify_function(
            "constructor",
            1,
            10,
            5,
            4
        )

        assert score == 0

    def test_useeffect_score_zero(self):

        chunker = Chunker("", "Python", "file")

        score = chunker.classify_function(
            "useEffect",
            1,
            10,
            8,
            10
        )

        assert score == 0

    def test_framework_bonus(self):

        chunker = Chunker("", "Python", "file")

        score = chunker.classify_function(
            "save",
            1,
            10,
            2,
            1
        )

        normal = chunker.classify_function(
            "calculate",
            1,
            10,
            2,
            1
        )

        assert score < normal

    def test_long_function_scores_higher(self):

        chunker = Chunker("", "Python", "file")

        short = chunker.classify_function(
            "foo",
            1,
            5,
            1,
            0
        )

        long = chunker.classify_function(
            "foo",
            1,
            50,
            1,
            0
        )

        assert long > short

    def test_more_calls_scores_higher(self):

        chunker = Chunker("", "Python", "file")

        low = chunker.classify_function(
            "foo",
            1,
            10,
            2,
            1
        )

        high = chunker.classify_function(
            "foo",
            1,
            10,
            2,
            8
        )

        assert high > low

    def test_more_complexity_scores_higher(self):

        chunker = Chunker("", "Python", "file")

        low = chunker.classify_function(
            "foo",
            1,
            10,
            1,
            2
        )

        high = chunker.classify_function(
            "foo",
            1,
            10,
            8,
            2
        )

        assert high > low

    def test_score_is_float(self):

        chunker = Chunker("", "Python", "file")

        score = chunker.classify_function(
            "foo",
            1,
            5,
            1,
            1
        )

        assert isinstance(score, float)


# =========================================================
# Integration
# =========================================================

class TestComplexityIntegration:

    def test_complex_function(self):

        source = """
def process(data):

    if validate(data):

        for item in data:

            if check(item):

                save(item)

    return len(data)
"""

        result = run_chunker(source)

        chunk = result["chunks"][0]

        assert chunk.complexity == 7

        assert chunk.score > 0

    def test_simple_vs_complex(self):

        simple = """
def foo():
    pass
"""

        complex_fn = """
def foo():

    if a:

        for i in range(5):

            while check():

                update()

    return len([])
"""

        s = run_chunker(simple)["chunks"][0]

        c = run_chunker(complex_fn)["chunks"][0]

        assert c.complexity > s.complexity
        assert c.score > s.score

if __name__ == "__main__":
    TestComplexity().test_boolean_expression()