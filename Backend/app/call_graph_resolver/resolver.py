"""
Call Graph Resolver
===================
Orchestrates the three independent resolvers into a single pipeline:

    raw calls
        ↓
    InternalCallResolver       (same-file calls)
        ↓ unmatched
    CrossFileCallResolver      (calls to other repo files)
        ↓ still unmatched
    ExternalLibraryResolver    (stdlib / third-party calls)
        ↓
    CallResolutionResult

Each resolver is completely independent — it does not call the others and
makes no assumptions about the outside world beyond its declared inputs.
The orchestrator is the ONLY place that knows the pipeline order.

All inputs are assumed correct (pre-validated / pre-built by the caller).

Example
-------
    from call_graph_resolver import CallGraphResolver

    result = CallGraphResolver(
        chunks=file_chunks,
        raw_calls=file_raw_calls,
        import_names={"np", "os", "UserService"},
        import_map={"UserService": "file_id_abc", "validate": "file_id_def"},
        import_module_map={"np": "numpy", "os": "os"},
        global_chunk_index={("file_id_abc", "get_user"): ["chunk_id_1"]},
        external_lib_names={"np", "os"},
    ).resolve()

    print(result.stats())
    # {'total': 42, 'resolved': 38, 'ambiguous': 2, 'unresolved': 2,
    #  'resolution_rate': 0.905}
"""

from __future__ import annotations

import logging
import sys
from typing import Any

from app.call_graph_resolver.models.call_resolution import (
    CallResolutionResult,
    CallKind,
    ResolutionStatus,
    ResolvedCall,
)
from app.call_graph_resolver.resolvers.internal_resolver import InternalCallResolver
from app.call_graph_resolver.resolvers.cross_resolver import CrossFileCallResolver
from app.call_graph_resolver.resolvers.external_resolver import ExternalLibraryResolver
from app.call_graph_resolver.call_graph import CallGraphDBFetcher

logger = logging.getLogger(__name__)


class CallGraphResolver:
    """
    Single entry-point for full call-graph resolution.

    Parameters
    ----------
    chunks
        All FunctionInfo dicts for the file being resolved.
        Required keys per dict: id, name, file_id, start, end, class_id (nullable).

    raw_calls
        All raw call dicts extracted by the chunker for this file.
        Required keys per dict: caller_id, function_name, call_line.

    import_names
        set[str] of top-level imported names for this file.
        Used by InternalCallResolver to exclude calls that look internal
        but are actually imports.
        Example: `from os import path` → {"path"}

    import_map
        dict[str, str] mapping imported name/alias → source file_id.
        Used by CrossFileCallResolver.
        Example: {"UserService": "src/services/user_service.py::abc123"}

    import_module_map
        dict[str, str] mapping imported name/alias → library root.
        Used by ExternalLibraryResolver.
        Example: {"np": "numpy", "pd": "pandas", "os": "os"}

    global_chunk_index
        dict[(file_id, function_name) → list[chunk_id]] covering all repo files.
        Used by CrossFileCallResolver for name lookup.

    external_lib_names
        set[str] of names known to be external library roots.
        Used by CrossFileCallResolver to skip cross-file resolution attempts
        on library-prefixed calls like "np.array".

    use_stdlib_detection
        If True, auto-populate known_stdlib from sys.stdlib_module_names
        (Python 3.10+) for richer external call annotation.
    """

    def __init__(
        self,
        chunks:               list[dict[str, Any]],
        raw_calls:            list[dict[str, Any]],
        import_names:         set[str],
        import_map:           dict[str, str],
        import_module_map:    dict[str, str],
        global_chunk_index:   dict[tuple[str, str], list[str]],
        external_lib_names:   set[str],
        use_stdlib_detection: bool = True,
    ) -> None:
        self._chunks              = chunks
        self._raw_calls           = raw_calls
        self._import_names        = import_names
        self._import_map          = import_map
        self._import_module_map   = import_module_map
        self._global_chunk_index  = global_chunk_index
        self._external_lib_names  = external_lib_names
        self._known_stdlib        = self._load_stdlib() if use_stdlib_detection else frozenset()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve(self) -> CallResolutionResult:
        """
        Run the full three-stage resolution pipeline.

        Returns
        -------
        CallResolutionResult
            Partitioned into resolved / ambiguous / unresolved lists.
            Call .stats() for a summary dict.
        """
        file_id = self._chunks[0]["file_id"] if self._chunks else "unknown"
        logger.info(
            "CallGraphResolver starting: file=%s, chunks=%d, raw_calls=%d",
            file_id, len(self._chunks), len(self._raw_calls),
        )

        # --- Stage 1: internal ---
        internal_resolver = InternalCallResolver(
            chunks=self._chunks,
            raw_calls=self._raw_calls,
            import_names=self._import_names,
        )
        internal_calls, after_internal = internal_resolver.resolve()

        # --- Stage 2: cross-file ---
        cross_file_resolver = CrossFileCallResolver(
            raw_calls=after_internal,
            import_map=self._import_map,
            global_chunk_index=self._global_chunk_index,
            external_lib_names=self._external_lib_names,
        )
        cross_file_calls, after_cross_file = cross_file_resolver.resolve()

        # --- Stage 3: external (terminal — no remainder) ---
        external_resolver = ExternalLibraryResolver(
            raw_calls=after_cross_file,
            import_module_map=self._import_module_map,
            known_stdlib=self._known_stdlib,
        )
        external_calls = external_resolver.resolve()

        # --- Merge and partition ---
        all_calls = internal_calls + cross_file_calls + external_calls
        result = _partition(all_calls)

        logger.info(
            "CallGraphResolver done: %s", result.stats()
        )
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_stdlib() -> frozenset[str]:
        """
        Load known stdlib names from sys.stdlib_module_names (Python 3.10+).
        Falls back gracefully on older versions.
        """
        try:
            return frozenset(sys.stdlib_module_names)  # type: ignore[attr-defined]
        except AttributeError:
            logger.debug("sys.stdlib_module_names unavailable (Python < 3.10); stdlib detection disabled.")
            return frozenset()


def _partition(calls: list[ResolvedCall]) -> CallResolutionResult:
    """
    Split a flat list of ResolvedCall into the three result buckets.
    """
    result = CallResolutionResult()
    for call in calls:
        if call.status == ResolutionStatus.RESOLVED:
            result.resolved.append(call)
        elif call.status == ResolutionStatus.AMBIGUOUS:
            result.ambiguous.append(call)
        else:
            result.unresolved.append(call)
    return result

