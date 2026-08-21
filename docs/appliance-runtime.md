---
hide:
  - toc
---

# Coriolis Appliance Runtime

!!! abstract
    Maps one supplied runtime snapshot to local implementation evidence; provenance and runtime readiness are unknown.

## :material-book-open-page-variant-outline: Scope And Evidence

- **Observed:** one 25-running-container snapshot of unknown origin; application tag `2603.4`; Kolla tag `2023.1-ubuntu-jammy`.
- **Source evidence:** local deployment roles and configuration.
- **Unknown:** relation to RC2, source commits, digests, build history, and runtime readiness.

## :material-book-open-page-variant-outline: Operator Status

Separate current operator evidence, independent of the snapshot above.

- RC4 is blocked/OVA-only for Kubernetes; the approved fallback is exact official release `2603.4`.
- All 26 approved images were mirrored to `cr.virtomat.io/virtomat/coriolis`, and all 21 historically selected image pulls passed in `virt-infra-dev-buc-hq` namespace `coriolis`. Step CA and web-proxy are deferred from the current initial runtime.
- The local API-only `core` slice is committed at `ab9df83` but not pushed or deployed; the deployed operator `0.5.3` remains marker-only.
- The metadata-only helper slice (`appliance_resource_name`, `appliance_identity`, `build_resource_metadata`) is committed locally at `fbab6e5` but not pushed or deployed; 44 tests pass, and the deployed marker `0.5.3` is unchanged and carries no standard labels.
- The collision/migration marker API-layer slice is committed locally at `d8df00f` on `dev` but **not pushed or deployed** (70 unit tests pass; ConfigMap RBAC gains only `get`): reconciliation pre-reads the marker ConfigMap before SSA and normalizes a compatible legacy `0.5.2`/`0.5.3` marker in place, treating conflicting metadata as a `ResourceCollision` that is never patched/adopted/deleted/renamed. The deployed operator `0.5.3` remains marker-only and lacks these semantics.
- The pure retained-resource classifier is committed locally at `1b73045` on `dev` but **not pushed or deployed** (94 tests pass): automatic ownerless exact stable-identity reuse across a changed CR UID; external/pre-existing resources fail closed; no runtime resource, reconcile, or adoption mutations.
- The historical documentation-only Secret/configuration contract is committed locally at `8ce26ba` on `dev` but **not pushed or deployed**: it froze the former three-retained-Secret mapping plus the `<appliance>-coriolis-config` and `<appliance>-coriolis-config-secret` split/mount. Its Step CA entry is superseded by the current two-retained-Secret contract.
- The historical pure Secret/ConfigMap builder slice is committed locally at `050f16e` on `dev`, not pushed or deployed: it provided five deterministic manifests with exact key sets; the Step CA builder is superseded while the remaining retained-credential and configuration builders continue as pure helpers. At that commit, 116 tests passed and no generation, reconcile, Kubernetes behavior, RBAC, or deployment changed.
- The historical pure retained credential generator slice is committed locally at `a604579` on `dev`, not pushed or deployed: three helpers independently generated seven frozen keys with `secrets.token_urlsafe(32)` (32 random bytes/256 bits, URL-safe); the Step CA generator is superseded by the current two-Secret/six-key contract. At that commit, 132 tests passed; `main.py` did not call the helpers and no Kubernetes/RBAC/CRD/deployment behavior changed.
- The pure retained Secret semantic validator/extractor is committed locally at `5165629` on `dev`, not pushed or deployed: `validated_retained_secret_values` supports mappings and `V1Secret`, requires `Opaque`, rejects persisted `stringData`, enforces exact frozen keys and string-encoded data, and strictly base64/UTF-8 validates non-empty values without mutation or value exposure; 152 tests pass; no runtime/Kubernetes/RBAC/CRD/deployment behavior changed. Decoded values remain internal and are never logged, statused, or evented.
- The pure non-sensitive `render_coriolis_config` is committed locally at `97153a7` on `dev`, not pushed or deployed: it validates explicit inputs, uses Jinja2 `PackageLoader`/`StrictUndefined`, and renders exactly six frozen ConfigMap files from verbatim Apache-2.0 upstream templates with source/license attribution; it excludes `coriolis.conf`, provider fragments, credentials, and Secret content. 19 focused/171 total tests plus wheel/template checks pass; no runtime/Kubernetes/RBAC/CRD/release/deployment behavior changed.
- The historical pure foundational five-resource preflight is committed locally at `35eac9b` on `dev`, not pushed or deployed: `OwnedClassification` treats an exact owner metadata/controller match as `MANAGED` despite content/type drift; all five resources receive metadata checks before retained semantics; semantic `ValueError` fails closed to `COLLISION`; generators run only for the corresponding `ABSENT` resource after collision-free validation; credentials are hidden from `repr` and remain value-safe. Its Step CA entry is superseded by the current four-resource preflight. At that commit, 23 focused/194 total tests passed and no runtime/Kubernetes/RBAC/CRD/release/deployment behavior changed.
- The historical documentation-only sensitive `coriolis.conf` renderer contract is committed locally at `574efcf` on `dev`, not pushed or deployed: exact one-key owner-referenced Secret boundary; immutable upstream base template and all 16 provider fragments/provider order/maps; custom overrides and compressor disabled; explicit internal inputs/value-safe redacted boundary/no CRD fields. Its former three-Secret retention statement is superseded by the current two-Secret contract; no renderer code/tests/runtime behavior changed at that commit.
- The pure sensitive renderer is committed locally at `9bb20f3` on `dev`, not pushed or deployed: `SensitiveCoriolisEndpoints`, `SensitiveCoriolisCredentials`, redacted one-key `SensitiveCoriolisConfig`, and `render_sensitive_coriolis_config` enforce exact `coriolis.conf` Secret-builder composition and ConfigMap rejection; inputs remain frozen and unmutated with redacted `repr` and fixed value-safe errors; immutable base plus 16 fragments, frozen order/maps, and disabled custom overrides/compressor are preserved. 40 focused/215 total tests, 17/17 parity, 25 wheel resources, and Ruff/mypy/Helm/diff validation pass; no runtime/Kubernetes/RBAC/CRD/release/deployment behavior changed.
- The historical documentation-only multi-resource reconciliation policy is committed locally at `747427a` on `dev`, not pushed or deployed. Its marker-plus-five sequence is superseded; durable collision, preparation-before-write, marker-last, non-transactional failure, and value-safe status semantics carry forward to the current marker-plus-four policy.
- The pure Kubernetes networking/configuration contract is committed locally at `e2ddb30` on `dev`, with tracking status at `2a72e24`; neither commit is pushed or deployed. It derives RabbitMQ, Memcached, MariaDB, and Keystone Service names; freezes plaintext internal ports and API/configuration paths; adds Kubernetes-derived plaintext templates; removes Step CA from the initial pure APIs/preflight; and defines per-CR ingress settings without creating runtime Services or Ingresses. Validation passed: 218 unit tests, Ruff lint/format, strict mypy, Helm lint/template, `git diff --check`, byte parity for all 23 immutable copied templates, and offline wheel inspection of all 27 packaged template resources. No `main.py`, runtime Kubernetes I/O, SSA/RBAC, release/chart/image, or deployment behavior changed; deployed `0.5.3` remains marker-only.
- The marker-plus-four foundational runtime is committed locally at `862777d` on `dev`, with tracking status at `f219977`; neither commit is pushed or deployed. Reconciliation performs the exact ordered marker-plus-four pre-reads with only `404` absent, completes metadata-first preflight/rendering before writes, creates or reuses retained `state-credentials` without writing the reuse path, uses resourceVersion-guarded SSA, writes the four foundational resources in order with the marker last, and preserves earlier writes after a later failure. Retryable failures publish sanitized status before Kopf retry; stable collisions remain mutation-free; `Ready=False/RuntimeNotImplemented` remains truthful. Secret and ConfigMap RBAC is limited to get/create/patch. Validation passed: 243 unit tests, Ruff lint/format, mypy, Helm lint/template, and `git diff --check`.
- The four-Service implementation is committed locally at `797235b` on `dev`, with tracking status at `c28832c`; neither commit is pushed or deployed. It adds deterministic owner-referenced plaintext ClusterIP Services for RabbitMQ (`5672`), Memcached (`11211`), MariaDB (`3306`), and Keystone (`5000`); reconciliation performs the existing marker-plus-four reads followed by four Service reads, with only `404` absent, and completes all preparation before writes. Managed Services use resourceVersion-guarded SSA; writes remain foundational resources, then Services, then marker. Collisions are mutation-free; retries are sanitized with no rollback; `Ready=False/RuntimeNotImplemented` remains truthful. Service RBAC is exactly get/create/patch. Validation passed: 252 tests plus Ruff/mypy/Helm/diff validation.
- The documentation-only dependency workload evidence gate is committed locally at `98ab0e4` on `dev`, unpushed and undeployed. It freezes exact mirrored support-image identities, source-backed dependency evidence, durable resource/credential boundaries, and fail-closed eligibility requirements. MariaDB is the first candidate only after single-node, storage, startup, and probe evidence closes; OCI launch/configuration, storage, bootstrap, probe, replica/disruption, and readiness details remain blockers. No workload, Job, PVC, RBAC, readiness, runtime, release, or deployment behavior changed; deployed `0.5.3` remains marker-only.
- No core workloads, endpoints, Ingress, or Jobs are implemented or deployed. Remaining Services and dependency workload/bootstrap/storage/readiness/rotation design are later work; deployed `0.5.3` remains marker-only.

