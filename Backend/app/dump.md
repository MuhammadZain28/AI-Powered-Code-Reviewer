## Normalize of Imports (old code, not used anymore)
```python
    def normalize_import(self):
        if self.language == "java":
            self.normalize_java()
            self.normalize_cpp()
        elif self.language == "python":
            self.normalize_py()
        elif self.language in ["cpp", "c", "objective-c"]:
            self.normalize_cpp()
        elif self.language in ["javascript", "typescript"]:
            self.normalize_js()
        return {
            "type": self.type,
            "source": self.source,
            "modules": self.modules
        }

    def normalize_py(self):
        if self.raw_import.startswith("import "):
            self.type = "module"
            parts = self.raw_import.split("import ")[1].split(",")
            for part in parts:
                module_name = {}
                sub_parts = part.strip().split(" as")
                module_name["module"] = sub_parts[0].strip('(){} ')
                if len(sub_parts) > 1:
                    module_name["alias"] = sub_parts[1].strip()
                else:
                    module_name["alias"] = module_name["module"]
                self.modules.append(module_name)

        elif self.raw_import.startswith("from "):
            self.type = "module"
            parts = self.raw_import.split('from ')[1].split('import ')
            self.source = parts[0].strip()
            if len(parts) > 1:
                for part in parts[1].split(","):
                    module_name = {}
                    sub_parts = part.split(" as")
                    module_name["module"] = sub_parts[0].strip('(){} ')
                    if len(sub_parts) > 1:
                        module_name["alias"] = sub_parts[1].strip()
                    else:
                        module_name["alias"] = module_name["module"]
                    self.modules.append(module_name)

    def normalize_js(self):
        if self.raw_import.startswith("import "):
            self.type = "module"
            parts = self.raw_import.split('import ')[1].split(' from ')
            if len(parts) == 2:
                self.source = parts[1].strip('\'"')
                for part in parts[0].split(","):
                    sub_parts = part.strip().split(" as")
                    module_name = sub_parts[0].strip('(){} ')
                    if len(sub_parts) > 1:
                        self.modules.append({"module": module_name, "alias": sub_parts[1].strip()})
                    else:
                        self.modules.append({"module": module_name, "alias": module_name})

        elif self.raw_import.startswith("export "):
            self.type = "module"
            parts = self.raw_import.split('export ')[1].split(' from ')
            if len(parts) == 2:
                self.source = parts[1].strip('\'"')
                for part in parts[0].split(","):
                    sub_parts = part.strip().split(" as ")
                    module_name = sub_parts[0].strip('(){} ')
                    if len(sub_parts) > 1:
                        self.modules.append({"module": module_name, "alias": sub_parts[1].strip()})
                    else:
                        self.modules.append({"module": module_name, "alias": module_name})


        elif self.raw_import.startswith("const "):
            self.type = "module"
            parts = self.raw_import.split('require(')
            if len(parts) == 2:
                self.source = parts[1].strip('\'");')
                parts = parts[0].split('const ')[1].split('=')
                for part in parts[0].split(","):
                    module_name = part.strip('(){} ')
                    self.modules.append({"module": module_name, "alias": module_name})

    def normalize_java(self):
        if self.raw_import.startswith("import "):
            self.type = "module"
            parts = self.raw_import.split()
            if parts[1] == "static":
                self.type = "static"
                self.source = parts[2].strip('; ')
            else:
                self.source = parts[1].strip('; ')
            self.modules.append(self.source.split(".")[-1])

    def normalize_cpp(self):
        if self.raw_import.startswith("#include ") or self.raw_import.startswith("# include ") or self.raw_import.startswith("#import ") or self.raw_import.startswith("@import "):
            self.type = "module"
            parts = self.raw_import.split()
            self.source = parts[1].strip().strip('"<>')
```

