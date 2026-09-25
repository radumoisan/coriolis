# CIXpress Git-Backed Pipeline-Step Manifest Storage - Current State

## Storage Authority And Migration

| Path | Role |
|---|---|
| `/app/backup/job-manifests` | Internal Git-backed authority root |
| `/app/backup/job-manifests/.initialized` | Marker - exact UTF-8 bytes `version: 1\n` |
| `/app/job-manifests` | Legacy read-only ConfigMap source |

Authority is entire-collection, not per-file overlay. Migration is one bounded synchronous startup attempt when the final internal directory is absent or truly empty, no marker exists, and valid legacy leaves are visible. It copies exact bytes (preserving non-UTF-8 content), stages in owned sibling storage, and atomically renames. After success or valid prepopulation, the internal collection is authoritative with no legacy fallback.

## State Table

| Internal state | Marker | Action | Authority | Writable |
|---|---|---|---|---|
| Nonempty valid leaves | Any | Use internal tree; repair marker at startup if absent | Internal entire collection | Yes, when storage and lock available |
| Empty | Present | Do not migrate - intentionally empty | Internal empty | No v1 create path exists |
| Absent or truly empty | Absent, legacy valid | One bounded startup migration | Legacy until adoption; internal after | Read-only until adoption |
| Migration failed | - | Record diagnostic; retain legacy usable | Legacy fallback | Read-only/unavailable |
| Both absent | Absent, no legacy | Do not fabricate | Uninitialized | Read-only/unavailable |
| Invalid/unreadable | Any | Never fall back | Internal failed | Read-only until out-of-band correction |

Readiness is gated by Redis/config reconciliation only; manifest health does not independently fail `/healthz/ready`.

## Raw Data Contract

Manifests are a separate raw-text collection - never parsed, serialized, formatted, or YAML-modeled. Migration preserves bytes regardless of UTF-8 validity. API reads and writes require UTF-8; non-UTF-8 stored content is cataloged as a read-only error without lossy conversion. `PUT` stores exactly the received UTF-8 body bytes, preserving CRLF/LF and final-newline presence. ETags are strong SHA-256 values from exact stored bytes. `GET` returns raw source with `Content-Type: application/yaml` and a quoted strong `ETag`. `PUT` requires `Content-Type: application/yaml`, UTF-8 body, and the selected-content `ETag` in `If-Match`. Jinja syntax is validated without source transformation. Responses carry six headers: `ETag`, `X-Manifest-Storage-Mode`, `X-Manifest-Authority`, `X-Manifest-Writable`, `X-Manifest-Git-State`, `X-Manifest-Git-Pending`. Status: `400` (invalid path/body/UTF-8/Jinja), `404` (valid absent path), `409` (read-only/unavailable), `412` (stale `If-Match`), `428` (missing precondition), `503` (lock timeout/service unavailable). A successful `PUT` does not prove Git push success.

## Rendering And Pipeline Snapshot

At `create_pipeline` start, one in-memory exact-byte snapshot is taken under shared worktree read coordination. The lock is released before rendering or Kubernetes calls. Rendering uses a Flask `app.jinja_env` overlay plus snapshot `DictLoader`, preserving current globals, filters, context, autoescaping, and undefined semantics. Existing pipelines are unchanged; only pipelines created after a save reflect the updated content.

## Concurrency And Git Publication

Process-wide worktree coordination with explicit lock ordering: shared worktree lock first, then domain lock. Default timeouts: 5 s (request/snapshot), 120 s (Git), 30 s (rebase-abort). No distributed lock or multi-replica write guarantee. Local save success queues asynchronous Git publication via managed pathspecs (`git add -A -- <managed-paths>`). Publication state (disabled/pending/success/failure) is independent of local authority. An unpublished write can be lost if the workload is replaced before publication. The Helm init container removes stale local `job-manifests` before forced remote checkout; remote tree wins when present.

## Frontend Behavior

The Workbench has a third Manifests tab. Catalog entries are grouped by template with search across template/step/path metadata (never filename parsing). Raw source is loaded lazily on selection. The editor uses raw mode: CodeMirror line separator preserves CRLF/LF and final newline; YAML language, lint, format, and `Shift-Alt-f` are disabled. Save uses the selected-content GET `ETag` in `If-Match`. On `412` the draft is retained with explicit recovery (compare, reapply, discard). Dirty drafts are protected during selection/tab/navigation changes. Local activation and Git publication feedback are displayed separately. An older backend without the manifests endpoint degrades only the Manifests tab.

## End-To-End Acceptance

1. Legacy deployment with only ConfigMap mounts -> startup migration adopts internal collection preserving byte hashes.
2. `GET /configuration/manifests` returns catalog with ETags, storage mode, writable state, no side effects.
3. Workbench lazy-loads, edits raw source, saves with `If-Match`, returns new ETag.
4. New pipeline uses saved snapshot; existing pipeline unchanged.
5. Publisher records local-active then Git publication outcome.
6. Rebuild from Git-backed stored collection without legacy mounts - startup restores internal authority.
7. No legacy resurrection: marker-empty remains empty; corrupt internal reports failure without fallback.

## Required Negative Cases

- Dangling/out-of-root symlinks fail migration without partial activation.
- Stale untracked local tree removed before forced checkout.
- Invalid path, encoded traversal/separator/NUL/extra nesting/wrong suffix rejected.
- Non-UTF-8 stored content cataloged read-only, not converted.
- Invalid Jinja `PUT` rejected without byte change or publication.
- Missing `If-Match` -> `428`; stale -> `412` with draft retention.
- Publisher timeout/failure visible, does not block API indefinitely.
- Older backend absence disables only Manifests tab.

## Pending Requirement

Deployment-based E2E acceptance and negative-case tests have not been run. They require separate runtime/deployment authority and are not authorized by this document.

## Maintained Documentation

- Conductor: [README](conductor/README.md), [docs/configuration.md](conductor/docs/configuration.md), [docs/api.md](conductor/docs/api.md), [docs/swagger.yaml](conductor/docs/swagger.yaml), [docs/operations.md](conductor/docs/operations.md), [docs/build_and_deploy.md](conductor/docs/build_and_deploy.md)
- Frontend: [README](frontend/README.md), [docs/admin-workbench.md](frontend/docs/admin-workbench.md)
