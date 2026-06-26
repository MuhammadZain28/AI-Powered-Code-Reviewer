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
# Basic Imports
# =========================================================

class TestBasicImports:

    def test_single_import(self):

        source = """
import os
"""

        result = run_chunker(source)

        assert len(result["imports"]) == 1

    def test_multiple_imports(self):

        source = """
import os
import sys
import json
"""

        result = run_chunker(source)

        assert len(result["imports"]) == 3

    def test_no_imports(self):

        source = """
def foo():
    pass
"""

        result = run_chunker(source)

        assert result["imports"] == []

        assert result["import_modules"] == []


# =========================================================
# Alias Imports
# =========================================================

class TestAliasImports:

    def test_numpy_alias(self):

        source = """
import numpy as np
"""

        result = run_chunker(source)

        assert len(result["imports"]) == 1

        assert any(
            "numpy" in str(x)
            for x in result["imports"]
        )

    def test_pandas_alias(self):

        source = """
import pandas as pd
"""

        result = run_chunker(source)

        assert len(result["imports"]) == 1

    def test_multiple_aliases(self):

        source = """
import numpy as np
import pandas as pd
"""

        result = run_chunker(source)

        assert len(result["imports"]) == 2


# =========================================================
# From Imports
# =========================================================

class TestFromImports:

    def test_single_from_import(self):

        source = """
from os import path
"""

        result = run_chunker(source)

        assert len(result["imports"]) == 1

    def test_multiple_from_import(self):

        source = """
from math import sin, cos, tan
"""

        result = run_chunker(source)

        assert len(result["imports"]) == 1

    def test_nested_module(self):

        source = """
from package.utils import helper
"""

        result = run_chunker(source)

        assert len(result["imports"]) == 1


# =========================================================
# Wildcard Imports
# =========================================================

class TestWildcardImports:

    def test_star_import(self):

        source = """
from math import *
"""

        result = run_chunker(source)

        assert len(result["imports"]) == 1


# =========================================================
# Mixed Imports
# =========================================================

class TestMixedImports:

    def test_import_and_from(self):

        source = """
import os
from math import sin
"""

        result = run_chunker(source)

        assert len(result["imports"]) == 2

    def test_complex_file(self):

        source = """
import os
import sys
import numpy as np

from math import sin, cos
from pathlib import Path

def foo():
    pass
"""

        result = run_chunker(source)

        assert len(result["imports"]) == 5


# =========================================================
# Duplicate Imports
# =========================================================

class TestDuplicateImports:

    def test_duplicate_import(self):

        source = """
import os
import os
"""

        result = run_chunker(source)

        assert len(result["imports"]) == 2

    def test_duplicate_alias(self):

        source = """
import numpy as np
import numpy as np
"""

        result = run_chunker(source)

        assert len(result["imports"]) == 2


# =========================================================
# Import Modules
# =========================================================

class TestImportModules:

    def test_import_modules_exists(self):

        source = """
import os
"""

        result = run_chunker(source)

        assert isinstance(
            result["import_modules"],
            list
        )

    def test_import_modules_alias(self):

        source = """
import numpy as np
"""

        result = run_chunker(source)

        assert len(result["import_modules"]) > 0

    def test_from_import_modules(self):

        source = """
from collections import defaultdict
"""

        result = run_chunker(source)

        assert len(result["import_modules"]) > 0

    def test_multiple_modules(self):

        source = """
import os
import numpy as np
import pandas as pd
"""

        result = run_chunker(source)

        assert len(result["import_modules"]) == 3


# =========================================================
# Imports With Functions
# =========================================================

class TestImportsWithFunctions:

    def test_imports_preserved(self):

        source = """
import os

def foo():
    os.getcwd()
"""

        result = run_chunker(source)

        assert len(result["imports"]) == 1
        assert len(result["chunks"]) == 1

    def test_imports_and_classes(self):

        source = """
import os

class User:

    def login(self):
        os.getcwd()
"""

        result = run_chunker(source)

        assert len(result["imports"]) == 1
        assert len(result["classes"]) == 1
        assert len(result["chunks"]) == 1


# =========================================================
# Edge Cases
# =========================================================

class TestEdgeCases:

    def test_import_inside_if(self):

        source = """
if True:
    import os
"""

        result = run_chunker(source)

        # Tree-sitter still parses it as an import statement.
        assert len(result["imports"]) == 1

    def test_import_inside_function(self):

        source = """
def foo():
    import os
"""

        result = run_chunker(source)

        assert len(result["imports"]) == 1

    def test_large_import_block(self):

        source = """
import os
import sys
import json
import math
import pathlib
import typing
import asyncio
import logging
"""

        result = run_chunker(source)

        assert len(result["imports"]) == 8

if __name__ == "__main__":
    pytest.main()