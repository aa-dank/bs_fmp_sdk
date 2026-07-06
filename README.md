# bs_fmp_sdk
Canonical Python SDK for interacting with the UCSC Business Services FileMaker system.

## Purpose
This repository is intended to centralize FileMaker integration code that has been drifting across multiple projects.

The current direction is:
- keep the package structure relatively flat
- provide a raw low-level FileMaker client that is useful by itself
- provide a higher-level business client for recurring UCSC-specific workflows
- implement only the functionality that is immediately useful in active projects

Initial supported focus:
- projects
- contracts
- RFIs
- CAANs
- submittals will follow next

## Installation
This project is set up for `uv`.

```powershell path=null start=null
uv sync --group notebooks
```

That creates a local `.venv` and installs:
- the package itself
- `python-fmrest` for FileMaker access
- `python-dotenv` for local environment loading
- notebook support for experimentation

## Credentials and local setup
Do not commit FileMaker credentials to this repository.

Create a local `.env` file at the repo root using `.env.example` as a template:

```powershell path=null start=null
Copy-Item .env.example .env
```

Expected environment variables:
- `FM_HOST`
- `FM_USER`
- `FM_PASSWORD`
- `FM_DATABASE`
- `FM_API_VERSION`
- `FM_VERIFY_SSL`
- `FM_TIMEOUT`
- `FM_FETCH_LIMIT`
- `FM_DEFAULT_LAYOUT`

Important dependency note:
- install package name: `python-fmrest`
- import name in code: `fmrest`

## Notebooks
Use `notebooks/` for shared experiments and examples.

Use `notebooks/local/` for personal scratch notebooks; it is ignored by Git.

The repo is configured so notebooks and local scripts can use a local `.env` file without exposing secrets in the public repository.

## Current package layout
- `bs_fmp_sdk/client.py`
  - low-level FileMaker client
- `bs_fmp_sdk/business.py`
  - higher-level business client
- `bs_fmp_sdk/config.py`
  - environment-backed config loading
- `bs_fmp_sdk/exceptions.py`
  - typed exceptions
- `bs_fmp_sdk/layouts.py`
  - centralized layout and field constants

## Public API
Main exports:

```python path=null start=null
from bs_fmp_sdk import (
    BusinessServicesFileMakerClient,
    FileMakerClient,
    FileMakerConfig,
    load_config,
    Layouts,
    CAANFields,
    ProjectFields,
    ContractFields,
    RFIFields,
)
```

### Low-level client
The low-level client is intended to be useful directly in scripts and notebooks.

Example:

```python path=null start=null
from bs_fmp_sdk import FileMakerClient, load_config, Layouts

config = load_config()
client = FileMakerClient(config)

projects = client.find_matching(
    {\"ProjectNumber\": \"1234\"},
    layout_name=Layouts.PROJECTS,
)
```

Available low-level methods currently include:
- `get_records(...)`
- `find(...)`
- `get_record(...)`
- `create_record(...)`
- `edit_record(...)`
- `find_matching(...)`
- `build_exact_query(...)`

### Higher-level business client
The business client builds on the raw client and exposes reusable public lookup methods, not just hidden internal workflow helpers.

Example:

```python path=null start=null
from bs_fmp_sdk import BusinessServicesFileMakerClient, FileMakerClient, load_config

config = load_config()
raw_client = FileMakerClient(config)
sdk = BusinessServicesFileMakerClient(raw_client)

project = sdk.get_project(project_number=\"1234\")
contract = sdk.get_contract_for_project(project=project)
rfis = sdk.find_rfis(contract_id_primary=contract[\"id_primary\"])
caans = sdk.search_caans(\"classroom\")
```

Current business methods include:
- `find_projects(...)`
- `get_project(...)`
- `find_contracts(...)`
- `get_contract(...)`
- `get_contract_for_project(...)`
- `resolve_project_contract_context(...)`
- `find_rfis(...)`
- `get_rfi(...)`
- `recent_rfis_for_contract(...)`
- `find_caans(...)`
- `get_caan(...)`
- `search_caans(...)`
- `create_rfi(...)`
- `preview_rfi_for_project(...)`
- `create_rfi_for_project(...)`
- `extract_spec_section(...)`

## Current business semantics
Some FileMaker field names are legacy or misleading. For the immediate first pass of this SDK, use these interpretations:

- `Contracts::ProjectNumber_lk`
  - treat this as the effective contract number for current business use
- `Contracts::ContractNumber`
  - do not currently treat this as the canonical business-facing contract number
