# python_filter.py
import sys
import builtins
from abc import ABC, abstractmethod
from dataclasses import dataclass

PYTHON_BUILTINS = frozenset(dir(builtins))  # dynamic — always up to date

PYTHON_STDLIB = frozenset(sys.stdlib_module_names)  # Python 3.10+

PYTHON_STRUCTURE_MANIPULATORS = frozenset({
    "append", "extend", "insert", "remove", "pop", "clear", "index", "count",
    "sort", "reverse", "copy", "update", "get", "setdefault", "keys", "values", "items",
    "add", "discard", "union", "intersection", "difference", "symmetric_difference",
})

class CallFilter(ABC):
    @abstractmethod
    def classify(self, calls: list) -> list:
        """Return the classification. BUILTIN/STDLIB means drop it."""
        ...

class PythonFilter(CallFilter):
    def classify(self, calls: list) -> list:
        result = []
        for call in calls:
            callee_name = call.function_name
            root, child = callee_name.split(".")[0], callee_name.split(".")[-1]
            print(f"Classifying call: {callee_name}, root: {root}, child: {child}")
            if root not in PYTHON_BUILTINS and root not in PYTHON_STDLIB and child not in PYTHON_STRUCTURE_MANIPULATORS:
                print(f"Adding call: {callee_name}")
                result.append(call.to_record())
            print(f"--------------------------------------------------------------------------------------------------------------")
        print(len(result))
        return result

JS_GLOBALS = frozenset({
    "console", "Math", "JSON", "Object", "Array", "String", "Number",
    "Boolean", "Promise", "Error", "Date", "RegExp", "Map", "Set",
    "WeakMap", "WeakSet", "Symbol", "Proxy", "Reflect", "fetch",
    "setTimeout", "setInterval", "clearTimeout", "clearInterval",
    "parseInt", "parseFloat", "isNaN", "isFinite", "encodeURI",
    "decodeURI", "encodeURIComponent", "decodeURIComponent",
    "window", "document", "navigator", "location", "history",
    "localStorage", "sessionStorage", "globalThis", "undefined",
    "null", "true", "false", "Infinity", "NaN",
})

NODE_BUILTINS = frozenset({
    "fs", "path", "os", "http", "https", "net", "url", "util",
    "stream", "buffer", "events", "child_process", "cluster",
    "crypto", "dns", "readline", "zlib", "assert", "module",
    "process", "require", "__dirname", "__filename", "Buffer",
    "global", "queueMicrotask", "setImmediate", "clearImmediate",
})

class JavaScriptFilter(CallFilter):
    def classify(self, calls: list) -> list:
        result = []
        for call in calls:
            callee_name = call.function_name
            root = callee_name.split(".")[0]

            if root not in JS_GLOBALS and root not in NODE_BUILTINS:
                result.append(call.to_record())

        return result  # resolver handles the rest

# cpp_filter.py
CPP_STD_NAMESPACES = frozenset({
    "std", "boost", "__builtin", "__cxx",
})

CPP_BUILTINS = frozenset({
    "sizeof", "alignof", "typeid", "decltype", "static_cast",
    "dynamic_cast", "reinterpret_cast", "const_cast",
    "new", "delete", "throw", "assert",
})

class CppFilter(CallFilter):
    def classify(self, calls: list) -> list:
        result = []
        for call in calls:
            callee_name = call.function_name
            root = callee_name.split("::")[0]  # note: :: not .

            if root not in CPP_STD_NAMESPACES and root not in CPP_BUILTINS:
                result.append(call.to_record())

        return result

# java_filter.py
JAVA_STDLIB_PREFIXES = (
    "java.", "javax.", "sun.", "com.sun.", "jdk.",
    "org.w3c.", "org.xml.", "org.ietf.",
)

JAVA_BUILTINS = frozenset({
    "System", "Object", "String", "Math", "Integer", "Long",
    "Double", "Float", "Boolean", "Character", "Byte", "Short",
    "StringBuilder", "StringBuffer", "Thread", "Runnable",
    "Exception", "RuntimeException", "Error", "Throwable",
    "Comparable", "Iterable", "Cloneable", "Serializable",
    "Class", "ClassLoader", "Enum", "Record",
})

class JavaFilter(CallFilter):
    def classify(self, calls: list) -> list:
        result = []
        for call in calls:
            callee_name = call.function_name
            root = callee_name.split(".")[0]
            if root not in JAVA_BUILTINS and root not in JAVA_STDLIB_PREFIXES:
                result.append(call.to_record())
        return result

_REGISTRY: dict[str, CallFilter] = {
    "python":     PythonFilter(),
    "javascript": JavaScriptFilter(),
    "cpp":        CppFilter(),
    "java":       JavaFilter(),
}

def get_filter(language: str) -> CallFilter:
    return _REGISTRY.get(language.lower())

def classify_call(calls: list, language: str) -> list:
    f = get_filter(language)
    if f is None:
        return None
    return f.classify(calls)