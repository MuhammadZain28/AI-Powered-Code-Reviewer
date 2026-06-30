"""
Call Graph DB Fetcher
=====================
Responsible for one thing: fetching and shaping raw database rows into the
exact structures that CallGraphResolver expects.

No resolution logic lives here — this module is purely a data-access layer.

Design
------
Fetching is split into two tiers:

  1. Project-level (fetch once per run):
       - global_chunk_index  →  dict[(file_id, fn_name) → list[chunk_id]]
       - file_ids            →  list[str] of all file IDs in the project

  2. File-level (fetch per file):
       - chunks              →  functions belonging to this file
       - raw_calls           →  unresolved calls whose caller is in this file
       - import_names        →  set[str] of top-level imported names
       - import_map          →  dict[name → file_id]  (internal imports only)
       - import_module_map   →  dict[name → lib_root]  (external imports only)
       - external_lib_names  →  set[str] of external library roots

The public surface is:
    fetcher = CallGraphDBFetcher(project_id)
    file_ids           = await fetcher.fetch_file_ids()
    global_chunk_index = await fetcher.fetch_global_chunk_index()

    for file_id in file_ids:
        kwargs = await fetcher.fetch_for_file(file_id, global_chunk_index)
        resolver = CallGraphResolver(**kwargs)

Schema assumptions
------------------
  functions        → id, file_id, class_id, name, start_line, end_line
  imports          → id, file_id, from_module, type, is_external
  import_symbols   → id, import_id, symbol, alias, is_used
  call_graph       → id, caller_id, callee_id, function_name, call_line
  files            → id, project_id, path

All queries accept an asyncpg Connection / Pool (or any object exposing
.fetch() / .fetchrow()). Swap for psycopg3 or SQLAlchemy Core by replacing
the thin `_fetch` / `_fetchrow` wrappers at the bottom of the file.
"""

from __future__ import annotations

import logging
from typing import Any
from app.managers.database import Database

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Main fetcher
# ---------------------------------------------------------------------------

