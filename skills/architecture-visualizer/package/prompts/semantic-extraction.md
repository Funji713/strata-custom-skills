# Semantic Extraction Prompt

Extract facts before building diagrams.

For every important fact:
- identify subject, relation, and object;
- assign relation mode when meaningful;
- attach evidence immediately;
- classify evidence level as `verified`, `supported`, `inferred`, or `uncertain`;
- never use a fake numeric confidence score;
- never serialize secret values.

Then build CSM entities and relations using stable IDs. Keep static dependency distinct from runtime invocation. Symbols are analysis units, not automatic diagram nodes. Unknown remains unknown.
