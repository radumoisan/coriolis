# AGENTS.md

## Purpose

This repository is for the Cloudbase Coriolis Product.

## Task Classification

Before the first inspection, debugging, or implementation tool call, classify the task as one of:

1. discovery
2. analysis
3. active change
4. narrow follow-up

Definitions:

- **Discovery:** Open-ended inspection, searching, reading documentation, identifying files, inspecting runtime state, logs, manifests, or configuration without changing anything.
- **Analysis:** Reasoning about evidence, explaining behavior, identifying likely causes, or evaluating competing explanations.
- **Active change:** Editing files, running side-effecting commands, applying configuration, or performing mutable operations.
- **Narrow follow-up:** Reading a specific file or a small number of already-identified paths in support of an edit, verification step, or previously scoped task.

## Agent Routing

### Required Routing Rules

- For discovery tasks, the main agent must delegate the first pass to `explore`.
- For analysis tasks, the main agent must gather evidence with `explore` first and then delegate reasoning to `general`.
- For active-change tasks, the main agent must delegate edit and implementation work to `general` when the context is clear and the instructions are not risky. Direct main-agent edits are allowed only for trivial, urgent, or unsafe-to-delegate cases. The main agent must not do broad discovery directly when `explore` fits the task.
- Direct main-agent inspection is allowed only for narrow follow-up reads tied to a known file/path, an edit already in progress, or a verification step.

### Agent Roles and Selection

- **Read-Only Tasks (`explore`):** Use the `explore` agent for discovery work: searching the repository, reading files, inspecting documentation, understanding existing patterns, summarizing findings, and running read-only commands. This includes exploratory diagnostics against remote machines, Kubernetes clusters, or other environments when the intent is observation rather than change.
- **Active Tasks (`general`):** Use the `general` agent for edit and implementation work when the context is clear and instructions are not risky, for actions that interact with systems in a non-read-only way, execute commands with side effects, or perform external operations with side effects. The main agent may still perform direct local file edits for trivial, urgent, or unsafe-to-delegate cases, and narrowly scoped supporting reads as allowed by the routing rules above.
- **Keep Context Small:** Use the smallest relevant files, snippets, or command outputs needed to answer the question. Avoid loading large files or broad documentation into the main context unless necessary.

### Delegation Rules

- Do not ask sub-agents to guess missing targets, credentials, command syntax, deployment details, or environment assumptions.
- Every delegation prompt must state the resolved absolute filesystem root, that the root and all descendants at any depth are allowed, that nested working directories do not redefine the root, that filesystem access outside the root is prohibited, and that these requirements must be propagated to all recursive delegations. Also provide the exact target, task objective, known constraints, commands or files involved, safety limits, and expected behavior.
- Ask sub-agents to return concise factual results: what was inspected or changed, commands run, files touched, important output, errors, and current state.
- Delegate the smallest safe unit of work. Avoid broad or open-ended instructions when a precise task can be given.
- When tasks are independent and do not rely on each other, prefer parallel delegation. Keep dependent work sequential.

### Main-Agent Restrictions

- The main agent must not perform broad repository discovery directly when `explore` fits the task.
- The main agent must not perform direct edit or implementation work when it can be safely delegated to `general` with clear context and non-risky instructions.
- The main agent must not perform active external-system work directly when `general` is the appropriate isolation boundary.
- The main agent remains responsible for orchestration, deciding whether evidence is sufficient, choosing follow-up actions, and producing the final user-facing answer.

### Execution and Safety

- **Targeted Searches:** When checking syntax, behavior, or implementation details, search for specific symbols, filenames, commands, or keywords instead of reading entire large references.
- **Bounded Recovery:** If a delegated command or operation fails because of syntax, quoting, missing tools, minor environment mismatch, or a similar manageable issue, the sub-agent may make a small number of reasonable corrective attempts when the next step is clear and low risk. Do not drift into open-ended trial and error.
- **Stop on Unclear or Risky Errors:** If the failure suggests permissions issues, unexpected state, unclear prompts, target ambiguity, or a risk of side effects, stop and report the exact failure instead of guessing.
- **Handle Failures Safely:** Return the attempted command or action, the exact error, any corrective attempts made, relevant output, and the observed state. The main agent should review the failure before deciding the next step.
- **Avoid Hidden Assumptions:** Do not infer environment-specific details unless they are documented or already verified.
- **Protect Secrets:** Never print, log, echo, or expose secret values. Prefer non-interactive secret handling where possible, and avoid prompts that may reveal sensitive data.
- **Fail Fast on Repeated Errors:** If the same operation keeps failing after a small number of reasonable corrective attempts, stop for that target and return the facts. Do not continue experimenting without a corrected instruction.
- **Main-Agent Orchestration:** The main agent is responsible for reviewing results, deciding follow-up actions, and delegating corrected tasks when needed.

## Site Structure

- Use `docs/` as the MkDocs documentation source directory.
- Split the content into one file per top-level chapter only.
- Include all eight top-level chapters from `kubernetes_lab.md`.
- Do not create separate files for subsections unless explicitly requested.
- Keep `docs/index.md` as the site home page and `docs/prerequisites.md` as the reference page for confirmed lab requirements.
- Keep `docs/assets/` for training diagrams and other documentation assets.
- Keep `migration.md` at the repository root as the internal migration tracker.
- Keep `playground.md` at the repository root as the internal lab machine inventory.
- Keep `commands.md` at the repository root as the internal record of successfully executed training commands.

## Navigation Status Markers

Use these status markers consistently in `mkdocs.yml` navigation labels:

