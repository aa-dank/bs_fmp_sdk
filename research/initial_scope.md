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