```python
    async def parse_project(self, project_id: str) -> dict:
        vector = []
        ids = []
        start_time = time.time()
        parsed_data = self.parser_service.parse_project()

        for file_path, file_data in parsed_data.items():
            file = File(id=None, project_id=project_id, path=file_path, language=file_data['language'], hash=file_data['hash'])
            _ = await file.save()
            _, normalized_imports = await self.insert_import(file_data['imports'], file_data['language'], file.id)

            if file_data['classes']:
                for cls in file_data['classes']:
                    class_id = await self.insert_class({
                        'file_id': file.id,
                        'name': cls['name'],
                        'start_line': cls['start_line'],
                        'end_line': cls['end_line'],
                        'docstring': cls['docstring'],
                        'attributes': cls.get('attributes', []),
                        'inheritances': cls.get('inheritances', [])
                    })

                    for chunk in cls['chunks']:
                        chunk_id = await self.insert_chunk(chunk_data={
                            'file_id': file.id,
                            'chunk_type': chunk['type'],
                            'name': chunk['name'],
                            'start_line': chunk['start_line'],
                            'end_line': chunk['end_line'],
                            'content': chunk['content'],
                            'parameters': chunk.get('params', []),
                            'return_values': chunk.get('returns', []),
                            'complexity': chunk.get('complexity', {}),
                            'hash': chunk.get('hash', ""),
                            'docstring': chunk.get('docstring', ""),
                            'calls': chunk.get('calls', [])
                        }, class_id=class_id, imports=normalized_imports)
                        ids.append(chunk_id)

            else:
                for chunk in file_data['chunks']:
                    chunk_id = await self.insert_chunk(chunk_data={
                        'file_id': file.id,
                        'chunk_type': chunk['type'],
                        'name': chunk['name'],
                        'start_line': chunk['start_line'],
                        'end_line': chunk['end_line'],
                        'content': chunk['content'],
                        'parameters': chunk.get('params', []),
                        'return_values': chunk.get('returns', []),
                        'complexity': chunk.get('complexity', {}),
                        'hash': chunk.get('hash', ""),
                        'docstring': chunk.get('docstring', ""),
                        'calls': chunk.get('calls', [])
                    }, class_id=None, imports=normalized_imports)
                    ids.append(chunk_id)

            embeddings = self.embedding_service.embed_chunks(file_data['chunks'], file_data['language'], file=file_path)
            vector.extend(vector['vector'] for vector in embeddings)

        self.__logger.info(f"Processed file {file_path} with {len(vector)} vectors and {len(ids)} ids.")
        if len(vector) == len(ids) and len(vector) > 0:
            self.faiss_index.add_embeddings(vector, ids)

        end_time = time.time()
        self.__logger.info(f"Completed parsing project {project_id} in {end_time - start_time:.2f} seconds.")

        return parsed_data
```

### Insert Code for Bulk Data
```python
    async def insert_chunk(self, chunk_data: dict, class_id: int = None, imports: list = None):
        chunk = Chunk(
            id=None,
            file_id=chunk_data['file_id'],
            class_id=class_id,
            chunk_type=chunk_data['chunk_type'],
            name=chunk_data['name'],
            start_line=chunk_data['start_line'],
            end_line=chunk_data['end_line'],
            content=chunk_data['content'],
            parameters=chunk_data.get('parameters', []),
            return_values=chunk_data.get('return_values', []),
            complexity=chunk_data.get('complexity', {}),
            hash=chunk_data.get('hash', ""),
            docstring=chunk_data.get('docstring', ""),
            calls=chunk_data.get('calls', [])
        )
        await chunk.save(imports=imports)
        self.__logger.info(f"Inserted new chunk {chunk.name} with ID {chunk.id} into FAISS index.")
        return chunk.id

    async def insert_class(self, class_data: dict):
        class_chunk = Class(
            id=None,
            file_id=class_data['file_id'],
            name=class_data['name'],
            start_line=class_data['start_line'],
            end_line=class_data['end_line'],
            docstring=class_data['docstring'],
            attributes=class_data.get('attributes', []),
            inheritances=class_data.get('inheritances', [])
        )
        await class_chunk.save()
        self.__logger.info(f"Inserted new class {class_chunk.name} with ID {class_chunk.id} into FAISS index.")
        return class_chunk.id

    async def insert_import(self, imports: list, language: str, file_id: str):
        import_chunk = Import(file_id=file_id)
        normalized_imports = []
        for import_statement in imports:
            normalized = normalize(import_statement, language)
            import_chunk.type = normalized.type
            import_chunk.source = normalized.source
            import_chunk.modules = normalized.modules
            import_chunk.aliases = normalized.aliases
            _ = await import_chunk.save()
            normalized_imports.append(normalized.to_dict())
            self.__logger.info(f"Inserted new import {import_chunk.modules} with ID {import_chunk.id} into FAISS index.")
        return import_chunk.id, normalized_imports
```

