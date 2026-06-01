### Trigger For Internal Methods
```sql
CREATE SCHEMA "public";
CREATE SCHEMA "auth";
CREATE SCHEMA "pgrst";
CREATE TABLE "calls" (
	"id" bigserial PRIMARY KEY,
	"caller_id" bigint NOT NULL UNIQUE,
	"function_name" text UNIQUE,
	"call_type" varchar(50),
	"created_at" timestamp DEFAULT now(),
	"resolve_to" text,
	"library" text,
	CONSTRAINT "unique_calls" UNIQUE("caller_id","function_name")
);
CREATE TABLE "chunks" (
	"id" bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY (sequence name "chunks_id_seq" INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START WITH 1 CACHE 1),
	"chunk_type" text,
	"name" text,
	"start_line" integer,
	"end_line" integer,
	"content" text,
	"created_at" timestamp DEFAULT now(),
	"docstring" text,
	"parameters" text[],
	"return_values" text[],
	"complexity" jsonb,
	"class_id" bigint,
	"file_id" uuid,
	"hash" text
);
CREATE TABLE "class_attributes" (
	"id" bigserial PRIMARY KEY,
	"class_id" bigint NOT NULL,
	"name" text NOT NULL,
	"attribute_type" text,
	"default_value" text,
	"is_static" boolean DEFAULT false,
	"created_at" timestamp DEFAULT now()
);
CREATE TABLE "classes" (
	"id" bigserial PRIMARY KEY,
	"file_id" uuid NOT NULL,
	"name" text NOT NULL,
	"start_line" integer,
	"end_line" integer,
	"docstring" text,
	"inheritance" text[],
	"created_at" timestamp DEFAULT now()
);
CREATE TABLE "files" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"project_id" uuid,
	"path" text NOT NULL,
	"language" text,
	"hash" text,
	"created_at" timestamp DEFAULT now(),
	"import_id" bigserial
);
CREATE TABLE "imports" (
	"id" bigserial PRIMARY KEY,
	"type" varchar(50),
	"created_at" timestamp DEFAULT now(),
	"modules" text[] UNIQUE,
	"source" text UNIQUE,
	"aliases" text[],
	CONSTRAINT "unique_imports" UNIQUE("source","modules")
);
CREATE TABLE "projects" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"name" text NOT NULL,
	"created_at" timestamp DEFAULT now(),
	"path" text,
	"description" text
);
CREATE UNIQUE INDEX "calls_pkey" ON "calls" ("id");
CREATE INDEX "idx_calls_caller" ON "calls" ("caller_id");
CREATE INDEX "idx_calls_function" ON "calls" ("function_name");
CREATE UNIQUE INDEX "unique_calls" ON "calls" ("caller_id","function_name");
CREATE UNIQUE INDEX "chunks_pkey" ON "chunks" ("id");
CREATE INDEX "idx_chunks_class" ON "chunks" ("class_id");
CREATE INDEX "idx_chunks_file" ON "chunks" ("file_id");
CREATE INDEX "idx_chunks_name" ON "chunks" ("name");
CREATE UNIQUE INDEX "class_attributes_pkey" ON "class_attributes" ("id");
CREATE UNIQUE INDEX "classes_pkey" ON "classes" ("id");
CREATE INDEX "idx_classes_file" ON "classes" ("file_id");
CREATE UNIQUE INDEX "files_pkey" ON "files" ("id");
CREATE UNIQUE INDEX "imports_pkey" ON "imports" ("id");
CREATE UNIQUE INDEX "unique_imports" ON "imports" ("source","modules");
CREATE UNIQUE INDEX "projects_pkey" ON "projects" ("id");
ALTER TABLE "calls" ADD CONSTRAINT "calls_caller_chunk_id_fkey" FOREIGN KEY ("caller_id") REFERENCES "chunks"("id") ON DELETE CASCADE;
ALTER TABLE "chunks" ADD CONSTRAINT "fk_chunks_classes" FOREIGN KEY ("class_id") REFERENCES "classes"("id") ON DELETE CASCADE;
ALTER TABLE "chunks" ADD CONSTRAINT "fk_files" FOREIGN KEY ("file_id") REFERENCES "files"("id") ON DELETE CASCADE;
ALTER TABLE "class_attributes" ADD CONSTRAINT "class_attributes_class_id_fkey" FOREIGN KEY ("class_id") REFERENCES "classes"("id") ON DELETE CASCADE;
ALTER TABLE "classes" ADD CONSTRAINT "classes_file_id_fkey" FOREIGN KEY ("file_id") REFERENCES "files"("id");
ALTER TABLE "classes" ADD CONSTRAINT "fk_constraint" FOREIGN KEY ("file_id") REFERENCES "files"("id") ON DELETE CASCADE;
ALTER TABLE "files" ADD CONSTRAINT "files_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "projects"("id") ON DELETE CASCADE;
ALTER TABLE "files" ADD CONSTRAINT "import_fk_constraint" FOREIGN KEY ("import_id") REFERENCES "imports"("id") ON DELETE SET NULL;
```