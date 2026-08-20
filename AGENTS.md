# AGENTS.md

## Task Classification

Before the first inspection, debugging, or implementation tool call, classify the task as one of:

1. **Discovery:** Open-ended inspection, searching, reading documentation, identifying files, inspecting runtime state, logs, manifests, or configuration without changing anything.
2. **Analysis:** Reasoning about evidence, explaining behavior, identifying likely causes, or evaluating competing explanations.
3. **Active change:** Editing files, running side-effecting commands, applying configuration, or performing mutable operations.
4. **Narrow follow-up:** Reading a specific file or small number of already-identified paths supporting an edit, verification step, or previously scoped task.

## Task Routing And Delegation

- The only roles are `main agent` and `subagent`. "Calling agent" means the main agent.
- Only the main agent may delegate. Each subagent performs only its assigned bounded task and must never delegate or spawn other agents.
- Only the main agent routes work: for discovery, it may delegate the first pass to `explore`; for analysis, it may gather evidence with `explore` then delegate reasoning to `general`; for active changes, it may delegate implementation to `general` when context is clear and instructions are not risky. This does not require delegating the entire user task. The main agent may edit directly only when work is trivial, urgent, or unsafe to delegate.
- `explore` subagents perform read-only discovery, including repository inspection, documentation review, pattern analysis, and observational diagnostics of remote environments. `general` subagents perform active changes and external operations with side effects.
- `/home/radu/Dev/cb-coriolis` is the single project root; all repositories live beneath it, nested repositories do not redefine it, and filesystem access outside it is prohibited and unnecessary.
- The main agent may directly inspect only narrow follow-up paths tied to a known edit, verification step, or scoped task. It must not do broad discovery or active external work when delegation is appropriate.
- The main agent retains decomposition, integration, ambiguity and risk decisions, user communication, and the final response.
- Every delegation prompt must identify the recipient as a subagent and state that no further delegation is allowed. It must state the resolved absolute repository root; that the root and all descendants at any depth are allowed; that nested working directories do not redefine the root; that filesystem access outside the root is prohibited; the exact target, objective, known constraints, relevant commands or files, safety limits, and expected behavior.
- Decompose work with subagent capability and context limits in mind: scope small, independently reviewable objectives, and do not delegate an entire user request or large undivided chunk when practical decomposition exists. Do not ask subagents to guess targets, credentials, command syntax, deployment details, or environment assumptions. Run independent delegations in parallel and dependent work sequentially.
- After every `general` subagent result, the main agent must perform a lightweight sanity review before accepting it, choosing follow-ups, or completing the task. Inspect the relevant diff, output, or state and run one targeted practical check without duplicating the full assignment.
- Request concise factual results: inspected or changed files, commands run, important output, errors, and current state.

## Execution And Safety

- Use targeted searches for symbols, filenames, commands, or keywords; avoid loading broad references unless necessary.
- After a manageable failure caused by syntax, quoting, missing tools, or minor environment mismatch, a subagent may make a small number of clear, low-risk corrective attempts only within its assigned scope.
- Stop and report exact failures when errors indicate permissions, unexpected state, unclear prompts, target ambiguity, or side-effect risk. Do not make environment assumptions or continue repeated failures without corrected instructions.
- Protect secrets: never print, log, echo, or expose their values. Prefer non-interactive secret handling and avoid prompts that may reveal them.
- Failure reports must include the attempted action or command, exact error, corrective attempts, relevant output, and observed state. The main agent reviews failures before proceeding.

## Site Structure

- `docs/` is the MkDocs documentation source.
- Keep documentation assets in `docs/assets/`.

## Confluence Documentation

- Use the authenticated Atlassian MCP server to query documentation in Confluence.
- Use the `Coriolis Docs Support` space (key: `CDS`): `https://cloudbasedev.atlassian.net/wiki/spaces/CDS`.

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

In this repository, any user request to commit, run `git commit`, or create a commit authorizes and requires the full commit-and-publish workflow unless the user explicitly says not to push. The main agent must first inspect and review the intended changes, then delegate execution to a `general` subagent to run `git add`, `git commit`, `git pull --rebase`, then `git push`, each with appropriate arguments and only after the preceding command succeeds. Accept delegated execution only after the mandatory `general`-subagent sanity review.

## CI And Release Versioning

- CI owns Helm chart versioning, application versioning, and container image tags.
- Do not manually change `helm/Chart.yaml` `version` or `appVersion`, or `helm/values.yaml` `image.tag`, unless the user explicitly requests a version change.
- Do not infer, select, or increment release versions for deployment fixes.
