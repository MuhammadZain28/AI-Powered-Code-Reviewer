from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from app.call_graph_resolver.models.call_resolution import (
    CallKind,
    ResolutionStatus,
)
from app.call_graph_resolver.resolvers.internal_resolver import InternalCallResolver
from app.call_graph_resolver.resolvers.cross_resolver import CrossFileCallResolver
from app.call_graph_resolver.resolvers.external_resolver import ExternalLibraryResolver
from app.call_graph_resolver import CallGraphResolver


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures / shared test data
# ─────────────────────────────────────────────────────────────────────────────

FILE_A = "file_id_A"
FILE_B = "file_id_B"

CHUNK_VALIDATE    = {"id": "chunk_validate",    "name": "validate",    "file_id": FILE_A, "start": 10, "end": 20, "class_id": None}
CHUNK_PROCESS     = {"id": "chunk_process",     "name": "process",     "file_id": FILE_A, "start": 22, "end": 40, "class_id": None}
CHUNK_SAVE        = {"id": "chunk_save",        "name": "save",        "file_id": FILE_A, "start": 42, "end": 55, "class_id": "cls_model"}
CHUNK_LOAD        = {"id": "chunk_load",        "name": "load",        "file_id": FILE_A, "start": 57, "end": 70, "class_id": "cls_model"}
CHUNK_GET_USER_B  = {"id": "chunk_get_user_b",  "name": "get_user",    "file_id": FILE_B, "start": 5,  "end": 15, "class_id": None}

FILE_A_CHUNKS = [CHUNK_VALIDATE, CHUNK_PROCESS, CHUNK_SAVE, CHUNK_LOAD]

GLOBAL_INDEX: dict = {
    (FILE_A, "validate"):  ["chunk_validate"],
    (FILE_A, "process"):   ["chunk_process"],
    (FILE_A, "save"):      ["chunk_save"],
    (FILE_A, "load"):      ["chunk_load"],
    (FILE_B, "get_user"):  ["chunk_get_user_b"],
}


# ─────────────────────────────────────────────────────────────────────────────
# InternalCallResolver
# ─────────────────────────────────────────────────────────────────────────────

class TestInternalCallResolver:

    def _make_resolver(self, raw_calls, import_names=None):
        return InternalCallResolver(
            chunks=FILE_A_CHUNKS,
            raw_calls=raw_calls,
            import_names=import_names or set(),
        )

    # --- happy path ---

    def test_bare_function_resolves(self):
        raw = [{"caller_id": "chunk_process", "function_name": "validate", "call_line": 25}]
        resolver = self._make_resolver(raw)
        resolved, unmatched = resolver.resolve()

        assert len(resolved) == 1
        assert len(unmatched) == 0
        r = resolved[0]
        assert r.callee_id == "chunk_validate"
        assert r.call_kind == CallKind.INTERNAL
        assert r.status == ResolutionStatus.RESOLVED
        assert r.call_line == 25

    def test_dotted_method_call_resolves(self):
        raw = [{"caller_id": "chunk_save", "function_name": "self.load", "call_line": 50}]
        resolver = self._make_resolver(raw)
        resolved, unmatched = resolver.resolve()

        # "load" exists in the same file — should resolve internally
        assert len(resolved) == 1
        assert resolved[0].callee_id == "chunk_load"
        assert resolved[0].call_kind == CallKind.INTERNAL

    def test_imported_name_not_resolved_internally(self):
        """A name that appears in import_names must not be matched internally."""
        raw = [{"caller_id": "chunk_process", "function_name": "validate", "call_line": 30}]
        resolver = self._make_resolver(raw, import_names={"validate"})
        resolved, unmatched = resolver.resolve()

        # "validate" is an import — must fall through
        assert len(resolved) == 0
        assert len(unmatched) == 1

    def test_unknown_function_falls_through(self):
        raw = [{"caller_id": "chunk_process", "function_name": "non_existent", "call_line": 35}]
        resolver = self._make_resolver(raw)
        resolved, unmatched = resolver.resolve()

        assert len(resolved) == 0
        assert len(unmatched) == 1

    def test_multiple_calls_mixed_outcome(self):
        raw = [
            {"caller_id": "chunk_process", "function_name": "validate",    "call_line": 25},
            {"caller_id": "chunk_process", "function_name": "np.array",    "call_line": 26},
            {"caller_id": "chunk_process", "function_name": "process",     "call_line": 27},
        ]
        resolver = self._make_resolver(raw, import_names={"np"})
        resolved, unmatched = resolver.resolve()

        assert len(resolved) == 2     # validate + process
        assert len(unmatched) == 1    # np.array (import)
        names = {r.function_name for r in resolved}
        assert names == {"validate", "process"}

    def test_ambiguous_same_name_in_file(self):
        """Two chunks with the same name in the same file → AMBIGUOUS."""
        dup_chunk = {"id": "chunk_validate_dup", "name": "validate", "file_id": FILE_A,
                     "start": 80, "end": 90, "class_id": "cls_other"}
        resolver = InternalCallResolver(
            chunks=FILE_A_CHUNKS + [dup_chunk],
            raw_calls=[{"caller_id": "chunk_process", "function_name": "validate", "call_line": 25}],
            import_names=set(),
        )
        resolved, unmatched = resolver.resolve()
        assert len(resolved) == 1
        assert resolved[0].status == ResolutionStatus.AMBIGUOUS
        assert len(resolved[0].candidates) == 2

    def test_empty_raw_calls(self):
        resolver = self._make_resolver([])
        resolved, unmatched = resolver.resolve()
        assert resolved == []
        assert unmatched == []

    def test_import_names_must_be_set(self):
        with pytest.raises(TypeError):
            InternalCallResolver(
                chunks=FILE_A_CHUNKS,
                raw_calls=[],
                import_names=["np"],   # list, not set
            )


