# AGENTS.md

## Task Classification

Before the first inspection, debugging, or implementation tool call, classify the task as one of:

1. **Discovery:** Open-ended inspection, searching, reading documentation, identifying files, inspecting runtime state, logs, manifests, or configuration without changing anything.
2. **Analysis:** Reasoning about evidence, explaining behavior, identifying likely causes, or evaluating competing explanations.
3. **Active change:** Editing files, running side-effecting commands, applying configuration, or performing mutable operations.
4. **Narrow follow-up:** Reading a specific file or small number of already-identified paths supporting an edit, verification step, or previously scoped task.

## Task Routing And Delegation

- For discovery, delegate the first pass to `explore`.
- For analysis, gather evidence with `explore` first, then delegate reasoning to `general`.
- For active changes, delegate implementation to `general` when context is clear and instructions are not risky. The main agent may edit directly only when the work is trivial, urgent, or unsafe to delegate.
- `explore` performs read-only discovery, including repository inspection, documentation review, pattern analysis, and observational diagnostics of remote environments. `general` performs active changes and external operations with side effects.
- The main agent may directly inspect only narrow follow-up paths tied to a known edit, verification step, or scoped task. It must not do broad discovery or active external work when delegation is appropriate.
- The main agent retains responsibility for orchestration: review results, decide whether evidence is sufficient, choose follow-ups, and provide the final response.
- Every delegation prompt must state the resolved absolute repository root; that the root and all descendants at any depth are allowed; that nested working directories do not redefine the root; that filesystem access outside the root is prohibited; and that recursive delegations must propagate these requirements. Include the exact target, objective, known constraints, relevant commands or files, safety limits, and expected behavior.
- Delegate the smallest safe unit. Do not ask sub-agents to guess targets, credentials, command syntax, deployment details, or environment assumptions. Run independent delegations in parallel and dependent work sequentially.
- Request concise factual results: inspected or changed files, commands run, important output, errors, and current state.

## Execution And Safety

- Use targeted searches for symbols, filenames, commands, or keywords; avoid loading broad references unless necessary.
- After a manageable failure caused by syntax, quoting, missing tools, or minor environment mismatch, a sub-agent may make a small number of clear, low-risk corrective attempts.
- Stop and report exact failures when errors indicate permissions, unexpected state, unclear prompts, target ambiguity, or side-effect risk. Do not make environment assumptions or continue repeated failures without corrected instructions.
- Protect secrets: never print, log, echo, or expose their values. Prefer non-interactive secret handling and avoid prompts that may reveal them.
- Failure reports must include the attempted action or command, exact error, corrective attempts, relevant output, and observed state. The main agent reviews failures before proceeding.

## Site Structure

- `docs/` is the MkDocs documentation source.
- Keep documentation assets in `docs/assets/`.

## Student-Facing Documentation

The rules in this section apply only to student-facing documentation under `docs/`; they do not impose heading or command-presentation requirements on this `AGENTS.md` file or other internal tracking files.

### Navigation

- Use `📋` for completed or currently validated pages, `⏳` for unvalidated or in-progress pages, and `📄` for reference pages in `mkdocs.yml` navigation labels.

### Writing And Admonitions

- Keep explanations concise, direct, task-focused, and consistently formatted. Keep commands close to their original intent, rewriting only for clarity.
- Prefix every second-level heading with `:material-book-open-page-variant-outline:` and every third-level heading with `:material-application-edit-outline:`.
- Use Material admonitions where helpful: `!!! abstract` for goals or purpose, `!!! note` for context, `!!! tip` for shortcuts or best practices, `!!! warning` for risky actions, and `!!! danger` for destructive actions.

## Editing Rules

- Prefer the smallest correct change.
- Keep existing deployment artifacts such as `helm/` and `Dockerfile` unless explicitly asked to change them.
- Do not run `mkdocs build` or otherwise build the MkDocs site unless explicitly requested.

## Git

When the user requests a commit under this repository's required commit-and-publish workflow, delegate execution to a `general` sub-agent and run `git add`, `git commit`, `git pull --rebase`, then `git push`, each with appropriate arguments and only after the preceding command succeeds.

## CI And Release Versioning

- CI owns Helm chart versioning, application versioning, and container image tags.
- Do not manually change `helm/Chart.yaml` `version` or `appVersion`, or `helm/values.yaml` `image.tag`, unless the user explicitly requests a version change.
- Do not infer, select, or increment release versions for deployment fixes.
