# Architecture: Strata custom skills, spec 1

Authority: user requested packaging, GitHub publication and local Docker installation;
public destination Funji713/strata-custom-skills explicitly selected. Risk R1 integration.

Existing Strata offers stdio MCP to opt-in chat requests. The package adds one independent
MCP server, leaving all tracked Strata engine/server files unchanged. Four tools expose
read-only skill discovery and paginated source loading, an advisory policy classifier,
and deterministic architecture artifact generation. Existing workspace MCP retains
file editing and basic PPTX production. Original skill text is an archive; the runtime
contract specifies actual Strata capabilities and allowed adaptations.

The package owns its runtime and copied skill resources. User files belong to /workspace.
Descriptor-based reads reject traversal, symlinks, hardlinks and devices. Architecture
inputs are explicit files copied into a private temporary snapshot; source code is never
executed. Outputs use generated workspace directories and atomic create-only writes.
No external network or model API, generic command runner, credentials or model data.

Acceptance: AC1 all six sources/resources retained with hashes and paginated load;
AC2 deny unsafe paths and unsupported arguments; AC3 actual bundled architecture output
and policy classification; AC4 Docker MCP ready and a live model skill tool invocation;
AC5 public source audit and push to the user-selected repository.

One implementation slice owns package/runtime, source import and installation. Validation
uses focused unit/wire tests, original executable-asset suites and actual Strata request.
Rollback removes only skills MCP entry and restores prior image/build configuration.
No GPU backend source changes; CUDA/HIP/SYCL rebuilds are not applicable.
