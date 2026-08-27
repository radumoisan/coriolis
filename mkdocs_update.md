# MkDocs Refactor Plan

## Objective

Refactor the public MkDocs site around three reader questions:

1. What is Coriolis and where does each component fit?
2. How does a typical OpenStack-to-OpenStack migration work?
3. What does the Coriolis Operator manage, what works today, and what remains limited or pending?

Keep the documentation concise, source-backed, and focused on the big picture. Use small ASCII diagrams where they improve understanding. Do not expose credentials, internal infrastructure, or detailed engineering evidence.

## Current Findings

- The public site is configured by `mkdocs.yml` at the workspace root and uses pages under `docs/`.
- Detailed operator documentation under `coriolis-operator/docs/` is not part of the public MkDocs navigation. It should remain engineering evidence rather than being published directly.
- `docs/index.md` is centered on repository roles and incorrectly states that Kubernetes and Helm deployment artifacts do not exist.
- `docs/discovery.md` is centered on an older VMware-to-OpenStack appliance path.
- `docs/terminology.md` defines the Coriolis appliance only as a VM.
- `docs/appliance-runtime.md` and `docs/appliance-release-flow.md` are dominated by legacy appliance research and internal implementation evidence.
- `docs/vmware-provider.md` is outside the initial OpenStack-to-OpenStack scope.
- `coriolis-operator/docs/architecture.md` still describes the old marker-only controller and is no longer accurate.
- Existing Confluence material provides historical context but no current Kubernetes operator architecture that should override repository evidence.

## Target Navigation

```yaml
nav:
  - Overview: index.md
  - Coriolis Architecture: architecture.md
  - Migration Flow: migration-flow.md
  - Coriolis Operator: operator.md
  - OpenStack Context: openstack-provider.md
  - Terminology: terminology.md
```

Use `⏳` while a page is in progress, `📋` after it is validated, and `📄` for reference pages.

## Page Responsibilities

| Page | Responsibility |
| --- | --- |
| `docs/index.md` | Explain what Coriolis is, what the operator adds, and the current OpenStack-to-OpenStack scope. |
| `docs/architecture.md` | Describe each important Coriolis component, its purpose, architectural location, and dependencies. |
| `docs/migration-flow.md` | Explain a typical migration from endpoint creation through transfer, deployment, validation, and cleanup. |
| `docs/operator.md` | Explain the custom resource, reconciliation, deployed runtime, readiness, validated coverage, pending work, and limitations. |
| `docs/openstack-provider.md` | Describe only the OpenStack assumptions and resources needed for the initial migration path. |
| `docs/terminology.md` | Define the small set of terms used by the other public pages. |

## Planned Diagrams

Architecture concept:

```text
User
  |
Web UI
  |
Coriolis API
  |
Migration control services ---- Worker ---- Provider plugins
  |                                      |
  +-- Conductor, scheduler, transfer     +-- Source OpenStack
      cron, minion manager, deployer     +-- Target OpenStack
      manager

Supporting services: Keystone | RabbitMQ | MariaDB | Memcached

Kubernetes operator -> deploys and reconciles the Coriolis runtime
```

The diagram places MariaDB, RabbitMQ, Memcached, and Keystone as supporting services without reproducing every RPC connection.

Migration concept:

```text
[Endpoints] -> [Transfer definition] -> [Transfer execution]
                                              |
                                [Disk transfer / synchronization]
                                              |
                                     [Transfer complete]
                                      |                \
                                      |                 -> [Separate deployment execution]
                                      |                              |
                                      |                   [Deployment complete]
                                      v
      [Later replica execution] -> [Disk transfer / synchronization]
                                        |
                                 [Transfer complete]
```

## Progressive Update Plan

### Step 1: Establish The Front Door

Discovery:

- Reconfirm core component entry points and deployment boundaries.

Updates:

- Rewrite `docs/index.md`.
- Create `docs/architecture.md`.
- Update `mkdocs.yml` to expose only useful pages available at this stage.
- Leave old pages unlisted temporarily rather than deleting them immediately.

Exit condition:

- A new reader can explain what Coriolis is and identify its major components.

### Step 2: Explain The Migration Flow

Discovery:

- Trace transfer creation, scheduling, source export, disk synchronization, destination deployment, and cleanup.

Updates:

- Create `docs/migration-flow.md`.
- Add one minimal ASCII flow diagram.
- Add a short component-by-stage table.

Exit condition:

- Transfer completion is clearly distinguished from destination deployment completion.

### Step 3: Document The Operator

Discovery:

- Reconcile CRD and controller behavior with `coriolis-operator/STATUS.md`, `coriolis-operator/ROADMAP.md`, `coriolis-operator/BACKLOG.md`, and recorded validation evidence.

Updates:

- Create `docs/operator.md`.
- Cover reconciliation, deployed resources, status conditions, validated scope, current limitations, and planned work.

Exit condition:

- Implemented, validated, partially validated, and pending capabilities cannot be confused.

### Step 4: Narrow The OpenStack Context

Discovery:

- Revalidate only the provider settings relevant to the planned two-cloud proof of concept.

Updates:

- Rewrite `docs/openstack-provider.md`.
- Simplify `docs/terminology.md`.
- Remove exhaustive source-derived options and credential examples.

Exit condition:

- The reader understands source backups, target mappings, temporary workers, connectivity, and cleanup without reading an API reference.

### Step 5: Retire Misleading Material

Discovery:

- Check old pages for unique content or inbound links still worth preserving.

Updates:

- Delete `docs/discovery.md`.
- Delete `docs/vmware-provider.md`.
- Delete `docs/appliance-runtime.md`.
- Delete `docs/appliance-release-flow.md`.
- Remove stale cross-links.
- Remove tracked `site/` output and ignore it; CI owns generated site artifacts.

Exit condition:

- No published page presents legacy appliance research as current operator behavior.

### Step 6: Consistency Pass

Discovery:

- Compare terminology, diagrams, component names, and status claims across all remaining pages.

Updates:

- Shorten repeated explanations.
- Standardize page labels and cross-links.
- Mark validated pages in navigation.

Exit condition:

- Markdown formatting and links pass targeted checks.
- Each concept has one authoritative public page.
- No internal identifiers, credentials, or unsupported claims appear in public content.

Do not run `mkdocs build` unless it is explicitly requested.

## Operator Status To Communicate

- The operator manages a namespaced `CoriolisAppliance`.
- The current profile deploys Coriolis services and their Kubernetes dependencies.
- Core single-replica deployment, Ingress, collision handling, and bounded internal readiness have been validated.
- `Ready=True` does not prove provider connectivity, browser login, migration success, high availability, or production storage.
- Automatic same-name custom resource recreation is accepted only for the bounded single-node 0.5.40 lifecycle case; exact retained state is reused without broad drift repair or production-readiness implications.
- OpenStack provider qualification and the end-to-end migration proof of concept are pending.
- Browser authentication, Barbican-backed UI credentials, and UI logging compatibility are pending.
- Production high availability, backup and restore, upgrades, multi-resource routing, and broader drift repair remain unsupported or unvalidated.
- The privileged worker requirement must be stated clearly.

## Content Policy

- Keep each page focused on one reader question.
- Prefer tables and short ordered flows over prose.
- Keep examples value-safe and free of credentials.
- Describe the current OpenStack-to-OpenStack context only.
- Clearly separate intended Coriolis architecture from operator validation status.
- Keep pipeline IDs, commits, image digests, namespaces, resource UIDs, timings, and detailed proof-of-concept transcripts in engineering status files.
- Delete stale public pages instead of creating a public legacy section. Git history remains the archive.
- Keep `coriolis-operator/docs/` as internal engineering evidence rather than exposing it directly through MkDocs.

## Progress

- [x] 2026-08-27: Inventoried the public MkDocs navigation and pages.
- [x] 2026-08-27: Traced Coriolis components and the OpenStack migration flow against source.
- [x] 2026-08-27: Reconciled operator implementation, validation status, roadmap, and limitations.
- [x] 2026-08-27: Reviewed relevant Coriolis Docs Support search results for reusable context.
- [x] 2026-08-27: Completed Step 1 by establishing the overview, architecture page, and focused navigation.
- [x] 2026-08-27: Completed Step 2 by documenting the branched migration flow.
- [x] 2026-08-27: Completed Step 3 by documenting the operator.
- [x] 2026-08-27: Completed Step 4 by narrowing the OpenStack context and simplifying terminology.
- [x] 2026-08-27: Completed Step 5 by retiring misleading material and removing generated site output from Git.
- [x] 2026-08-27: Completed Step 6 by standardizing terminology, cross-links, component names, and public status claims.

Update this section after each completed discovery and documentation step so the next session can resume from the first unchecked item.
