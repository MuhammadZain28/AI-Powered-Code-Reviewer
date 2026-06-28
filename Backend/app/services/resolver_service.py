from app.call_graph_resolver import CallGraphResolver
from app.managers.call_graph import CallGraphDBFetcher

async def resolve_call_graph():
    data = await CallGraphDBFetcher(project_id="13931f2a-a817-4ada-9d21-f4f4164ad1c8").fetch()
    return CallGraphResolver(
        chunks=data['chunks'],
        raw_calls=data['raw_calls'],
        import_names=data['import_names'],
        import_map=data['import_map'],
        import_module_map=data['import_module_map'],
        global_chunk_index=data['global_chunk_index'],
        external_lib_names=data['external_lib_names'],
        use_stdlib_detection=True,
    )

if __name__ == "__main__":
    import asyncio
    resolver = asyncio.run(resolve_call_graph())
    result = resolver.resolve()
    print(result.stats())