- `📋` for completed or currently validated pages.
- `⏳` for pages still in progress.
- `📄` for reference pages.

## Writing Rules

- Keep explanations concise.
- Do not over-explain unless explicitly asked.
- Prefer direct, task-focused wording.
- Normalize inconsistent formatting from the source.
- Keep command examples close to the original intent, but rewrite for clarity when needed.
- All second-level headings must use the prefix `:material-book-open-page-variant-outline:`, for example `## :material-book-open-page-variant-outline: Second level header`.
- All third-level headings must use the prefix `:material-application-edit-outline:`, for example `### :material-application-edit-outline: Third level header`.

## Admonitions

Use Material admonitions when they improve clarity:

- Use `!!! abstract` for page goals and short page-purpose callouts.
- Use `!!! note` for context.
- Use `!!! tip` for helpful shortcuts or best practices.
- Use `!!! warning` for risky actions.
- Use `!!! danger` for actions that can break the lab or destroy data.
- Use expandable admonitions such as `??? example` for bulky "Current result in this lab" snapshots so the default reading path stays compact.

## Command Formatting

- Start every fenced command block with a short shell comment immediately before the command; an outside prose sentence alone does not satisfy this rule.
- When presenting a provided lab file, use a student-useful inspection command such as `cat <path>` with an in-block shell comment and paired expected-result block instead of rendering the file directly in prose.
- Use one command block per command.
- Do not group multiple commands under one shared comment or one shared expected-result block.
- Exception: A student-useful shell-variable assignment and its immediately following `echo "$VARIABLE"` verification may share a command block and expected-result pair; the expected result contains only the echo output.
- Each command must be followed by an admonition in this form:

```md
??? example "Expected result"
    Expected output or verification notes.
```

- Commands and expected results must remain in pairs.
- Each command must have its own paired expected-result admonition.
- Use expected results to show the actual command output or a close representative example of what the output looks like.
- Do not use redaction placeholders, including `<redacted>`, in student-facing expected results. Use captured actual values when safe; static training fixtures may be shown.
- For a command that generates a live credential, describe the observable result rather than committing the active credential. Do not introduce live bearer tokens, certificate contents, SSH credentials, or connection values into version-controlled student-facing documentation.
- For validated temporary-lab output, use captured actual values rather than invented placeholders. Preserve static training fixtures; do not introduce active credentials or external SSH access details into version control.
- Prefer concrete output over description or interpretation.
- If a command produces no output, use a placeholder such as `No output.`
- If exact output may vary, keep the example realistic and focus on the visible success signals in the command output.

## Lab Flow

- Default to an interactive workflow only when the user explicitly asks for an interactive session during live training.
- Present one instruction at a time when running the lab with the user.
- Before every lab command in interactive mode, state the exact command you recommend next and explain its intent in one short sentence.
- Show the student-facing command exactly as the student should see and run it, even if the actual executed command uses SSH wrappers or other environment-specific prefixes.
- Do not skip the intent explanation, even for obvious or repetitive commands.
- In an interactive session, run one command at a time only.
- In an interactive session, wait for explicit user approval before running each command.
- In an interactive session, after the user runs a non-interactive command, double-check the result before moving on.
- In an interactive session, do not update `commands.md` for commands executed by the user or student.
- After each command, report the result and explain what it means before moving on.
- In an interactive session, if the user says `go`, treat that as approval to proceed with the recommended next step.

## Editing Rules

- Prefer the smallest correct change.
- Keep existing deployment artifacts such as `helm/` and `Dockerfile` unless explicitly asked to change them.
- Do not remove source material that belongs to the training.
- Do not run `mkdocs build` or otherwise attempt to build the MkDocs site unless the user explicitly asks for it.

## Git

- When the user asks for a Git commit, run `git add`, `git commit`, `git pull --rebase`, and then `git push`, each with appropriate arguments and only after the preceding command succeeds.
- Delegate Git commit execution to a `general` sub-agent.

## CI and Release Versioning

- CI owns Helm chart versioning, application versioning, and container image tags.
- Do not manually change `helm/Chart.yaml` `version` or `appVersion`, or `helm/values.yaml` `image.tag`, unless the user explicitly requests a version change.
- Do not infer, select, or increment release versions for deployment fixes.

## Tracking Files

- Update `migration.md` after each material change to record the current phase, active page, next action, status by chapter and subsection, open findings, blockers, and a dated session log.
- Track subchapters in `migration.md`, not just top-level chapters.
- Use these migration statuses: `Not started`, `Structured`, `Formatting`, `Ready for validation`, `Validating`, `Blocked`, and `Complete`.
- Mark a chapter as `Complete` only after all commands in that chapter have been run and their results have been documented.
- Keep unvalidated pages marked `⏳` in `mkdocs.yml`; use `📋` only for completed or currently validated pages.
- Update `playground.md` whenever a lab machine is added, changed, or reassigned.
- Use `playground.md` for internal execution context only; it is not part of the training content.
- Update `commands.md` for successful training commands executed by the agent locally or remotely, including during live interactive training sessions.
- Record only commands from the training material that actually succeeded.
- Record the exact command string that was actually executed successfully, except redact external SSH connection wrappers and credentials as `Connection wrapper: [redacted; executed against the assigned lab VM]` while retaining the exact student/source command. This internal-record redaction does not apply to student-facing expected results.
- Do not replace the executed command with a simplified or student-facing form in `commands.md`.
- Do not record failed commands, exploratory commands, or commands that were corrected before a successful run.