class CallGraphDBFetcher:
    """
    Two-tier fetcher: project-level data is fetched once; per-file data is
    fetched on demand.

    Typical usage::

        fetcher            = CallGraphDBFetcher(project_id)
        file_ids           = await fetcher.fetch_file_ids()
        global_chunk_index = await fetcher.fetch_global_chunk_index()

        for file_id in file_ids:
            kwargs = await fetcher.fetch_for_file(file_id, global_chunk_index)
            resolver = CallGraphResolver(**kwargs)
            results  = resolver.resolve()
    """

    def __init__(self, project_id: str) -> None:
        self._project_id = project_id
        self.db = Database()

    # ------------------------------------------------------------------
    # Project-level fetches  (call once per run)
    # ------------------------------------------------------------------

    async def fetch_file_ids(self) -> list[str]:
        """
        Return all file IDs that belong to the project.

        The caller iterates this list and calls fetch_for_file() for each one.
        """
        rows = await self.db.fetch(
            """
            SELECT id::text AS file_id
            FROM   files
            WHERE  project_id = $1::uuid
            ORDER  BY path
            """,
            self._project_id,
        )

        file_ids = [r["file_id"] for r in rows]

        if not file_ids:
            logger.warning(
                "CallGraphDBFetcher: no files found for project_id=%s",
                self._project_id,
            )

        logger.info(
            "CallGraphDBFetcher: project=%s has %d files",
            self._project_id,
            len(file_ids),
        )

        return file_ids

    async def fetch_global_chunk_index(self) -> dict[tuple[str, str], list[str]]:
        """
        Build the repo-wide index used by CrossFileCallResolver.

        Returns
        -------
        dict[(file_id, function_name) → list[chunk_id]]
            All functions across every file in the project, grouped by
            (file_id, name) so the resolver can look up callee IDs by name.
        """
        rows = await self.db.fetch(
            """
            SELECT
                f.id::text      AS chunk_id,
                f.file_id::text AS file_id,
                f.name          AS function_name,
                f.id::text      AS chunk_id
            FROM functions f
            JOIN files fi ON fi.id = f.file_id
            WHERE fi.project_id = $1::uuid
            ORDER BY f.file_id, f.name
            """,
            self._project_id,
        )


        index: dict[str, dict[str, str]] = {}
        for row in rows:
            key = row["file_id"]
            index.setdefault(key, {})[row["function_name"]] = row["chunk_id"]

        logger.info(
            "CallGraphDBFetcher: global_chunk_index has %d entries for project=%s",
            len(index),
            self._project_id,
        )

        return index

    # ------------------------------------------------------------------
    # File-level fetch  (call once per file)
    # ------------------------------------------------------------------

    async def fetch_for_file(self, file_id: str, global_chunk_index: dict[tuple[str, str], list[str]]) -> dict[str, Any]:
        """
        Fetch all resolver inputs for a single file and return them as a
        dict ready to splat directly into ``CallGraphResolver(**kwargs)``.

        Parameters
        ----------
        file_id:
            The UUID (as str) of the file to resolve.
        global_chunk_index:
            The repo-wide index returned by ``fetch_global_chunk_index()``.
            Passed through unchanged so the resolver can do cross-file lookups.

        Returns
        -------
        dict with the following keys — matching CallGraphResolver's signature::

            chunks              list[dict]               functions in this file
            raw_calls           list[dict]               unresolved calls from this file
            import_names        set[str]                 top-level imported names
            import_map          dict[str, str]           name → source file_id
            import_module_map   dict[str, str]           name → library root
            global_chunk_index  dict[(str,str),list[str]]  repo-wide function index
            external_lib_names  set[str]                 known external library roots
        """
        logger.debug(
            "CallGraphDBFetcher: fetching data for file_id=%s (project=%s)",
            file_id,
            self._project_id,
        )

        chunks = await self._fetch_chunks_for_file(file_id)
        raw_calls = await self._fetch_raw_calls_for_file(file_id, chunks)
        (
            import_names,
            import_map,
            import_module_map,
            external_lib_names,
        ) = await self._fetch_import_data_for_file(file_id)

        logger.debug(
            "CallGraphDBFetcher: file=%s — chunks=%d, raw_calls=%d, "
            "import_names=%d, import_map=%d, import_module_map=%d",
            file_id,
            len(chunks),
            len(raw_calls),
            len(import_names),
            len(import_map),
            len(import_module_map),
        )

        return {
            "chunks":             chunks,
            "raw_calls":          raw_calls,
            "import_names":       import_names,
            "import_map":         import_map,
            "import_module_map":  import_module_map,
            "global_chunk_index": global_chunk_index,
            "external_lib_names": external_lib_names,
        }

    # ------------------------------------------------------------------
    # Private — file-scoped queries
    # ------------------------------------------------------------------

    async def _fetch_chunks_for_file(self, file_id: str) -> list[dict[str, Any]]:
        """
        Fetch all functions belonging to *file_id*.

        Each dict has the keys expected by CallGraphResolver:
            id, name, file_id, start, end, class_id
        """
        rows = await self.db.fetch(
            """
            SELECT
                id::text        AS id,
                name,
                file_id::text   AS file_id,
                start_line      AS start,
                end_line        AS end,
                class_id::text  AS class_id
            FROM functions
            WHERE file_id = $1::uuid
            ORDER BY start_line
            """,
            file_id,
        )

        chunks = [dict(r) for r in rows]

        if not chunks:
            logger.debug(
                "CallGraphDBFetcher: no functions found for file_id=%s", file_id
            )

        return chunks

    async def _fetch_raw_calls_for_file(
        self,
        file_id: str,
        chunks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Fetch unresolved call_graph rows whose caller belongs to *file_id*.

        Only rows with ``callee_id IS NULL`` are returned — these are the raw
        calls that still need resolution.

        Each dict has the keys expected by CallGraphResolver:
            caller_id, function_name, call_line
        """
        if not chunks:
            # No functions in this file → no calls possible.
            return []

        chunk_ids = [c["id"] for c in chunks]

        rows = await self.db.fetch(
            """
            SELECT
                caller_id::text AS caller_id,
                function_name,
                call_line
            FROM function_calls
            WHERE caller_id = ANY($1::uuid[])
            ORDER BY call_line
            """,
            chunk_ids,
        )

        return [dict(r) for r in rows]

    async def _fetch_import_data_for_file(self, file_id: str) -> tuple[set[str], dict[str, str], dict[str, str], set[str]]:
        """
        Fetch and shape all import information for *file_id*.

        Returns
        -------
        import_names : set[str]
            Every top-level imported name (alias preferred over symbol,
            symbol preferred over bare module name).
            Example: ``from os import path as p`` → ``{"p"}``

        import_map : dict[str, str]
            Internal imports only: ``name → file_id`` of the source file.
            Example: ``{"UserService": "<uuid>"}``

        import_module_map : dict[str, str]
            External imports only: ``name → library root``.
            Example: ``{"np": "numpy", "pd": "pandas"}``

        external_lib_names : set[str]
            The set of library roots referenced by any external import.
            Example: ``{"numpy", "pandas", "os"}``
        """
        rows = await self.db.fetch(
            """
            SELECT
                i.from_module,
                i.is_external,
                s.symbol,
                s.alias
            FROM imports i
            LEFT JOIN import_symbols s ON s.import_id = i.id
            WHERE i.file_id = $1::uuid
            ORDER BY i.id
            """,
            file_id,
        )

        import_names:       set[str]       = set()
        import_map:         dict[str, str] = {}   # name → file_id (internal)
        import_module_map:  dict[str, str] = {}   # name → lib_root (external)
        external_lib_names: set[str]       = set()

        _pending_internal: dict[str, str] = {}

        for row in rows:
            from_module  = row["from_module"] or ""
            is_external  = row["is_external"]
            symbol       = row["symbol"]
            alias        = row["alias"]

            effective_name: str | None = alias or symbol or from_module or None

            if not effective_name:
                continue

            import_names.add(effective_name)

            lib_root = from_module or effective_name
            import_module_map[effective_name] = lib_root
            external_lib_names.add(lib_root)


        return import_names, import_map, import_module_map, external_lib_names

    async def copy_resolved_calls_to_database(self, resolved_calls: list):
        if not resolved_calls:
            logger.info("No resolved calls to copy to database.")
            return

        _ = await self.db.copy_to_table(table_name="call_graph", data=resolved_calls, columns=["caller_id", "callee_id", "function_name", "call_line", "call_type", "library", "resolved_path"])

# ---------------------------------------------------------------------------
# Smoke-test entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        project_id = "ad124d38-5776-42b4-8fa3-b10648a6b901"

        fetcher = CallGraphDBFetcher(project_id=project_id)

        file_ids           = await fetcher.fetch_file_ids()
        global_chunk_index = await fetcher.fetch_global_chunk_index()

        print(f"Files to resolve: {len(file_ids)}")
        print(f"Global chunk index entries: {global_chunk_index}")

        for file_id in file_ids:
            kwargs = await fetcher.fetch_for_file(file_id, global_chunk_index)
            print(
                f"\nfile_id={file_id}  "
                f"chunks={len(kwargs['chunks'])}  "
                f"raw_calls={len(kwargs['raw_calls'])}  "
                f"import_names={len(kwargs['import_names'])}  "
                f"import_map={len(kwargs['import_map'])}  "
                f"import_module_map={len(kwargs['import_module_map'])}  "
                f"external_lib_names={len(kwargs['external_lib_names'])}"
            )

    asyncio.run(main())