# ─────────────────────────────────────────────────────────────────────────────
# CrossFileCallResolver
# ─────────────────────────────────────────────────────────────────────────────

class TestCrossFileCallResolver:

    def _make_resolver(self, raw_calls, import_map=None, external_lib_names=None):
        return CrossFileCallResolver(
            raw_calls=raw_calls,
            import_map=import_map or {"get_user": FILE_B, "UserService": FILE_B},
            global_chunk_index=GLOBAL_INDEX,
            external_lib_names=external_lib_names or set(),
        )

    # --- happy path ---

    def test_direct_import_resolves(self):
        """from services.user import get_user → get_user() resolves to FILE_B."""
        raw = [{"caller_id": "chunk_process", "function_name": "get_user", "call_line": 30}]
        resolver = self._make_resolver(raw, import_map={"get_user": FILE_B})
        cross, unmatched = resolver.resolve()

        assert len(cross) == 1
        assert len(unmatched) == 0
        r = cross[0]
        assert r.callee_id == "chunk_get_user_b"
        assert r.call_kind == CallKind.CROSS_FILE
        assert r.status == ResolutionStatus.RESOLVED
        assert r.resolved_path == FILE_B

    def test_qualified_import_resolves(self):
        """user_service.get_user() where user_service → FILE_B."""
        raw = [{"caller_id": "chunk_process", "function_name": "UserService.get_user", "call_line": 35}]
        resolver = self._make_resolver(raw, import_map={"UserService": FILE_B})
        cross, unmatched = resolver.resolve()

        assert len(cross) == 1
        assert cross[0].callee_id == "chunk_get_user_b"
        assert cross[0].status == ResolutionStatus.RESOLVED

    def test_external_lib_skipped(self):
        """np.array() where np is an external lib — must NOT be resolved cross-file."""
        raw = [{"caller_id": "chunk_process", "function_name": "np.array", "call_line": 28}]
        resolver = self._make_resolver(
            raw,
            import_map={"np": FILE_B},        # even if in import_map, external_lib overrides
            external_lib_names={"np"},
        )
        cross, unmatched = resolver.resolve()

        assert len(cross) == 0
        assert len(unmatched) == 1

    def test_function_not_in_target_file(self):
        """Import resolves the file but the function isn't defined there."""
        raw = [{"caller_id": "chunk_process", "function_name": "UserService.missing_fn", "call_line": 40}]
        resolver = self._make_resolver(raw, import_map={"UserService": FILE_B})
        cross, unmatched = resolver.resolve()

        assert len(cross) == 1
        assert cross[0].status == ResolutionStatus.UNRESOLVED
        assert cross[0].resolved_path == FILE_B
        assert "missing_fn" in cross[0].note

    def test_no_import_match_falls_through(self):
        """A call with no matching import → falls to external resolver."""
        raw = [{"caller_id": "chunk_process", "function_name": "unknown_fn", "call_line": 45}]
        resolver = self._make_resolver(raw, import_map={})
        cross, unmatched = resolver.resolve()

        assert len(cross) == 0
        assert len(unmatched) == 1

    def test_ambiguous_cross_file(self):
        """Multiple chunk_ids for the same name in the target file → AMBIGUOUS."""
        index_with_dup = {
            **GLOBAL_INDEX,
            (FILE_B, "get_user"): ["chunk_get_user_b", "chunk_get_user_b2"],
        }
        resolver = CrossFileCallResolver(
            raw_calls=[{"caller_id": "chunk_process", "function_name": "get_user", "call_line": 30}],
            import_map={"get_user": FILE_B},
            global_chunk_index=index_with_dup,
            external_lib_names=set(),
        )
        cross, _ = resolver.resolve()
        assert cross[0].status == ResolutionStatus.AMBIGUOUS
        assert len(cross[0].candidates) == 2

    def test_empty_raw_calls(self):
        resolver = self._make_resolver([])
        cross, unmatched = resolver.resolve()
        assert cross == []
        assert unmatched == []

    def test_external_lib_names_must_be_set(self):
        with pytest.raises(TypeError):
            CrossFileCallResolver(
                raw_calls=[],
                import_map={},
                global_chunk_index={},
                external_lib_names=["np"],  # list, not set
            )


