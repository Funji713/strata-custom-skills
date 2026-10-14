# Repository Discovery Prompt

Goal: build a source index without prematurely inventing architecture.

1. Inspect the project tree and manifests first.
2. Detect languages, frameworks, candidate entry points, and likely subsystems.
3. Identify high-priority paths for focused analysis.
4. Deprioritize generated/vendor/build artifacts.
5. Treat tests and README as supporting evidence, not architectural truth by default.
6. Detect secret-bearing files such as `.env`; record key names only and redact values.
7. For monorepos, establish subsystem boundaries before deep reading.
8. Output only fields valid under `source-index.schema.json`.
9. Do not infer services, databases, or external systems without evidence.