This section records current operator state and does not establish snapshot provenance or runtime readiness.

## :material-book-open-page-variant-outline: Runtime Architecture

```text
Coriolis appliance VM
|-- Host operating system and systemd services
|-- Coriolis application containers
|-- Kolla-managed dependencies
`-- Third-party supporting containers
```

Conceptual grouping of the snapshot; host services are absent from `docker ps`.

| Layer | Observed count | Purpose |
| --- | ---: | --- |
| Coriolis application/admin | 13 | Application, workflow, data-plane, and appliance administration. |
| Kolla dependencies | 10 | Identity, secrets, messaging, cache, database, and utilities. |
| Third-party support | 2 | Certificate authority and telemetry storage. |
| Total | 25 | Running containers in one snapshot. |

## :material-book-open-page-variant-outline: Application Source Ownership

### :material-application-edit-outline: Core Application Repository

`cloudbase/coriolis`, checked out locally as `coriolis-oss`, supplies these seven entry points:

- `coriolis-api` - `coriolis.cmd.api:main`
- `coriolis-conductor` - `coriolis.cmd.conductor:main`
- `coriolis-worker` - `coriolis.cmd.worker:main`
- `coriolis-scheduler` - `coriolis.cmd.scheduler:main`
- `coriolis-transfer-cron` - `coriolis.cmd.transfer_cron:main`
- `coriolis-minion-manager` - `coriolis.cmd.minion_manager:main`
- `coriolis-deployer-manager` - `coriolis.cmd.deployer_manager:main`

### :material-application-edit-outline: Dedicated Application Repositories

- `coriolis-provider-openstack` - local OpenStack provider implementation; provider framework remains in core.
- `coriolis-provider-vmware` - local VMware vSphere provider implementation; provider framework remains in core.
- `coriolis-web` - `cloudbase/coriolis-web`, checked out locally as the `coriolis-web` submodule at `6b08192` (`1.8.4`).
- `coriolis-licensing-server` - `cloudbase/coriolis-licensing-server`; source is not checked out locally.
- `coriolis-metal-hub` - `cloudbase/coriolis-metal-hub`; server source is not checked out locally; `python-coriolismetalhubclient` is a separate client library.
- `coriolis-compressor` - `cloudbase/coriolis-compressor`; source is not checked out locally.

### :material-application-edit-outline: Appliance-Generated Components

- `coriolis-web-proxy` - generated local proxy configuration and startup behavior.
- `coriolis-console-editor` - generated appliance utility, intentionally idle.

This maps source ownership, not deployed commits or image provenance.

## :material-book-open-page-variant-outline: Observed Component Inventory

Registry prefix for application and Kolla images: `registry.cloudbase.it/appliance/`.

### :material-application-edit-outline: Coriolis

| Container | Image | Tag | Role | Status |
| --- | --- | --- | --- | --- |
| `coriolis-metal-hub` | `coriolis-metal-hub` | `2603.4` | Metal Hub integration | Up |
| `coriolis-console-editor` | `coriolis-console-editor` | `2603.4` | Console/editor, intentionally idle | Up |
| `coriolis-licensing-server` | `coriolis-licensing-server` | `2603.4` | License backend | Up |
| `coriolis-web-proxy` | `coriolis-web-proxy` | `2603.4` | Web/UI reverse proxy | Up |
| `coriolis-web` | `coriolis-web` | `2603.4` | Web UI | Up |
| `coriolis-worker` | `coriolis-worker` | `2603.4` | Migration/provider execution worker | Up |
| `coriolis-deployer-manager` | `coriolis-deployer-manager` | `2603.4` | Deployment orchestration | Up |
| `coriolis-minion-manager` | `coriolis-minion-manager` | `2603.4` | Temporary/minion worker management | Up |
| `coriolis-scheduler` | `coriolis-scheduler` | `2603.4` | Transfer scheduling | Up |
| `coriolis-transfer-cron` | `coriolis-transfer-cron` | `2603.4` | Periodic transfer work | Up |
| `coriolis-conductor` | `coriolis-conductor` | `2603.4` | Core workflow coordination | Up |
| `coriolis-api` | `coriolis-api` | `2603.4` | Coriolis API | Up |
| `coriolis-compressor` | `coriolis-compressor` | `2603.4` | Compression/data processing | Up |

### :material-application-edit-outline: Kolla

| Container | Image | Tag | Role | Status |
| --- | --- | --- | --- | --- |
| `kolla_toolbox` | `kolla-toolbox` | `2023.1-ubuntu-jammy` | Kolla administration/utilities | Up |
| `barbican_worker` | `barbican-worker` | `2023.1-ubuntu-jammy` | Secret-management worker | Up (healthy) |
| `barbican_keystone_listener` | `barbican-keystone-listener` | `2023.1-ubuntu-jammy` | Barbican/Keystone listener | Up (healthy) |
| `barbican_api` | `barbican-api` | `2023.1-ubuntu-jammy` | Secret-management API | Up (healthy) |
| `keystone` | `keystone` | `2023.1-ubuntu-jammy` | Internal identity service | Up (healthy) |
| `keystone_fernet` | `keystone-fernet` | `2023.1-ubuntu-jammy` | Fernet key management | Up (healthy) |
| `keystone_ssh` | `keystone-ssh` | `2023.1-ubuntu-jammy` | Keystone SSH support | Up (healthy) |
| `rabbitmq` | `rabbitmq` | `2023.1-ubuntu-jammy` | Message broker | Up (healthy) |
| `memcached` | `memcached` | `2023.1-ubuntu-jammy` | Cache | Up (healthy) |
| `mariadb` | `mariadb-server` | `2023.1-ubuntu-jammy` | Relational database | Up (healthy) |

### :material-application-edit-outline: Third-Party

| Container | Image | Tag | Role | Status |
| --- | --- | --- | --- | --- |
| `step-ca` | `smallstep/step-ca` | `latest` | Local certificate authority | Up (healthy) |
| `influxdb` | `influxdb` | `1.7` | Logging/telemetry database | Up |

## :material-book-open-page-variant-outline: Version Families And Provenance

- Matching application tags show the observed application family, not a common source commit or build.
- Kolla tags can differ from, or remain stable across, application versions.
- `latest` is mutable.
- Tags do not provide digests.

!!! warning
    The snapshot does not establish provenance or readiness.

## :material-book-open-page-variant-outline: Component Responsibilities

- UI/API: web, web proxy, API.
- Workflow: conductor, scheduler, transfer cron, minion manager, deployer manager.
- Data plane: worker, compressor.
- Appliance admin: console editor, licensing server, Metal Hub.
- Identity/secrets: Keystone and Barbican.
- Messaging/persistence: RabbitMQ, MariaDB, Memcached.
- PKI/telemetry: Step CA, InfluxDB.
- Kolla toolbox: administration utilities.

!!! warning
    The worker is privileged and mounts host device and kernel resources.

## :material-book-open-page-variant-outline: Host Services, Networking, And Expected Absences

- Logger is a host systemd binary; InfluxDB is a container.
- Licensing UI can use a separate host.
- HAProxy, Fluentd, and Redis are disabled and expected absent.
- Built images do not imply running containers; empty `PORTS` does not imply unavailability.
- Local roles generally use host networking; host `ss` is relevant.
- **Unknown:** exact networking mode requires restricted inspection.

## :material-book-open-page-variant-outline: Health And Persistence Limits

- `Up` means process running; `Up (healthy)` means Docker health status.
- Kolla reported healthy while Coriolis reported Up in the snapshot; this is process proof only.
- Creation time, uptime, and image build time differ; causes are unknown.
- VM disk export can preserve persistent state; the snapshot does not establish import origin or persistence across releases.

See [Appliance Release](appliance-release-flow.md).

## :material-book-open-page-variant-outline: Safe Read-Only Inspection

```bash
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.CreatedAt}}'
docker inspect --format '{{.Name}} network={{.HostConfig.NetworkMode}} restart={{.HostConfig.RestartPolicy.Name}} image={{.Config.Image}}' <container>
docker image inspect --format '{{.RepoTags}} {{.Id}} {{.Created}}' <image>
ss -lntup
systemctl --no-pager status coriolis-logger
cat /etc/coriolis/coriolis.release
cat /etc/os-release
uptime -s
```

!!! warning
    Do not use unrestricted `docker inspect`, secret files, generated configuration, or mounted secret files.

## :material-book-open-page-variant-outline: Open Questions

- Appliance OS and release value.
- Import versus upgrade history.
- Full stopped-container inventory.
- Image digests.
- Host listeners.
- Logger status.
- Exact relation to `2608.0-rc2`.
- Whether optional components can safely be excluded.

## :material-book-open-page-variant-outline: Implementation Evidence

`coriolis-docker/coriolis_ansible/appliance.yml:1-87`; `roles/coriolis/worker/tasks/setup_worker_container.yml:2-29`; `roles/common/console-editor/tasks/setup_console_editor_container.yml:7-17`; `roles/bootstrap/step-ca/tasks/setup_step_ca_container.yml:26-29`; `roles/bootstrap/step-ca/vars/main.yml`; `roles/coriolis/logger/vars/main.yml`; `coriolis-docker/kolla/deploy.sh:65-78`; `coriolis-docker/coriolis_ansible/group_vars/all.yml:126-156`.

Local paths corroborate design; the snapshot is separate evidence.

## :material-book-open-page-variant-outline: Related Information

[Terminology](terminology.md), [Appliance Release](appliance-release-flow.md), and [Discovery](discovery.md).