# ─────────────────────────────────────────────────────────────────────────────
# ExternalLibraryResolver
# ─────────────────────────────────────────────────────────────────────────────

class TestExternalLibraryResolver:

    BASE_MODULE_MAP = {
        "np":       "numpy",
        "pd":       "pandas",
        "os":       "os",
        "path":     "os.path",
        "datetime": "datetime",
    }

    def _make_resolver(self, raw_calls, module_map=None, known_stdlib=None):
        return ExternalLibraryResolver(
            raw_calls=raw_calls,
            import_module_map=module_map or self.BASE_MODULE_MAP,
            known_stdlib=known_stdlib,
        )

    # --- happy path ---

    def test_qualified_library_call(self):
        raw = [{"caller_id": "chunk_process", "function_name": "np.array", "call_line": 10}]
        results = self._make_resolver(raw).resolve()

        assert len(results) == 1
        r = results[0]
        assert r.call_kind == CallKind.EXTERNAL
        assert r.status == ResolutionStatus.RESOLVED
        assert r.library == "numpy"
        assert r.callee_id is None

    def test_bare_import_call(self):
        """datetime() where `datetime` is imported at the top level."""
        raw = [{"caller_id": "chunk_process", "function_name": "datetime", "call_line": 12}]
        results = self._make_resolver(raw).resolve()

        assert results[0].library == "datetime"
        assert results[0].status == ResolutionStatus.RESOLVED

    def test_stdlib_annotation(self):
        raw = [{"caller_id": "chunk_process", "function_name": "os.path.join", "call_line": 15}]
        results = self._make_resolver(raw, known_stdlib=frozenset({"os"})).resolve()

        assert "stdlib" in results[0].note.lower()

    def test_third_party_annotation(self):
        raw = [{"caller_id": "chunk_process", "function_name": "np.array", "call_line": 18}]
        results = self._make_resolver(raw, known_stdlib=frozenset({"os"})).resolve()

        assert "third-party" in results[0].note.lower()

    def test_builtin_call(self):
        """print(), len(), etc. resolve to library='builtins' without an import entry."""
        for builtin in ["print", "len", "isinstance"]:
            raw = [{"caller_id": "chunk_process", "function_name": builtin, "call_line": 20}]
            results = self._make_resolver(raw, module_map={}).resolve()
            assert results[0].library == "builtins"
            assert results[0].status == ResolutionStatus.RESOLVED

    def test_unknown_call_marked_unresolved(self):
        """A call with no import and not a builtin → UNRESOLVED (not an exception)."""
        raw = [{"caller_id": "chunk_process", "function_name": "mystery_fn", "call_line": 25}]
        results = self._make_resolver(raw, module_map={}).resolve()

        assert results[0].status == ResolutionStatus.UNRESOLVED
        assert results[0].call_kind == CallKind.EXTERNAL
        assert results[0].library is None

    def test_no_calls_returns_empty_list(self):
        results = self._make_resolver([]).resolve()
        assert results == []

    def test_every_call_gets_a_result(self):
        """Terminal resolver must not leave any call unhandled."""
        raw = [
            {"caller_id": "c1", "function_name": "np.sum",     "call_line": 1},
            {"caller_id": "c1", "function_name": "print",      "call_line": 2},
            {"caller_id": "c1", "function_name": "mystery",    "call_line": 3},
            {"caller_id": "c1", "function_name": "pd.read_csv","call_line": 4},
        ]
        results = self._make_resolver(raw).resolve()
        assert len(results) == 4

    def test_multiple_calls_same_library(self):
        raw = [
            {"caller_id": "c1", "function_name": "np.array",   "call_line": 10},
            {"caller_id": "c1", "function_name": "np.zeros",   "call_line": 11},
            {"caller_id": "c1", "function_name": "np.ones",    "call_line": 12},
        ]
        results = self._make_resolver(raw).resolve()
        assert all(r.library == "numpy" for r in results)
        assert all(r.status == ResolutionStatus.RESOLVED for r in results)


# ─────────────────────────────────────────────────────────────────────────────
# CallGraphResolver (full pipeline integration)
# ─────────────────────────────────────────────────────────────────────────────

