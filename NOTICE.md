# Source and rights

The six directories under `skills/` are the user's custom Codex skill sources,
published at the user's explicit request. Source files are preserved byte for byte;
`SOURCE_MANIFEST.json` records the relative path and SHA256 of each included file.
Version-control internals and Python caches are excluded. No account configuration,
credentials, model weights, private workspace data, or installed system skills are included.

No license file or license declaration was present in the imported skill sources.
This package does not invent a license grant for them or for external resources
linked from their documentation. Public availability alone is not an open-source
license. Linked websites and reference materials retain their owners' rights.

`runtime/workspace_mcp.py` is the companion workspace implementation prepared for
this user's local Strata integration. It is bundled to keep confined file access
self-contained. This project does not redistribute Strata or model weights.
The Docker image uses an existing, separately installed Strata tools image.
