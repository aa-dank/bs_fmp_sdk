# AGENTS.md
This repository is intended to become the canonical Python SDK for interacting with the UCSC Business Services FileMaker system.

## Repository goals
- Centralize FileMaker integration code that is currently spread across multiple projects.
- Provide a low-level API layer that can be used directly for quick scripts and notebooks.
- Provide a higher-level UCSC-specific business layer for operations that recur across projects.
- Keep the supported surface intentionally small and driven by immediate real use cases.

## Current design direction
- Favor a relatively flat project structure over a deeply nested package tree.
- Use the hardened low-level wrapper approach from `project_sync_service` as the primary reference for connection handling, retries, and exception design.
- Keep business logic more portable than a large multi-package architecture would be, while still separating it from the raw API layer.
- Prefer plain Python dicts and lightweight types in the core API. Avoid a pandas dependency in the transport layer.

## Initial scope
Implement only the functionality needed immediately or in near-term downstream projects:
- Projects
- Contracts
- Submittals
- RFIs

Out of scope for now:
- Broad schema coverage
- FileMaker script execution helpers
- Exhaustive table/layout support
- SQL-through-FileMaker helpers

## FileMaker layout guidance
- The `Import*` layouts are the preferred layouts for requests.
- These import layouts are expected to be close to 1:1 with their corresponding tables.
- Very rarely should other layouts be used.
- Treat layout names as centralized constants so downstream projects benefit from updates made here.
- Remember that `fmrest.Server` has both a default layout and method-level layout overrides; do not assume the server instance layout must be the only layout used for a session.

## Architecture preference
When choosing between elegance and portability, prefer the version that is easier to lift into a notebook or a small standalone script.

That suggests a shape closer to:
- one raw/core client module
- one exceptions module
- one config module
- one layout/constants module
- one business/domain module, or at most a very small number of domain modules

Avoid introducing many nested folders unless they clearly pay for themselves.

## Documentation and research notes
- Keep a `research/` directory with focused markdown notes that help future development.
- Do not try to mirror the full FileMaker design report there.
- Prefer concise notes about supported layouts, source projects, field conventions, and known constraints.
- If a note becomes obsolete, update it rather than accumulating conflicting guidance.

## Development workflow
- Use `uv` for project setup and dependency management.
- Keep the virtual environment and package metadata current.
- Add typed exceptions early.
- Prefer tests around behavior that is easy to break:
  - retry/login behavior
  - token expiration handling
  - layout switching behavior
  - record lookup/update helpers

## Source projects worth consulting
- `\\wsl.localhost\Ubuntu-22.04\home\projects\project_sync_service\src\project_sync_service`
- `\\wsl.localhost\Ubuntu-22.04\home\projects\constdoc_app\constdoc_app`
- `\\wsl.localhost\Ubuntu-22.04\home\projects\archives_app\archives_application`
- `C:\Users\adankert\projects\filemaker_automation`

## Database design report notes
- The design report is large and contains vestigial material.
- Avoid reading the giant main HTML file wholesale unless absolutely necessary.
- Prefer targeted inspection of known layouts, tables, and small entry-point files.
