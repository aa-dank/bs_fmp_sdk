# Architecture notes
## Working architectural preference
The current preference is for a flat and portable SDK rather than a deeply nested package.

The main tradeoff under discussion is:
- flatter structure and easier portability into notebooks/scripts
- versus more modular domain-specific subpackages

Current lean:
- keep the number of files small
- keep the raw API layer usable on its own
- keep business logic separate, but not necessarily spread across many directories

## Proposed shape
One likely early shape is:
- `config.py`
- `exceptions.py`
- `layouts.py`
- `client.py` for raw FileMaker operations
- `business.py` for UCSC-specific higher-level operations

Possible refinement if `business.py` grows too large:
- `projects.py`
- `contracts.py`
- `submittals.py`
- `rfis.py`

That split should only happen if the single-file business layer starts to become awkward.

## Layering
### Raw/core layer
Responsible for:
- authentication
- retries
- token refresh behavior
- default layout handling
- method-level layout overrides
- returning plain Python data
- raising typed exceptions

### Business layer
Responsible for:
- project-specific lookup helpers
- create/update flows for supported entities
- opinionated convenience methods used by downstream apps

### CLI/tooling layer
The SDK now includes a small JSON CLI wrapper in `bs_fmp_sdk/cli.py`.

Purpose:
- give Codex and local scripts a deterministic command surface
- keep FileMaker access routed through the SDK instead of ad hoc scripts
- make dry-run write previews easy before any live mutation
- return structured JSON for both success and failure

Current command families:
- connectivity: `ping`
- lookups: `find-projects`, `get-project`, `find-contracts`, `find-rfis`
- writes: `create-rfi`, `create-rfi-for-project`

Design notes:
- dry-run write previews should not require credentials
- committed writes and live lookups should load normal `.env` config
- commands should remain thin wrappers around SDK methods, not a second business layer
- future Codex MCP/plugin tools can wrap this CLI or import the SDK directly

### Codex skill layer
A local Codex skill named `bs-filemaker` documents how agents should use this SDK, where the DDR/reference files live, and what approval rules apply before FileMaker writes.

Keep durable domain semantics in this repo first. The skill should point back here rather than becoming a competing source of truth.

## Things to avoid early
- exhaustive schema modeling
- code generation from the full design report
- FileMaker script helpers as a central design feature
- large dependency footprint
- premature abstraction for unsupported entities
