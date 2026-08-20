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
- All 26 approved images were mirrored to `cr.virtomat.io/virtomat/coriolis`, and all 21 initial-runtime image pulls passed in `virt-infra-dev-buc-hq` namespace `coriolis`.
- The local API-only `core` slice is implemented but uncommitted and not deployed; the deployed operator `0.5.3` remains marker-only.
- No core runtime workloads are implemented or deployed; foundational resource contracts/construction is the next milestone.

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
- `coriolis-web` - `cloudbase/coriolis-web`; source is not checked out locally.
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
