# Layout notes
## Preferred layout family
For this SDK, the preferred layouts are the `Import*` layouts wherever they exist and are appropriate for the entity.

These are expected to be close to 1:1 with their corresponding tables and are the preferred request targets.

## Known layouts already referenced by existing projects
### Projects
- `projects_table`
- `ImportProjects`

### CAANs
- `caan_table`

### People
- `people_table`
- `ImportPeople`

### Contracts
- `ImportContracts`
- there are also non-import contract layouts in the file, but they should not be preferred unless needed
- Important semantic note: `Contracts::ProjectNumber_lk` should currently be treated as the effective business-facing contract number.
- Historical note: contract numbering used to be unique, but later changed so the contract number is effectively just the associated project number.
- `ProjectNumber_lk` was added as a patch to support that change.
- For the immediate first pass of SDK development, do not treat `Contracts::ContractNumber` as the canonical business-facing contract identifier.
- For now, contract creation is not an expected SDK use case.
- In higher-level SDK methods, expose this value with normalized snake_case naming such as `contract_number`.

### Submittals
- `ImportSubmittal`
- `ImportSubmittalItems`
- `ImportSubmittalReview`
- `submittal_list`
- `submittalitems_table`
- `Submittal_review_table`
- The `Submittal` table is effectively a spec-section table rather than a table of actual submitted items.
- `Submittal::SectionNumber` is the useful business field here and should be treated as the spec section.
- `SubmittalNumber` on the `Submittal` table is no longer used.
- Actual submitted/reviewed items live in `SubmittalItems`.
- Creating a real submittal item requires resolving the associated `Submittal` row first to obtain the section-level ID used by `SubmittalItems`.
- `Submittal` should be treated as unique by `ProjectNumber` + `SectionNumber`.
- `SubmittalItems` should be treated as unique by `ID_Submittal` + `SubmittalItemNumber`.
- Revision number is not manually entered; it is calculated within the FileMaker system.
- Existing parsing logic for deriving a spec section from a submittal item number should follow the `constdoc_app` pattern: extract six sequential digits, then format them as pairs (`08 11 13`).

### RFIs
- `ImportRFILog`
- `rfilog_table`
- `RFI Status`
- RFI uniqueness rule: treat RFIs as unique by `ID_Contracts` + `RFINumber`.
- `RFINumber` is business-entered and may include revisions, decimals, or other non-uniform formats, but it is still the correct uniqueness key within the contract/project context.

## Design note about fmrest and layouts
`fmrest.Server` has a default layout associated with the server instance, but major calls can also take a layout argument.

Practical implication:
- do not over-couple the client design to a single-layout-per-session assumption
- it may still be useful to keep a server default layout for convenience
- wrapper methods should support explicit layout overrides cleanly

## SDK policy
- centralize supported layout names in code constants
- treat layout selection as part of the SDK contract
- if a layout changes, update this project so downstream projects inherit the fix
- where business-facing field semantics are confusing, prefer documenting the current best interpretation here rather than silently encoding assumptions in code
- where legacy field names are misleading, prefer exposing clearer business terminology in higher-level SDK methods and docs
