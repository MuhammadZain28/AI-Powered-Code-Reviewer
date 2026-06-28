"""
Call Graph DB Fetcher
=====================
Responsible for one thing: fetching and shaping raw database rows into the
exact structures that CallGraphResolver expects.

No resolution logic lives here — this module is purely a data-access layer.

Schema assumptions
------------------
  functions        → id, file_id, class_id, name, start_line, end_line, content, signature, ...
  imports          → id, file_id, from_module, type, is_external
  import_symbols   → id, import_id, symbol, alias, is_used
  call_graph       → id, caller_id, callee_id, function_name, call_type, call_line, library, resolved_path
  classes          → id, file_id, name, start_line, end_line, is_abstract, inheritances

All queries accept an asyncpg Connection / Pool (or any object exposing
.fetch() / .fetchrow()). Swap for psycopg3 or SQLAlchemy Core by replacing
the thin `_fetch` / `_fetchrow` wrappers at the bottom of the file.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from app.managers.database import Database

logger = logging.getLogger(__name__)



# ---------------------------------------------------------------------------
# Public data-class-style containers (plain dicts kept for resolver compat)
# ---------------------------------------------------------------------------

class CallGraphData:
    """
    All data required to run CallGraphResolver for a single file.

    Attributes mirror CallGraphResolver.__init__ parameters exactly so the
    service can splat (**) this object's dict representation directly.
    """
    __slots__ = (
        "project_id",
        "chunks",
        "raw_calls",
        "import_names",
        "import_map",
        "import_module_map",
        "global_chunk_index",
        "external_lib_names",
    )

    def __init__(
        self,
        project_id:         str,
        chunks:             list[dict[str, Any]],
        raw_calls:          list[dict[str, Any]],
        import_names:       set[str],
        import_map:         dict[str, str],
        import_module_map:  dict[str, str],
        global_chunk_index: dict[tuple[str, str], list[str]],
        external_lib_names: set[str],
    ) -> None:
        self.project_id         = project_id
        self.chunks             = chunks
        self.raw_calls          = raw_calls
        self.import_names       = import_names
        self.import_map         = import_map
        self.import_module_map  = import_module_map
        self.global_chunk_index = global_chunk_index
        self.external_lib_names = external_lib_names

    def resolver_kwargs(self) -> dict[str, Any]:
        """Return kwargs ready to splat into CallGraphResolver(**...)."""
        return {
            "chunks":             self.chunks,
            "raw_calls":          self.raw_calls,
            "import_names":       self.import_names,
            "import_map":         self.import_map,
            "import_module_map":  self.import_module_map,
            "global_chunk_index": self.global_chunk_index,
            "external_lib_names": self.external_lib_names,
        }


# ---------------------------------------------------------------------------
# Main fetcher
# ---------------------------------------------------------------------------

class CallGraphDBFetcher:

    def __init__(self, project_id: str) -> None:
        self._project_id = project_id
        self.db = Database()

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    async def fetch(self) -> CallGraphData:
        """
        Fetch all resolver inputs for *project_id* in parallel logical groups.

        Returns a CallGraphData ready for CallGraphResolver(**data.resolver_kwargs()).
        """
        logger.info("CallGraphDBFetcher: fetching data for Project=%s", self._project_id)

        chunks             = await self._fetch_chunks()
        raw_calls          = await self._fetch_raw_calls(chunks)
        import_names, import_map, import_module_map, external_lib_names =  await self._fetch_import_data()
        global_chunk_index = await self._fetch_global_chunk_index()

        logger.info(
            "CallGraphDBFetcher done: chunks=%d, raw_calls=%d, imports=%d, "
            "global_index_entries=%d",
            len(chunks), len(raw_calls), len(import_names), len(global_chunk_index),
        )

        return CallGraphData(
            project_id         = self._project_id,
            chunks             = chunks,
            raw_calls          = raw_calls,
            import_names       = import_names,
            import_map         = import_map,
            import_module_map  = import_module_map,
            global_chunk_index = global_chunk_index,
            external_lib_names = external_lib_names,
        ).resolver_kwargs()

    # ------------------------------------------------------------------
    # Stage fetchers
    # ------------------------------------------------------------------

    async def _fetch_chunks(self) -> list[dict[str, Any]]:
        rows = await self.db.fetch(
            """
            SELECT
                f.id::text          AS id,
                f.name,
                f.file_id::text     AS file_id,
                f.start_line        AS start,
                f.end_line          AS end,
                f.class_id::text    AS class_id
            FROM functions f JOIN files fi ON fi.id = f.file_id
            WHERE fi.project_id = $1::uuid
            ORDER BY f.start_line
            """,
            self._project_id,
        )

        chunks = [dict(r) for r in rows]

        if not chunks:
            logger.warning("No functions found for project_id=%s", self._project_id)

        return chunks

    async def _fetch_raw_calls(self, chunks:  list[dict[str, Any]]) -> list[dict[str, Any]]:

        if not chunks:
            return []

        chunk_ids = [c["id"] for c in chunks]

        rows = await self.db.fetch(
            """
            SELECT
                cg.caller_id::text  AS caller_id,
                cg.function_name,
                cg.call_line
            FROM call_graph cg
            WHERE cg.caller_id = ANY($1::uuid[])
              AND cg.callee_id IS NULL
            ORDER BY cg.call_line
            """,
            chunk_ids,
        )

        return [dict(r) for r in rows]

    async def _fetch_import_data(self) -> tuple[set[str], dict[str, str], dict[str, str], set[str]]:
        rows = await self.db.fetch(
            """
            SELECT
                i.id::text          AS import_id,
                i.from_module,
                i.type,
                i.is_external,
                s.symbol,
                s.alias,
                s.is_used
            FROM imports i
            LEFT JOIN import_symbols s ON s.import_id = i.id
            JOIN files f ON f.id = i.file_id
            WHERE f.project_id = $1::uuid
            ORDER BY i.id
            """,
            self._project_id,
        )

        import_names:      set[str]        = set()
        import_map:        dict[str, str]  = {}
        import_module_map: dict[str, str]  = {}
        external_lib_names: set[str]       = set()

        for row in rows:
            from_module   = row["from_module"] or ""
            is_external   = row["is_external"]
            symbol        = row["symbol"]
            alias         = row["alias"]

            effective_name: str | None = alias or symbol or from_module

            if not effective_name:
                continue

            import_names.add(effective_name)

            if is_external:
                lib_root = from_module or effective_name
                import_module_map[effective_name] = lib_root
                external_lib_names.add(lib_root)

            else:
                import_map[effective_name] = from_module  # placeholder

        if import_map:
            import_map = await self._resolve_internal_file_ids(import_map)

        return import_names, import_map, import_module_map, external_lib_names

    async def _resolve_internal_file_ids(self, name_to_module: dict[str, str]) -> dict[str, str]:

        unique_modules = list({v for v in name_to_module.values() if v})

        if not unique_modules:
            return {}

        rows = await self.db.fetch(
            """
            SELECT
                f.id::text  AS file_id,
                f.path      AS module_path
            FROM files f
            WHERE f.project_id = $1::uuid
            """,
            self._project_id,
            unique_modules,
        )

        module_to_file_id: dict[str, str] = {r["module_path"]: r["file_id"] for r in rows}

        resolved: dict[str, str] = {}
        for name, module_path in name_to_module.items():
            file_id = module_to_file_id.get(module_path)
            if file_id:
                resolved[name] = file_id
            else:
                logger.debug(
                    "Could not resolve internal module '%s' to a file_id — skipping.",
                    module_path,
                )

        return resolved

    async def _fetch_global_chunk_index(self) -> dict[tuple[str, str], list[str]]:
        rows = await self.db.fetch(
            """
            SELECT
                f.id::text      AS chunk_id,
                f.file_id::text AS file_id,
                f.name          AS function_name
            FROM functions f
            JOIN files fi ON fi.id = f.file_id
            WHERE fi.project_id = $1::uuid
            ORDER BY f.file_id, f.name
            """,
            self._project_id,
        )

        index: dict[tuple[str, str], list[str]] = {}
        for row in rows:
            key = (row["file_id"], row["function_name"])
            index.setdefault(key, []).append(row["chunk_id"])

        return index


if __name__ == "__main__":
    import asyncio

    async def main():
        fetcher = CallGraphDBFetcher(project_id="4c8ef3d9-1372-4dd4-9aa6-944e4d33fa28")
        data = await fetcher.fetch()
        print(json.dumps(data.resolver_kwargs(), indent=2))

    asyncio.run(main())