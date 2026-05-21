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