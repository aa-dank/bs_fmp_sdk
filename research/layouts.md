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

### Submittals
- `ImportSubmittal`
- `ImportSubmittalItems`
- `ImportSubmittalReview`
- `submittal_list`
- `submittalitems_table`
- `Submittal_review_table`

### RFIs
- `ImportRFILog`
- `rfilog_table`
- `RFI Status`

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
