# Context for function review
```json
{
  "query": "Review scan_project function",
  "target_function": {
    "name": "scan_project",
    "file": "scanner.py",
    "code": "...",
    "start_line": 12,
    "end_line": 58
  },
  "calls_out": [
    "calculate_hash",
    "parse_file",
    "store_embedding"
  ],
  "calls_in": [
    "main",
    "worker_thread"
  ],
  "imports": {
    "project": ["utils.parser", "db.storage"],
    "external": ["os", "logging"]
  },
  "related_functions": [
    {
      "name": "calculate_hash",
      "code": "..."
    }
  ],
  "embedding_similar": [
    "process_files",
    "scan_directory"
  ],
  "repo_stats": {
    "total_functions": 1240,
    "module": "scanner"
  }
}
```