Here's a thinking process:\n\n1.  **Analyze User Input:**\n   - **Input Code:** `def k_rotate(arr, k):\\n    n = len(arr)\\n    k = k % n\\n    return arr[k:] + arr[:k]`\n   - **Context:** Python function for rotating an array/list by `k` positions.\n   - **Metadata:** File path, function name, parameters, return values, metrics (fan_in/out = 0), no imports, no docstring.\n   - **Task:** Review the code chunk in the context of a project (though only one chunk is provided), following specific guidelines (architectural impact, interactions, module responsibilities, performance, maintainability, security, readability, naming, consistency). Output valid JSON only with specific fields for each issue.\n\n2.  **Evaluate the Code:**\n   - *Functionality:* Rotates a list `arr` to the right by `k` positions. Wait, let's verify: `arr[k:] + arr[:k]` actually rotates to the *left* by `k`. If `arr = [1,2,3,4,5]`, `k=2`, `arr[2:]` is `[3,4,5]`, `arr[:2]` is `[1,2]`, result `[3,4,5,1,2]`. That's a left rotation. The name `k_rotate` is ambiguous but often implies right rotation in competitive programming contexts. I should note this potential semantic mismatch.\n   - *Edge Cases:* What if `arr` is empty? `n = len(arr)` -> `n=0`. `k % n` will raise `ZeroDivisionError`. This is a critical bug.\n   - *Performance:* Slicing creates new lists. Time complexity O(n), Space complexity O(n). This is standard for Python lists. If `arr` is huge, it might be memory intensive, but acceptable for typical use. Could mention in-place rotation for performance/memory optimization if needed, but slicing is Pythonic.\n   - *Type Hints/Docstring:* Missing. Affects maintainability/readability.\n   - *Naming:* `k_rotate` is okay, but `rotate_left` or `rotate_right` would be clearer. `arr` and `k` are standard.\n   - *Security:* No direct security issues, but unvalidated input could cause crashes.\n   - *Architecture/Context:* Standalone function. No external calls. Fan-in/out 0.\n\n3.  **Identify Issues & Map to Guidelines:**\n   - **Issue 1: ZeroDivisionError on empty list**\n     - Severity: Critical\n     - Category: Bug\n     - Location: Line 2 (`k = k % n`)\n     - Explanation: If `arr` is empty, `n` becomes 0, causing `ZeroDivisionError` when computing `k % n`.\n     - Suggested Fix: Add a guard clause: `if not arr: return arr[:]` or `if n == 0: return arr`\n   - **Issue 2: Ambiguous Rotation Direction**\n     - Severity: Medium\n     - Category: Readability / Maintainability\n     - Location: Function signature & body\n     - Explanation: The implementation performs a left rotation, but the name `k_rotate` doesn't specify direction. This can lead to misuse.\n     - Suggested Fix: Rename to `rotate_left` or add a docstring clarifying the direction. Consider adding a `direction` parameter if right rotation is also needed.\n   - **Issue 3: Missing Type Hints and Docstring**\n     - Severity: Low\n     - Category: Maintainability / Readability\n     - Location: Function definition\n     - Explanation: Lack of type hints and documentation reduces code clarity and IDE support.\n     - Suggested Fix: Add type hints (`def k_rotate(arr: list, k: int) -> list:`) and a docstring explaining parameters, return value, and behavior.\n   - **Issue 4: Memory/Performance for Large Lists**\n     - Severity: Low\n     - Category: Performance\n     - Location: Return statement (`return arr[k:] + arr[:k]`)\n     - Explanation: Slicing creates two new lists and concatenates them, resulting in O(n) additional memory. For very large arrays, this may be inefficient.\n     - Suggested Fix: If memory is a constraint, consider using `collections.deque` with `rotate()` or an in-place reversal algorithm. Otherwise, note it in documentation.\n\n4.  **Structure Output as JSON:**\n   Need to format exactly as requested. The prompt says \"Output valid JSON only.\" and gives a structure for each issue. I'll create a JSON array of issues or a JSON object containing an \"issues\" array. I'll stick to a clean structure.\n\n   Let's draft the JSON:\n   ```json\n   {\n     \"issues\": [\n       {\n         \"severity\": \"Critical\",\n         \"category\": \"Bug\",\n         \"location\": \"Line 2: k = k % n\",\n         \"explanation\": \"If the input list `arr` is empty, `n` becomes 0. The modulo operation `k % n` will raise a `ZeroDivisionError`, crashing the program.\",\n         \"suggested_fix\": \"Add a guard clause to handle empty lists: `if not arr: return arr[:]` or `if n == 0: return arr` before the modulo operation.\"\n       },\n       {\n         \"severity\": \"Medium\",\n         \"category\": \"Readability\",\n         \"location\": \"Function signature and body\",\n         \"explanation\": \"The function performs a left rotation, but the name `k_rotate` does not specify the direction. This ambiguity can lead to incorrect usage by callers expecting a right rotation.\",\n         \"suggested_fix\": \"Rename the function to `rotate_left` or add a clear docstring specifying the rotation direction. Consider adding a `direction` parameter if both left and right rotations are needed.\"\n       },\n       {\n         \"severity\": \"Low\",\n         \"category\": \"Maintainability\",\n         \"location\": \"Function definition\",\n         \"explanation\": \"The function lacks type hints and a docstring, which reduces code clarity, hinders static analysis, and limits IDE autocomplete support.\",\n         \"suggested_fix\": \"Add type hints and a docstring: `def rotate_left(arr: list, k: int) -> list:` followed by a docstring explaining parameters, return value, and edge cases.\"\n       },\n       {\n         \"severity\": \"Low\",\n         \"category\": \"Performance\",\n         \"location\": \"Return statement: return arr[k:] + arr[:k]\",\n         \"explanation\": \"List slicing and concatenation create new list objects, resulting in O(n) additional memory usage. This may be inefficient for very large arrays.\",\n         \"suggested_fix\": \"For memory-constrained environments, consider using `collections.deque(arr).rotate(-k)` or an in-place reversal algorithm. Otherwise, document the O(n) space complexity.\"\n       }\n     ]\n   }\n   ```\n\n5.  **Self-Correction/Verification against constraints:**\n   - *Architectural impact:* Noted in performance/maintainability.\n   - *Interactions:* Fan-in/out is 0, so it's isolated. Noted.\n   - *Module responsibilities:* It's a utility function. Clear.\n   - *Performance:* Addressed.\n   - *Maintainability:* Addressed.\n   - *Security:* No direct issues, but crash on empty input is a DoS vector in some contexts. I'll stick to Bug.\n   - *Readability/Naming:* Addressed.\n   - *Avoid conflicting patterns:* Pythonic slicing is standard, so I won't force in-place unless necessary. I'll frame it as a suggestion.\n   - *JSON format:* Valid. Matches requested fields.\n   - *Check logic:* `arr[k:] + arr[:k]` is indeed left rotation. If `k` is negative, Python handles it, but `k % n` makes it positive. So it's strictly left rotation by `k % n`. Correct.\n   - *ZeroDivisionError:* Definitely critical.\n   - *Structure:* I'll output exactly the JSON structure requested. The prompt says \"For each issue provide: Severity, Category, Location, Explanation, Suggested Fix\". I'll wrap them in a list under an \"issues\" key for valid JSON.\n\n   One minor thing: The prompt says \"Output valid JSON only.\" I will ensure no markdown formatting interferes, or I'll use standard markdown code blocks but the content will be pure JSON. I'll output raw JSON to be safe.\n\n   Let's verify the exact field names requested:\n   - Severity\n   - Category\n   - Location\n   - Explanation\n   - Suggested Fix\n\n   I'll map them exactly.\n\n   Draft:\n   ```json\n   [\n     {\n       \"Severity\": \"Critical\",\n       \"Category\": \"Bug\",\n       \"Location\": \"Line 2: k = k % n\",\n       \"Explanation\": \"If the input list `arr` is empty, `n` evaluates to 0. The modulo operation `k % n`