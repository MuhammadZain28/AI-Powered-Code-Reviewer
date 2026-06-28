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
# Static / Class Attributes
# =========================================================

class TestStaticAttributes:

    def test_single_static_attribute(self):

        source = """
class User:
    name = "John"
"""

        result = run_chunker(source)

        assert len(result["attributes"]) == 1

        attr = result["attributes"][0]

        assert attr.name == "name"
        assert attr.default_value == '"John"'
        assert attr.is_static is True

    def test_multiple_static_attributes(self):

        source = """
class User:
    name = ""
    age = 20
"""

        result = run_chunker(source)

        assert len(result["attributes"]) == 2

    def test_static_function_assignment(self):

        source = """
class User:
    serializer = create_serializer()
"""

        result = run_chunker(source)

        attr = result["attributes"][0]

        assert attr.name == "serializer"
        assert attr.attribute_type == None


# =========================================================
# Typed Attributes
# =========================================================

class TestTypedAttributes:

    def test_typed_attribute(self):

        source = """
class User:
    age: int = 20
"""

        result = run_chunker(source)

        attr = result["attributes"][0]

        assert attr.name == "age"
        assert attr.attribute_type == "int"

    def test_multiple_typed_attributes(self):

        source = """
class User:
    age: int = 20
    name: str = ""
"""

        result = run_chunker(source)

        assert len(result["attributes"]) == 2


# =========================================================
# Instance Attributes
# =========================================================

class TestInstanceAttributes:

    def test_single_instance_attribute(self):

        source = """
class User:

    def __init__(self):
        self.name = ""
"""

        result = run_chunker(source)

        attr = result["attributes"][0]

        assert attr.name == "name"
        assert attr.is_static is False

    def test_multiple_instance_attributes(self):

        source = """
class User:

    def __init__(self):
        self.name = ""
        self.age = 20
"""

        result = run_chunker(source)

        assert len(result["attributes"]) == 2

    def test_function_assignment(self):

        source = """
class User:

    def __init__(self):
        self.db = Database()
"""

        result = run_chunker(source)

        attr = result["attributes"][0]

        assert attr.attribute_type == None

    def test_typed_instance_attribute(self):

        source = """
class User:

    def __init__(self):
        self.age: int = 20
"""

        result = run_chunker(source)

        attr = result["attributes"][0]

        assert attr.name == "age"
        assert attr.attribute_type == "int"


# =========================================================
# Constructors
# =========================================================

class TestConstructorExtraction:

    def test_attributes_only_from_constructor(self):

        source = """
class User:

    def login(self):
        self.name = ""
"""

        result = run_chunker(source)

        assert result["attributes"] == []

    def test_constructor_detected(self):

        source = """
class User:

    def __init__(self):
        self.id = 1
"""

        result = run_chunker(source)

        assert len(result["attributes"]) == 1


    def test_class_attribute_schema(self):

        source = """
    class User:

        version = 1

        def __init__(self):
            self.name = ""
    """

        result = run_chunker(source)

        attrs = result["attributes"]

        assert len(attrs) == 2

        attr = attrs[0]

        assert attr.name == "version"
        assert attr.is_static is True
        assert attr.attribute_type == 'int'
        assert attr.default_value == "1"
# =========================================================
# Inheritance
# =========================================================

class TestInheritance:

    def test_single_parent(self):

        source = """
class Admin(User):
    pass
"""

        result = run_chunker(source)

        cls = result["classes"][0]

        assert cls.inheritances == ["User"]

    def test_multiple_parents(self):

        source = """
class Admin(User, Logger):
    pass
"""

        result = run_chunker(source)

        cls = result["classes"][0]

        assert len(cls.inheritances) == 2

        assert "User" in cls.inheritances
        assert "Logger" in cls.inheritances

    def test_no_parent(self):

        source = """
class User:
    pass
"""

        result = run_chunker(source)

        cls = result["classes"][0]

        assert cls.inheritances == []


# =========================================================
# Attribute Ownership
# =========================================================

class TestAttributeOwnership:

    def test_attribute_has_class_id(self):

        source = """
class User:
    name = ""
"""

        result = run_chunker(source)

        cls = result["classes"][0]
        attr = result["attributes"][0]

        assert attr.class_id == cls.id

    def test_multiple_classes(self):

        source = """
class A:
    x = 1

class B:
    y = 2
"""

        result = run_chunker(source)

        attrs = result["attributes"]

        assert len(attrs) == 2

        assert attrs[0].class_id != attrs[1].class_id


# =========================================================
# Edge Cases
# =========================================================

class TestEdgeCases:

    def test_empty_class(self):

        source = """
class User:
    pass
"""

        result = run_chunker(source)

        assert result["attributes"] == []

    def test_class_with_only_methods(self):

        source = """
class User:

    def login(self):
        pass

    def logout(self):
        pass
"""

        result = run_chunker(source)

        assert result["attributes"] == []

    def test_static_and_instance(self):

        source = """
class User:

    version = 1

    def __init__(self):
        self.name = ""
"""

        result = run_chunker(source)

        assert len(result["attributes"]) == 2

        static = [a for a in result["attributes"] if a.is_static]
        instance = [a for a in result["attributes"] if not a.is_static]

        assert len(static) == 1
        assert len(instance) == 1


# =========================================================
# Integration
# =========================================================

class TestAttributeIntegration:

    def test_complete_class(self):

        source = """
class User(Person):

    version = 1
    active: bool = True

    def __init__(self):
        self.name = ""
        self.age: int = 20
"""

        result = run_chunker(source)

        assert len(result["classes"]) == 1
        assert len(result["attributes"]) == 4

        cls = result["classes"][0]

        assert cls.inheritances == ["Person"]

    def test_class_inheritance_schema(self):

        source = """
    class Admin(User, Logger):
        pass
    """

        result = run_chunker(source)

        cls = result["classes"][0]

        assert len(cls.inheritances) == 2

        assert "User" in cls.inheritances
        assert "Logger" in cls.inheritances
if __name__ == "__main__":
    pytest.main()