"""
Cross-File Call Resolver
========================
Resolves function calls where the callee is defined in a *different* file
within the same repository.

Inputs (assumed correct by contract):
    raw_calls       — list[dict] of unmatched calls forwarded from InternalCallResolver.
                      Each dict: caller_id, function_name, call_line.
    import_map      — dict mapping imported name/alias → source file_id.
                      Built from the file's normalized import records.
                      Example:
                        {
                          "UserService": "src/services/user_service.py::file_id_abc",
                          "validate":    "src/utils/validators.py::file_id_def",
                          "utils":       "src/utils/__init__.py::file_id_ghi",
                        }
    global_chunk_index — dict mapping (file_id, function_name) → list[chunk_id].
                         Represents all functions across the entire repo.
                         Example:
                           {
                             ("file_id_abc", "get_user"): ["chunk_id_1"],
                             ("file_id_def", "validate"): ["chunk_id_2", "chunk_id_3"],
                           }
    external_lib_names — set[str] of top-level library names that are known external.
                         Used to exclude calls that look cross-file but are stdlib/pip.

Contract:
    - Does NOT touch the database.
    - Does NOT handle external (library) calls — those fall through as unmatched.
    - A call is cross-file if its base name (or qualifier) matches an entry in
      import_map that points to a different file_id than the caller's file.
    - Method calls on imported objects (e.g. `service.get_user()`) are resolved
      by looking up `service` in import_map, then finding `get_user` in that file.
"""

from __future__ import annotations

import logging
from typing import Any

from app.call_graph_resolver.models.call_resolution import (
    CallKind,
    ResolvedCall,
    ResolutionStatus,
)

logger = logging.getLogger(__name__)


def _split_call_expr(call_expr: str) -> tuple[str | None, str]:
    """
    Split a dotted call expression into (qualifier, base_name).

    Examples
    --------
    "service.get_user"    → ("service", "get_user")
    "validate"            → (None,      "validate")
    "a.b.c"               → ("a",       "c")         ← qualifier is first segment
    """
    parts = call_expr.strip().split(".")
    if len(parts) == 1:
        return None, parts[0]
    return parts[0], parts[-1]


def _resolve_single_call(
    raw_call:            dict[str, Any],
    import_map:          dict[str, str],
    global_chunk_index:  dict[tuple[str, str], list[str]],
    external_lib_names:  set[str],
) -> ResolvedCall | None:
    """
    Try to resolve one raw call as a CROSS_FILE call.

    Returns
    -------
    ResolvedCall  — if the call resolves to a different file (resolved or ambiguous)
    None          — if the call cannot be identified as cross-file
                    (should be passed to ExternalLibraryResolver)
    """
    caller_id  = raw_call["caller_id"]
    call_expr  = raw_call["function_name"]
    call_line  = raw_call.get("call_line")

    qualifier, base = _split_call_expr(call_expr)

    if qualifier and qualifier in import_map:
        # Don't cross-resolve if the qualifier is a known external library.
        if qualifier in external_lib_names:
            return None

        target_file_id = import_map[qualifier]
        return _lookup_in_file(
            caller_id=caller_id,
            call_expr=call_expr,
            call_line=call_line,
            target_file_id=target_file_id,
            base=base,
            global_chunk_index=global_chunk_index,
        )

    # --- Strategy 2: base name directly imported from another file ---
    # e.g.  `from utils.validators import validate` then `validate()`
    if base in import_map:
        if base in external_lib_names:
            return None

        target_file_id = import_map[base]
        return _lookup_in_file(
            caller_id=caller_id,
            call_expr=call_expr,
            call_line=call_line,
            target_file_id=target_file_id,
            base=base,
            global_chunk_index=global_chunk_index,
        )

    # Not resolvable as cross-file — pass to external resolver.
    return None


