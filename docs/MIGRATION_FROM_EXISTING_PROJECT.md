# Migration from the Existing Baseline

The existing project was intentionally preserved as a Git baseline before the redesign.

Recommended migration workflow:

1. Keep the existing repository and its `.git` directory.
2. Extract this package to a temporary location first.
3. Review the new `README_AR.md`, `PROJECT_MAP.md`, and `docs/ASSIGNMENT_MAPPING.md`.
4. Copy the new project files into the existing working tree as a deliberate refactor.
5. Remove obsolete single-source modules only after verifying the new structure.
6. Create a Git commit such as:

```text
refactor: evolve pipeline into multi-source architecture
```

This keeps the Git history showing the evolution from the original API pipeline to the multi-source Data Engineering implementation.
