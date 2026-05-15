# Source project notes
## Strongest reference for the low-level wrapper
`project_sync_service` currently has the most advanced low-level FileMaker wrapper.

Useful qualities observed there:
- typed exceptions
- cleaner retry behavior
- explicit auth/layout errors
- timeout handling
- plain dict return values
- no pandas dependency in the adapter itself

This should be the main reference for the core transport layer.

## Strongest reference for business methods
`constdoc_app` shows the style of higher-level FileMaker client methods that perform actual business operations, especially around submittals.

Useful qualities observed there:
- instance-specific convenience methods
- task-oriented APIs instead of only CRUD primitives

Things to improve when carrying ideas over:
- avoid mixing business logic with a weak transport layer
- avoid pandas as a requirement for basic operations
- improve exception clarity

## Archives app
`archives_app` is valuable mostly as a consumer of FileMaker data and as a source of domain logic around projects and CAANs.

It is less useful as the canonical SDK transport reference.

## Older automation scripts
`filemaker_automation` is useful for historical patterns and examples of real tasks:
- changing project managers
- updating project locations
- people/company relationship summaries

It should be treated as reference material, not as the canonical structural model for this repository.
