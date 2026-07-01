import json
from app.call_graph_resolver import CallGraphResolver
from app.managers.call_graph import CallGraphDBFetcher

async def resolve_call_graph():
    fetcher = CallGraphDBFetcher(project_id="ad124d38-5776-42b4-8fa3-b10648a6b901")

    file_ids           = await fetcher.fetch_file_ids()
    global_chunk_index = await fetcher.fetch_global_chunk_index()

    print(f"Files to resolve: {len(file_ids)}, global index entries: {len(global_chunk_index)}")

    results = []
    for file_id in file_ids:
        kwargs   = await fetcher.fetch_for_file(file_id, global_chunk_index)
        resolver = CallGraphResolver(**kwargs, use_stdlib_detection=True)
        result   = resolver.resolve()
        results.extend(result.to_record_list())


    # await fetcher.copy_resolved_calls_to_database(results)

    return results

if __name__ == "__main__":
    import asyncio
    asyncio.run(resolve_call_graph())