"""
Internal Call Resolver
======================
Resolves function calls where both caller and callee live in the same file.

Inputs (assumed correct by contract):
    chunks      — list of dicts representing all FunctionInfo rows for ONE file.
                  Each dict must have: id, name, file_id, start, end, class_id (nullable).
    raw_calls   — list of dicts produced by the chunker for ONE file.
                  Each dict must have: caller_id, function_name, call_line.
    import_names— set[str] of top-level names that are known imports for this file.
                  Used to exclude calls that look internal but are actually external.

Contract:
    - This resolver does NOT touch the database.
    - It does NOT resolve cross-file or external calls — those fall through as
      UNRESOLVED and must be handled by their respective resolvers.
    - A call is considered internal only if its base name matches a chunk name
      in the same file AND the base name is not in import_names.
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


def _base_name(call_expr: str) -> str:
    """
    Extract the final function name from a dotted call expression.

    Examples
    --------
    "self.validate"        → "validate"
    "helper"               → "helper"
    "obj.method.sub"       → "sub"
    "ClassName.static_fn"  → "static_fn"
    """
    return call_expr.strip().split(".")[-1]


def _build_name_index(chunks: list[dict[str, Any]]) -> dict[str, list[dict]]:
    """
    Map bare function names → list of chunk records with that name.
    Multiple chunks share a name when the same function exists in different
    classes within the same file (method overloading / sibling classes).
    """
    index: dict[str, list[dict]] = {}
    for chunk in chunks:
        name = chunk["name"]
        index.setdefault(name, []).append(chunk)
    return index


def _resolve_single_call(
    raw_call:     dict[str, Any],
    name_index:   dict[str, list[dict]],
    import_names: set[str],
    file_id:      str,
) -> ResolvedCall | None:
    """
    Attempt to resolve one raw call dict as an INTERNAL call.

    Returns
    -------
    ResolvedCall  — if the call is internal (resolved, ambiguous, or unresolved-internal)
    None          — if the call base name is an import; caller should skip to next resolver
    """
    caller_id     = raw_call["caller_id"]
    call_expr     = raw_call["function_name"]
    call_line     = raw_call.get("call_line")
    base          = _base_name(call_expr)

    # If the base name is a known import, this is NOT an internal call.
    if base in import_names:
        return None

    candidates = name_index.get(base, [])

    # No match at all — cannot determine kind yet; return unresolved-internal
    # so the orchestrator can hand it off to the cross-file resolver next.
    if not candidates:
        return None  # signal: not provably internal, pass to next resolver

    # Narrow by class context when the call is a dotted method call.
    # "self.validate" → only match chunks whose class_id is the same as the caller's.
    if "." in call_expr:
        caller_class_id = _get_caller_class(caller_id, name_index)
        class_scoped = [c for c in candidates if c.get("class_id") == caller_class_id]
        if class_scoped:
            candidates = class_scoped

    if len(candidates) == 1:
        callee = candidates[0]
        logger.debug(
            "Internal resolved: %s → %s (line %s)", call_expr, callee["id"], call_line
        )
        return ResolvedCall(
            caller_id=caller_id,
            callee_id=callee["id"],
            call_kind=CallKind.INTERNAL,
            function_name=call_expr,
            call_line=call_line,
            status=ResolutionStatus.RESOLVED,
        )

    # Multiple candidates — ambiguous within the same file.
    candidate_ids = tuple(c["id"] for c in candidates)
    logger.warning(
        "Internal ambiguous: %s matched %d chunks in file %s",
        call_expr, len(candidates), file_id,
    )
    return ResolvedCall(
        caller_id=caller_id,
        callee_id=None,
        call_kind=CallKind.INTERNAL,
        function_name=call_expr,
        call_line=call_line,
        status=ResolutionStatus.AMBIGUOUS,
        candidates=candidate_ids,
        note=f"Matched {len(candidates)} chunks with name '{base}' in the same file.",
    )


def _get_caller_class(caller_id: str, name_index: dict[str, list[dict]]) -> str | None:
    """
    Look up the class_id of the caller chunk from the flat name index.
    Used to scope dotted method calls to their enclosing class.
    """
    for chunks in name_index.values():
        for chunk in chunks:
            if chunk["id"] == caller_id:
                return chunk.get("class_id")
    return None


class InternalCallResolver:
    """
    Resolves intra-file function calls.

    Usage
    -----
        resolver = InternalCallResolver(chunks, raw_calls, import_names)
        resolved, unmatched = resolver.resolve()

        # resolved   → list[ResolvedCall] with kind=INTERNAL
        # unmatched  → list[dict] raw calls that are NOT internal; pass to next resolver
    """

    def __init__(
        self,
        chunks:       list[dict[str, Any]],
        raw_calls:    list[dict[str, Any]],
        import_names: set[str],
    ) -> None:
        """
        Parameters
        ----------
        chunks        All FunctionInfo chunks belonging to one file.
        raw_calls     All raw call dicts extracted by the chunker for that file.
        import_names  Top-level imported names (first segment only).
                      E.g. `from os import path` → {"path"};
                           `import numpy as np`  → {"np"}.
        """
        if not isinstance(import_names, set):
            raise TypeError("import_names must be a set[str]")

        self._chunks       = chunks
        self._raw_calls    = raw_calls
        self._import_names = import_names
        self._file_id      = chunks[0]["file_id"] if chunks else "unknown"
        self._name_index   = _build_name_index(chunks)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve(self) -> tuple[list[ResolvedCall], list[dict[str, Any]]]:
        """
        Returns
        -------
        (internal_calls, unmatched_raw_calls)

        internal_calls      All ResolvedCall objects with kind=INTERNAL.
                            Includes both RESOLVED and AMBIGUOUS status.
        unmatched_raw_calls Raw call dicts that could not be identified as
                            internal. Pass these to the cross-file or external
                            resolver next.
        """
        internal_calls: list[ResolvedCall]   = []
        unmatched:      list[dict[str, Any]] = []

        for raw_call in self._raw_calls:
            result = _resolve_single_call(
                raw_call=raw_call,
                name_index=self._name_index,
                import_names=self._import_names,
                file_id=self._file_id,
            )
            if result is not None:
                internal_calls.append(result)
            else:
                unmatched.append(raw_call)

        logger.info(
            "InternalCallResolver [%s]: %d resolved/ambiguous internal, %d unmatched",
            self._file_id, len(internal_calls), len(unmatched),
        )
        return internal_calls, unmatched