def _lookup_in_file(
    caller_id:           str,
    call_expr:           str,
    call_line:           int | None,
    target_file_id:      str,
    base:                str,
    global_chunk_index:  dict[tuple[str, str], list[str]],
) -> ResolvedCall:
    """
    Look up `base` in `target_file_id` via the global chunk index.
    Always returns a ResolvedCall; status reflects match quality.
    """
    key = (target_file_id, base)
    candidate_ids = global_chunk_index.get(key, [])

    # Attempt fuzzy fallback: search all functions in the target file.
    if not candidate_ids:
        all_in_file = [
            ids
            for (fid, _name), ids in global_chunk_index.items()
            if fid == target_file_id
        ]
        flat = [cid for ids in all_in_file for cid in ids]
        logger.debug(
            "Cross-file unresolved: %s not found in file %s (has %d functions)",
            call_expr, target_file_id, len(flat),
        )
        return ResolvedCall(
            caller_id=caller_id,
            callee_id=None,
            call_kind=CallKind.CROSS_FILE,
            function_name=call_expr,
            call_line=call_line,
            status=ResolutionStatus.UNRESOLVED,
            resolved_path=target_file_id,
            note=f"Import resolved to file '{target_file_id}' but function '{base}' not found there.",
        )

    if len(candidate_ids) == 1:
        logger.debug(
            "Cross-file resolved: %s → %s in file %s",
            call_expr, candidate_ids[0], target_file_id,
        )
        return ResolvedCall(
            caller_id=caller_id,
            callee_id=candidate_ids[0],
            call_kind=CallKind.CROSS_FILE,
            function_name=call_expr,
            call_line=call_line,
            status=ResolutionStatus.RESOLVED,
            resolved_path=target_file_id,
        )

    # Multiple chunks with the same name in the target file — ambiguous.
    logger.warning(
        "Cross-file ambiguous: %s matched %d chunks in file %s",
        call_expr, len(candidate_ids), target_file_id,
    )
    return ResolvedCall(
        caller_id=caller_id,
        callee_id=None,
        call_kind=CallKind.CROSS_FILE,
        function_name=call_expr,
        call_line=call_line,
        status=ResolutionStatus.AMBIGUOUS,
        resolved_path=target_file_id,
        candidates=tuple(candidate_ids),
        note=f"Matched {len(candidate_ids)} overloads of '{base}' in '{target_file_id}'.",
    )


class CrossFileCallResolver:
    """
    Resolves calls to functions defined in other files of the same repository.

    Usage
    -----
        resolver = CrossFileCallResolver(
            raw_calls=unmatched_from_internal_resolver,
            import_map=file_import_map,
            global_chunk_index=repo_chunk_index,
            external_lib_names=known_external_libs,
        )
        cross_file_calls, still_unmatched = resolver.resolve()

        # cross_file_calls → list[ResolvedCall] with kind=CROSS_FILE
        # still_unmatched  → list[dict] to pass to ExternalLibraryResolver
    """

    def __init__(
        self,
        raw_calls:           list[dict[str, Any]],
        import_map:          dict[str, str],
        global_chunk_index:  dict[tuple[str, str], list[str]],
        external_lib_names:  set[str],
    ) -> None:
        """
        Parameters
        ----------
        raw_calls
            Unmatched raw call dicts from InternalCallResolver.
        import_map
            Dict of {imported_name_or_alias → file_id_of_source}.
            Must be pre-built by the caller from normalized import records.
        global_chunk_index
            Dict of {(file_id, function_name) → [chunk_id, ...]}.
            Covers every function in the entire repository.
        external_lib_names
            Set of names that are known external library roots.
            These short-circuit cross-file resolution to avoid false matches.
        """
        if not isinstance(external_lib_names, set):
            raise TypeError("external_lib_names must be a set[str]")

        self._raw_calls          = raw_calls
        self._import_map         = import_map
        self._global_chunk_index = global_chunk_index
        self._external_lib_names = external_lib_names

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve(self) -> tuple[list[ResolvedCall], list[dict[str, Any]]]:
        """
        Returns
        -------
        (cross_file_calls, still_unmatched)

        cross_file_calls    ResolvedCall objects with kind=CROSS_FILE.
                            Includes RESOLVED, AMBIGUOUS, and UNRESOLVED
                            (where import resolved but function not found).
        still_unmatched     Raw call dicts that could not be identified as
                            cross-file. Pass to ExternalLibraryResolver.
        """
        cross_file_calls: list[ResolvedCall]   = []
        still_unmatched:  list[dict[str, Any]] = []

        for raw_call in self._raw_calls:
            result = _resolve_single_call(
                raw_call=raw_call,
                import_map=self._import_map,
                global_chunk_index=self._global_chunk_index,
                external_lib_names=self._external_lib_names,
            )
            if result is not None:
                cross_file_calls.append(result)
            else:
                still_unmatched.append(raw_call)

        logger.info(
            "CrossFileCallResolver: %d cross-file, %d still unmatched",
            len(cross_file_calls), len(still_unmatched),
        )
        return cross_file_calls, still_unmatched