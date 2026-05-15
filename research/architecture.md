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

## Things to avoid early
- exhaustive schema modeling
- code generation from the full design report
- FileMaker script helpers as a central design feature
- large dependency footprint
- premature abstraction for unsupported entities
