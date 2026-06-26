"""
External Library Call Resolver
================================
Classifies function calls that originate from stdlib or third-party (pip) imports.

By this stage the call has already been rejected by both InternalCallResolver
and CrossFileCallResolver — the only remaining candidates are external.

Inputs (assumed correct by contract):
    raw_calls       — list[dict] forwarded from CrossFileCallResolver.
                      Each dict: caller_id, function_name, call_line.
    import_module_map — dict mapping imported name/alias → library root.
                        Built from the file's normalized import_modules records.
                        Example:
                          {
                            "np":       "numpy",
                            "pd":       "pandas",
                            "os":       "os",
                            "path":     "os.path",
                            "datetime": "datetime",
                            "Session":  "sqlalchemy.orm",
                          }
    known_stdlib     — optional set[str] of stdlib top-level package names.
                       If provided, used to tag calls as stdlib vs third-party.
                       If omitted, all external calls are tagged EXTERNAL without
                       distinguishing stdlib vs pip.

Contract:
    - Does NOT touch the database.
    - Does NOT perform network calls or introspect installed packages.
    - Every call passed in is classified — none fall through as None.
    - Calls whose qualifier/base name is not in import_module_map are marked
      UNRESOLVED with a note; they may be dynamic calls, builtins, or
      chunker noise.
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


# Commonly used builtins that are valid call targets but have no import.
# Calls to these should be UNRESOLVED with an informative note rather than
# treated as missing imports.
_PYTHON_BUILTINS = frozenset({
    "print", "len", "range", "enumerate", "zip", "map", "filter",
    "sorted", "reversed", "list", "dict", "set", "tuple", "str", "int",
    "float", "bool", "bytes", "type", "isinstance", "issubclass",
    "hasattr", "getattr", "setattr", "delattr", "callable", "iter",
    "next", "open", "repr", "hash", "id", "abs", "round", "min", "max",
    "sum", "any", "all", "vars", "dir", "help", "input", "super",
})


def _split_call_expr(call_expr: str) -> tuple[str | None, str]:
    """
    Split a dotted call expression into (qualifier, base_name).

    "np.array"       → ("np", "array")
    "os.path.join"   → ("os", "join")    ← qualifier is always the first segment
    "datetime"       → (None, "datetime")
    """
    parts = call_expr.strip().split(".")
    if len(parts) == 1:
        return None, parts[0]
    return parts[0], parts[-1]


def _resolve_single_call(
    raw_call:          dict[str, Any],
    import_module_map: dict[str, str],
    known_stdlib:      frozenset[str],
) -> ResolvedCall:
    """
    Classify one call as EXTERNAL or UNRESOLVED.

    Always returns a ResolvedCall — external calls have no callee_id.
    """
    caller_id  = raw_call["caller_id"]
    call_expr  = raw_call["function_name"]
    call_line  = raw_call.get("call_line")

    qualifier, base = _split_call_expr(call_expr)

    # --- Try to match via qualifier (e.g. "np" in "np.array") ---
    lookup_key = qualifier if qualifier else base
    library = import_module_map.get(lookup_key)

    if library:
        logger.debug(
            "External resolved: %s → library '%s' (line %s)",
            call_expr, library, call_line,
        )
        return ResolvedCall(
            caller_id=caller_id,
            callee_id=None,
            call_kind=CallKind.EXTERNAL,
            function_name=call_expr,
            call_line=call_line,
            status=ResolutionStatus.RESOLVED,
            library=library,
            note=_classify_library_note(library, known_stdlib),
        )

    # --- Builtin: valid but no import entry ---
    if base in _PYTHON_BUILTINS:
        logger.debug("External builtin: %s (line %s)", call_expr, call_line)
        return ResolvedCall(
            caller_id=caller_id,
            callee_id=None,
            call_kind=CallKind.EXTERNAL,
            function_name=call_expr,
            call_line=call_line,
            status=ResolutionStatus.RESOLVED,
            library="builtins",
            note="Python builtin — no import required.",
        )

    # --- Could not match to any known import ---
    logger.warning(
        "External unresolved: '%s' — not in import_module_map and not a builtin (line %s)",
        call_expr, call_line,
    )
    return ResolvedCall(
        caller_id=caller_id,
        callee_id=None,
        call_kind=CallKind.EXTERNAL,
        function_name=call_expr,
        call_line=call_line,
        status=ResolutionStatus.UNRESOLVED,
        note=(
            f"'{call_expr}' not found in import map and not a known builtin. "
            "Possible causes: dynamic call, attribute on a local variable, "
            "or a missing import record."
        ),
    )


def _classify_library_note(library: str, known_stdlib: frozenset[str]) -> str:
    """
    Produce a short annotation indicating stdlib vs third-party.
    """
    root = library.split(".")[0]
    if not known_stdlib:
        return f"External library: {library}"
    if root in known_stdlib:
        return f"Python stdlib: {library}"
    return f"Third-party package: {library}"


class ExternalLibraryResolver:
    """
    Classifies remaining unmatched calls as external library / builtin calls.

    This is the terminal resolver in the pipeline — every call passed in will
    receive a ResolvedCall with kind=EXTERNAL. Calls that cannot be attributed
    to any import get status=UNRESOLVED with an explanatory note.

    Usage
    -----
        resolver = ExternalLibraryResolver(
            raw_calls=still_unmatched,
            import_module_map=file_module_map,
            known_stdlib=frozenset(sys.stdlib_module_names),  # optional
        )
        external_calls = resolver.resolve()
        # external_calls → list[ResolvedCall] with kind=EXTERNAL, no unmatched remainder
    """

    def __init__(
        self,
        raw_calls:          list[dict[str, Any]],
        import_module_map:  dict[str, str],
        known_stdlib:       frozenset[str] | None = None,
    ) -> None:
        """
        Parameters
        ----------
        raw_calls
            Unmatched raw call dicts from CrossFileCallResolver.
        import_module_map
            Dict of {imported_name_or_alias → library_root_path}.
            E.g. {"np": "numpy", "os": "os", "Session": "sqlalchemy.orm"}.
        known_stdlib
            Optional frozenset of stdlib module names for annotation.
            If None, all resolved external calls are annotated as "External library".
            Recommended: pass `frozenset(sys.stdlib_module_names)` on Python 3.10+.
        """
        self._raw_calls         = raw_calls
        self._import_module_map = import_module_map
        self._known_stdlib      = known_stdlib or frozenset()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve(self) -> list[ResolvedCall]:
        """
        Classify all remaining calls.

        Returns
        -------
        list[ResolvedCall]
            Every call classified as EXTERNAL (no remainder — this is the
            terminal resolver). Status may be RESOLVED or UNRESOLVED.
        """
        results: list[ResolvedCall] = []

        for raw_call in self._raw_calls:
            result = _resolve_single_call(
                raw_call=raw_call,
                import_module_map=self._import_module_map,
                known_stdlib=self._known_stdlib,
            )
            results.append(result)

        resolved_count   = sum(1 for r in results if r.is_resolved())
        unresolved_count = len(results) - resolved_count

        logger.info(
            "ExternalLibraryResolver: %d external resolved, %d unresolved",
            resolved_count, unresolved_count,
        )
        return results