- `Submittal::SectionNumber`
  - think of this as the \"Spec Section\"
- `SubmittalItems::SubmittalItemNumber`
  - think of this as the business-facing \"Submittal Number\"

Additional first-pass assumptions:
- project lookup is primarily by `ProjectNumber`
- if duplicate project numbers exist, `ProjectName` may be used as an additional filter
- there should be a single relevant contract per project for current workflows
- if multiple contracts are found for a project in a single-contract workflow, the SDK should raise an error
- RFIs are unique by `ID_Contracts` + `RFINumber`
- CAAN exact lookup is by `CAANs::CAAN`; text search checks `CAANs::Name` and `CAANs::Description`
- higher-level business methods return normalized snake_case keys and include the original FileMaker record under `raw_fields`

## Current workflow example
The initial RFI workflow reflects the real relationship chain in the FileMaker app:

1. resolve a single project
2. resolve the single associated contract
3. check whether an RFI with the same `RFINumber` already exists for that contract
4. create the new RFI if no duplicate exists

Example:

```python path=null start=null
result = sdk.create_rfi_for_project(
    project_criteria={\"ProjectNumber\": \"1234\"},
    rfi_data={
        \"rfi_number\": \"RFI-001\",
        \"Request\": \"Clarify finish at west elevation.\",
    },
)
```

## JSON CLI wrapper
The package includes a small JSON-oriented CLI intended for Codex/tool use and repeatable local scripts.

Run commands from the repo using the local virtual environment:

```powershell path=null start=null
.\.venv\Scripts\python.exe -m bs_fmp_sdk.cli --help
```

Dry-run write commands do not require credentials:

```powershell path=null start=null
.\.venv\Scripts\python.exe -m bs_fmp_sdk.cli create-rfi-for-project `
  --project-criteria '{"ProjectNumber":"1234"}' `
  --rfi-data '{"rfi_number":"RFI-001","Request":"Clarify finish at west elevation."}'
```

Live lookups and committed writes use the SDK `.env` configuration. Add `--commit` only after reviewing the resolved project/contract and payload.

CAAN lookup examples:

```powershell path=null start=null
.\.venv\Scripts\python.exe -m bs_fmp_sdk.cli find-caans --caan ABC123
.\.venv\Scripts\python.exe -m bs_fmp_sdk.cli search-caans --search-text classroom
```

## Error handling
The package exposes typed exceptions for common failure modes:
- `FileMakerError`
- `FileMakerAuthError`
- `FileMakerLayoutError`
- `FileMakerNotFoundError`
- `FileMakerAmbiguousResultError`
- `FileMakerDuplicateError`
- `FileMakerValidationError`

This is intended to let downstream code distinguish:
- no match
- too many matches
- duplicate create attempts
- bad inputs
- auth/layout failures

## Layout policy
The preferred layouts are the `Import*` layouts wherever they exist and make sense for the entity.

Examples already encoded in the package:
- `ImportProjects`
- `ImportContracts`
- `ImportRFILog`
- `ImportSubmittal`
- `ImportSubmittalItems`
- `ImportSubmittalReview`

The idea is to centralize these layout choices in one place so downstream projects benefit when they change.

## Submittal note
The FileMaker submittal model is a little counterintuitive:
- `Submittal` is effectively a spec-section table
- `SubmittalItems` contains the actual submitted items to be reviewed

In practice, creating a submittal item means:
1. derive the spec section from the incoming submittal item number
2. resolve or create the matching `Submittal` row for `ProjectNumber` + `SectionNumber`
3. create the `SubmittalItems` row linked through `ID_Submittal`

Current helper for the parsing step:

```python path=null start=null
spec_section = sdk.extract_spec_section(\"081113.2\")
# -> \"08 11 13\"
```

Current uniqueness assumptions:
- `Submittal`: `ProjectNumber` + `SectionNumber`
- `SubmittalItems`: `ID_Submittal` + `SubmittalItemNumber`

## Cross-platform use
This repository is intended for use from both Windows and Linux environments.

Git line endings are controlled with `.gitattributes` so:
- Python and config/docs files stay LF
- Windows-native script files use CRLF

## Development notes
- `research/` contains focused notes useful during development
- `AGENTS.md` contains repository-specific guidance for agents working in this repo
- this repo currently favors a small, portable API surface over broad schema coverage

## Near-term next steps
- add submittal workflows
- refine contract lookup rules where project-to-contract matching needs more specificity
- add shared example notebooks or small example scripts
- document the intended patterns for spreadsheet/report generation use cases
