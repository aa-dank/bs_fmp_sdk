# Initial scope
## Supported entity focus
Only implement functionality that is needed by existing or near-term projects.

Initial target entities:
- Projects
- Contracts
- Submittals
- RFIs

## Non-goals for the first version
- full database coverage
- generalized support for all 73 tables
- FileMaker SQL/script helpers
- support for rarely used layouts

## Expected usage modes
### Direct/raw usage
The low-level API should be usable directly for:
- quick scripts
- ad hoc maintenance tasks
- notebooks
- small experiments

### Higher-level usage
The business layer should support common recurring tasks such as:
- looking up and updating projects
- contract-oriented operations needed by downstream apps
- submittal creation/update flows
- forthcoming RFI workflows

## Expansion policy
Before adding new entity support:
- identify a real downstream use case
- identify the preferred layout
- identify a minimal stable field set
- add only the methods needed for that use case

## Known first-pass ambiguities
These are not blockers for starting implementation, but they should be kept visible because they affect business-facing API design.

### Contract number semantics
- `Contracts::ProjectNumber_lk` should currently be treated as the effective contract number.
- Contract numbering changed from unique contract numbers to just using the associated project number.
- `ProjectNumber_lk` was added as a patch to support that change.
- `Contracts::ContractNumber` should not currently be treated as the canonical public contract identifier for this SDK.
- We do not currently expect to implement contract creation in the first pass.

### Design implication
- business methods that identify or return contracts should be careful about which field they expose as the human-facing contract number
- lookup helpers should be written so this can be corrected centrally once the semantics are fully verified

### Project to contract cardinality
- Historically there were multiple contracts per project.
- Current operational assumption for first-pass workflows is that there is now a single relevant contract per project.
- For workflows like adding RFIs, if more than one contract is found for the resolved project, the SDK should raise an error rather than guess.

### Project resolution
- The expected primary lookup path is `ProjectNumber` -> `ID_Primary`.
- Some older projects may have duplicate `ProjectNumber` values.
- `ProjectName` can be used as an additional filter when `ProjectNumber` alone is not unique.
- Business methods that require a single project should explicitly enforce that expectation and raise when the match set is ambiguous.
- Higher-level SDK methods should prefer normalized snake_case output rather than exposing raw FileMaker field names directly.

### RFI uniqueness
- RFIs should be treated as unique by `ID_Contracts` + `RFINumber`.
- The add/create-RFI workflow should always check for an existing record with that combination before creating a new one.

### Submittal structure
- The `Submittal` table is effectively a spec-section table.
- The real reviewed submission entries are in `SubmittalItems`.
- Given a `SubmittalItemNumber`, the SDK will often need to extract the spec section, resolve or create the matching `Submittal` row, then create the `SubmittalItems` row.
- `Submittal` uniqueness: `ProjectNumber` + `SectionNumber`
- `SubmittalItems` uniqueness: `ID_Submittal` + `SubmittalItemNumber`
- `Submittal.SectionNumber` should be treated as \"Spec Section\" in higher-level docs and APIs where that improves clarity.
- `SubmittalItems.SubmittalItemNumber` should be treated as the business-facing \"Submittal Number\".
- The initial parsing rule for extracting a spec section from a submittal item number should match the existing `constdoc_app` regex approach: find six sequential digits, then split them into pairs.
