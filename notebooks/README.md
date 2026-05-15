# Notebooks
Use this directory for SDK experimentation and ad hoc local workflows.

## Suggested layout
- Keep committed, shareable notebook examples here.
- Put personal scratch notebooks in `notebooks/local/` so they stay untracked.

## Credentials
- Do not hardcode FileMaker credentials into notebooks.
- Use a local `.env` file at the repository root.
- Start from `.env.example`.

## Suggested local setup
Install the notebook extras with `uv` and point your notebook kernel at the project environment.
