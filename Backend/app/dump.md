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