class TestCallGraphResolver:
    """
    Integration tests that verify the pipeline routing is correct end-to-end.
    A call classified by stage N must not bleed into stage N+1.
    """

    IMPORT_NAMES       = {"np", "pd", "os", "get_user"}
    IMPORT_MAP         = {"get_user": FILE_B}
    IMPORT_MODULE_MAP  = {"np": "numpy", "pd": "pandas", "os": "os"}
    EXTERNAL_LIB_NAMES = {"np", "pd", "os"}

    def _make_resolver(self, raw_calls):
        return CallGraphResolver(
            chunks=FILE_A_CHUNKS,
            raw_calls=raw_calls,
            import_names=self.IMPORT_NAMES,
            import_map=self.IMPORT_MAP,
            import_module_map=self.IMPORT_MODULE_MAP,
            global_chunk_index=GLOBAL_INDEX,
            external_lib_names=self.EXTERNAL_LIB_NAMES,
            use_stdlib_detection=False,
        )

    def test_all_three_kinds_in_one_batch(self):
        raw = [
            {"caller_id": "chunk_process", "function_name": "validate",    "call_line": 25},  # internal
            {"caller_id": "chunk_process", "function_name": "get_user",    "call_line": 26},  # cross-file
            {"caller_id": "chunk_process", "function_name": "np.array",    "call_line": 27},  # external
        ]
        result = self._make_resolver(raw).resolve()

        assert result.stats()["total"] == 3
        kinds = {r.call_kind for r in result.all_calls()}
        assert kinds == {CallKind.INTERNAL, CallKind.CROSS_FILE, CallKind.EXTERNAL}

    def test_internal_resolved_correctly(self):
        raw = [{"caller_id": "chunk_process", "function_name": "validate", "call_line": 25}]
        result = self._make_resolver(raw).resolve()

        assert len(result.resolved) == 1
        assert result.resolved[0].callee_id == "chunk_validate"
        assert result.resolved[0].call_kind == CallKind.INTERNAL

    def test_cross_file_resolved_correctly(self):
        raw = [{"caller_id": "chunk_process", "function_name": "get_user", "call_line": 26}]
        result = self._make_resolver(raw).resolve()

        assert len(result.resolved) == 1
        r = result.resolved[0]
        assert r.callee_id == "chunk_get_user_b"
        assert r.call_kind == CallKind.CROSS_FILE
        assert r.resolved_path == FILE_B

    def test_external_resolved_correctly(self):
        raw = [{"caller_id": "chunk_process", "function_name": "np.array", "call_line": 27}]
        result = self._make_resolver(raw).resolve()

        assert len(result.resolved) == 1
        r = result.resolved[0]
        assert r.library == "numpy"
        assert r.call_kind == CallKind.EXTERNAL

    def test_stats_sums_to_total(self):
        raw = [
            {"caller_id": "chunk_process", "function_name": "validate",  "call_line": 10},
            {"caller_id": "chunk_process", "function_name": "np.zeros",  "call_line": 11},
            {"caller_id": "chunk_process", "function_name": "mystery",   "call_line": 12},
        ]
        result = self._make_resolver(raw).resolve()
        s = result.stats()
        assert s["resolved"] + s["ambiguous"] + s["unresolved"] == s["total"]

    def test_empty_input(self):
        result = self._make_resolver([]).resolve()
        assert result.all_calls() == []
        assert result.stats()["total"] == 0

    def test_all_unresolved_gracefully(self):
        raw = [
            {"caller_id": "chunk_process", "function_name": "ghost_fn_1", "call_line": 1},
            {"caller_id": "chunk_process", "function_name": "ghost_fn_2", "call_line": 2},
        ]
        result = self._make_resolver(raw).resolve()
        # All should end up as external UNRESOLVED (terminal resolver catches them all)
        assert result.stats()["total"] == 2
        assert all(r.call_kind == CallKind.EXTERNAL for r in result.unresolved)

    def test_resolution_rate_calculation(self):
        raw = [
            {"caller_id": "chunk_process", "function_name": "validate", "call_line": 10},  # resolved
            {"caller_id": "chunk_process", "function_name": "ghost",    "call_line": 11},  # unresolved
        ]
        result = self._make_resolver(raw).resolve()
        assert result.stats()["resolution_rate"] == 0.5

    def test_all_calls_returns_full_flat_list(self):
        raw = [
            {"caller_id": "chunk_process", "function_name": "validate",  "call_line": 10},
            {"caller_id": "chunk_process", "function_name": "get_user",  "call_line": 11},
            {"caller_id": "chunk_process", "function_name": "np.array",  "call_line": 12},
        ]
        result = self._make_resolver(raw).resolve()
        assert len(result.all_calls()) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])