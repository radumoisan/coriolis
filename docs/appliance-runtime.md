---
hide:
  - toc
---

# Coriolis Appliance Runtime

!!! abstract
    This page maps one supplied `docker ps` snapshot to local implementation evidence and does not establish provenance or runtime readiness.

## :material-book-open-page-variant-outline: Scope And Evidence

The snapshot records 25 running containers from one appliance of unknown origin. It could be a fresh import, in-place upgrade, or stateful build; no conclusion is justified. Every snapshot observation on this page is therefore an example from that one appliance and is not proof of current RC2 `2608.0` behavior.

Observed runtime facts are container names, image references, tags, and status. Local-code corroboration is the deployment role and configuration evidence. Inference connects those two evidence types but is not runtime proof. No secrets were inspected.

The observed application tag is `2603.4`; the Kolla tag is `2023.1-ubuntu-jammy`. This single appliance snapshot is explicitly not proof for `2608.0-rc2`.

## :material-book-open-page-variant-outline: Runtime Architecture

```
Coriolis appliance VM
|
+-- Host operating system and systemd services
|   +-- Docker
|   +-- Coriolis logger
|   +-- Network and certificate configuration
|
+-- Coriolis application containers
|
+-- Kolla-managed dependencies
|
+-- Public supporting containers
```

| Layer | Observed count | Purpose |
| --- | ---: | --- |
| Coriolis application/admin | 13 | Application, workflow, data-plane, and appliance administration services. |
| Kolla dependencies | 10 | Internal identity, secrets, messaging, cache, database, and utility services. |
| Public support | 2 | Certificate authority and telemetry storage. |
| Total | 25 | Running containers in the one supplied snapshot. |

The host layer supplies Docker, systemd-managed services, networking, and certificate configuration. Host services do not appear in `docker ps`; the three container layers do.

## :material-book-open-page-variant-outline: Application Source Ownership

A runtime component or image is distinct from the repository that supplies its application source. This map shows default source ownership and build inputs, not a deployed commit, image digest, image provenance, or current RC2 behavior.

### :material-application-edit-outline: Core Application Repository

These seven components come from the single open-source `cloudbase/coriolis` Git repository, checked out locally as `coriolis-oss`. They are distinct service entry points in one shared Python package, and none has a dedicated application-source repository.

- `coriolis-api` - `coriolis.cmd.api:main`
- `coriolis-conductor` - `coriolis.cmd.conductor:main`
- `coriolis-worker` - `coriolis.cmd.worker:main`
- `coriolis-scheduler` - `coriolis.cmd.scheduler:main`
- `coriolis-transfer-cron` - `coriolis.cmd.transfer_cron:main`
- `coriolis-minion-manager` - `coriolis.cmd.minion_manager:main`
- `coriolis-deployer-manager` - `coriolis.cmd.deployer_manager:main`

Exact source evidence is `coriolis-oss/setup.cfg:26-35`. Detailed architecture and coupling analysis is outside this source-ownership map.

### :material-application-edit-outline: Dedicated Application Repositories

Source ownership is distinct at the repository level for these four components.

- `coriolis-web` - `cloudbase/coriolis-web` on GitHub; its source is not checked out locally.
- `coriolis-licensing-server` - `cloudbase/coriolis-licensing-server` on Bitbucket; its source is not checked out locally.
- `coriolis-metal-hub` - `cloudbase/coriolis-metal-hub` on Bitbucket; server source is not checked out locally. `python-coriolismetalhubclient` is a separate client library, not its server source.
- `coriolis-compressor` - `cloudbase/coriolis-compressor` on GitHub; its source is not checked out locally.

### :material-application-edit-outline: Appliance-Generated Components

No independent application-source repository was identified in the local product source layout for these components.

- `coriolis-web-proxy` - Generated local proxy configuration and startup behavior.
- `coriolis-console-editor` - Generated appliance utility and intentionally idle.

This establishes only that no source clone is used by their observed local roles; it does not prove that an external source repository never exists.

### :material-application-edit-outline: Source Ownership Summary

```
Application source ownership
|
+-- cloudbase/coriolis
|   +-- coriolis-api
|   +-- coriolis-conductor
|   +-- coriolis-worker
|   +-- coriolis-scheduler
|   +-- coriolis-transfer-cron
|   +-- coriolis-minion-manager
|   +-- coriolis-deployer-manager
|
+-- cloudbase/coriolis-web
|   +-- coriolis-web
|
+-- cloudbase/coriolis-licensing-server
|   +-- coriolis-licensing-server
|
+-- cloudbase/coriolis-metal-hub
|   +-- coriolis-metal-hub
|
+-- cloudbase/coriolis-compressor
|   +-- coriolis-compressor
|
`-- Appliance-generated
    +-- coriolis-web-proxy
    `-- coriolis-console-editor
```

This is a source-ownership map rather than a deployment or CI/CD map.

## :material-book-open-page-variant-outline: Observed Component Inventory

Names, images, tags, and status below are examples from one runtime snapshot of an appliance of unknown origin, not proof of current RC2 `2608.0` behavior. Role mappings are corroborated by Ansible role names, but exact workload behavior still needs operational testing.

### :material-application-edit-outline: Coriolis

| Container | Image | Tag | Role | Observed health indicator |
| --- | --- | --- | --- | --- |
| `coriolis-metal-hub` | `registry.cloudbase.it/appliance/coriolis-metal-hub` | `2603.4` | Metal Hub integration | Up |
| `coriolis-console-editor` | `registry.cloudbase.it/appliance/coriolis-console-editor` | `2603.4` | Console/editor container, intentionally idle | Up |
| `coriolis-licensing-server` | `registry.cloudbase.it/appliance/coriolis-licensing-server` | `2603.4` | License backend | Up |
| `coriolis-web-proxy` | `registry.cloudbase.it/appliance/coriolis-web-proxy` | `2603.4` | Web/UI reverse proxy | Up |
| `coriolis-web` | `registry.cloudbase.it/appliance/coriolis-web` | `2603.4` | Web UI | Up |
| `coriolis-worker` | `registry.cloudbase.it/appliance/coriolis-worker` | `2603.4` | Migration/provider execution worker | Up |
| `coriolis-deployer-manager` | `registry.cloudbase.it/appliance/coriolis-deployer-manager` | `2603.4` | Deployment orchestration | Up |
| `coriolis-minion-manager` | `registry.cloudbase.it/appliance/coriolis-minion-manager` | `2603.4` | Temporary/minion worker management | Up |
| `coriolis-scheduler` | `registry.cloudbase.it/appliance/coriolis-scheduler` | `2603.4` | Transfer scheduling | Up |
| `coriolis-transfer-cron` | `registry.cloudbase.it/appliance/coriolis-transfer-cron` | `2603.4` | Periodic transfer work | Up |
| `coriolis-conductor` | `registry.cloudbase.it/appliance/coriolis-conductor` | `2603.4` | Core workflow coordination | Up |
| `coriolis-api` | `registry.cloudbase.it/appliance/coriolis-api` | `2603.4` | Coriolis API | Up |
| `coriolis-compressor` | `registry.cloudbase.it/appliance/coriolis-compressor` | `2603.4` | Compression/data processing | Up |

### :material-application-edit-outline: Kolla

| Container | Image | Tag | Role | Observed health indicator |
| --- | --- | --- | --- | --- |
| `kolla_toolbox` | `registry.cloudbase.it/appliance/kolla-toolbox` | `2023.1-ubuntu-jammy` | Kolla administration/utilities | Up |
| `barbican_worker` | `registry.cloudbase.it/appliance/barbican-worker` | `2023.1-ubuntu-jammy` | Secret-management worker | Up (healthy) |
| `barbican_keystone_listener` | `registry.cloudbase.it/appliance/barbican-keystone-listener` | `2023.1-ubuntu-jammy` | Barbican/Keystone listener | Up (healthy) |
| `barbican_api` | `registry.cloudbase.it/appliance/barbican-api` | `2023.1-ubuntu-jammy` | Secret-management API | Up (healthy) |
| `keystone` | `registry.cloudbase.it/appliance/keystone` | `2023.1-ubuntu-jammy` | Internal identity service | Up (healthy) |
| `keystone_fernet` | `registry.cloudbase.it/appliance/keystone-fernet` | `2023.1-ubuntu-jammy` | Fernet key management | Up (healthy) |
| `keystone_ssh` | `registry.cloudbase.it/appliance/keystone-ssh` | `2023.1-ubuntu-jammy` | Keystone SSH support | Up (healthy) |
| `rabbitmq` | `registry.cloudbase.it/appliance/rabbitmq` | `2023.1-ubuntu-jammy` | Message broker | Up (healthy) |
| `memcached` | `registry.cloudbase.it/appliance/memcached` | `2023.1-ubuntu-jammy` | Cache | Up (healthy) |
| `mariadb` | `registry.cloudbase.it/appliance/mariadb-server` | `2023.1-ubuntu-jammy` | Relational database | Up (healthy) |

### :material-application-edit-outline: Public

| Container | Image | Tag | Role | Observed health indicator |
| --- | --- | --- | --- | --- |
| `step-ca` | `smallstep/step-ca` | `latest` | Local certificate authority | Up (healthy) |
| `influxdb` | `influxdb` | `1.7` | Logging/telemetry database | Up |

## :material-book-open-page-variant-outline: Version Families And Provenance

One appliance snapshot of unknown origin shows this layered composition, not one image:

```
Application: 2603.4
Kolla: 2023.1-ubuntu-jammy
Certificate authority: smallstep/step-ca:latest
Telemetry: influxdb:1.7
```

Matching application tags suggest coordinated application deployment, but do not prove a common source commit, build, deployment, or digest. Kolla dependency tags can remain stable across an application update. `latest` is mutable. Tags do not supply digests. These snapshot observations are not proof of current RC2 `2608.0` behavior.

!!! warning
    The supplied snapshot does not establish image provenance, build history, or readiness. Restrict conclusions to its one appliance of unknown origin.

## :material-book-open-page-variant-outline: Component Responsibilities

The flat groups are UI/API (`coriolis-web`, `coriolis-web-proxy`, `coriolis-api`); workflow (`coriolis-conductor`, `coriolis-scheduler`, `coriolis-transfer-cron`, and the managers); data plane (`coriolis-worker`, `coriolis-compressor`); appliance admin (`coriolis-console-editor`, `coriolis-licensing-server`, `coriolis-metal-hub`); identity/secrets (Keystone and Barbican); messaging/persistence (RabbitMQ, MariaDB, Memcached); PKI/telemetry (Step CA, InfluxDB); and Kolla toolbox.

The worker is privileged and local role configuration mounts host device and kernel resources. This is important host interaction, not a generic low-privilege application container. This local implementation evidence corroborates the role mapping, while the single unknown-origin snapshot is not proof of current RC2 `2608.0` behavior.

Per-stage implementation references are `coriolis-docker/coriolis_ansible/appliance.yml:1-87`, `roles/coriolis/worker/tasks/setup_worker_container.yml:2-29`, `roles/bootstrap/step-ca/vars/main.yml`, and `roles/coriolis/logger/vars/main.yml`.

## :material-book-open-page-variant-outline: Host Services And Expected Absences

`coriolis-logger` is expected as a host systemd static binary; InfluxDB is a container. The absence of a logger container is not a discrepancy. The licensing UI can deploy to a separate host group, so its absence would also not be a discrepancy.

HAProxy, Fluentd, and Redis are disabled by Kolla configuration, making their absence expected. A broad built-image set does not equal the running container set. Current image inventory does not prove which optional components are needed for the first VMware-to-OpenStack objective; this unknown-origin snapshot happens to show Metal Hub, licensing, and compressor running, though they are outside the current investigation scope and are not proof of current RC2 `2608.0` behavior.

## :material-book-open-page-variant-outline: Host Networking

An empty `PORTS` column does not mean services are unavailable. Local role configuration widely uses `network_mode: host`, so containers share the host namespace and bind host interfaces; Docker publishing is irrelevant, while host firewall rules and port conflicts apply. Host `ss` output is more relevant.

The specific network mode must be confirmed with restricted inspection of the exact container, even though local roles show expected configuration. The single unknown-origin snapshot is not proof of current RC2 `2608.0` networking behavior.

## :material-book-open-page-variant-outline: Health, Creation, And Uptime

`Up` means the container process is running. `Up (healthy)` is Docker health status. In this one unknown-origin appliance snapshot, most Kolla containers recorded healthy while most Coriolis containers recorded only Up; neither proves API, migration, endpoint, or cleanup correctness, and neither is proof of current RC2 `2608.0` behavior.

Without repeating exact absolute times, the observed runtime lasted about half an hour, application container objects were roughly two weeks old, most Kolla objects roughly five months old, Step CA roughly three months old, and Kolla toolbox near the current runtime. `CREATED`, current uptime, and image build time are different values. The split could result from reboot, upgrade, stateful base, OVA preservation, or selective recreation. Unknown origin means no conclusion.

## :material-book-open-page-variant-outline: OVA Persistence Implications

See [Appliance Release](appliance-release-flow.md) for the observed release and export flow.

A VM disk export can preserve images and layers, container definitions and creation times, database state, PKI, configuration, and services. Restart policy can start existing containers on boot. This snapshot does not prove that this appliance was imported from an OVA or that every container and layer persists the same way across releases; it is not proof of current RC2 `2608.0` behavior.

## :material-book-open-page-variant-outline: What This Snapshot Does Not Prove

It does not prove image digests, source commits, image build time, import versus update history, stopped-container inventory, host listeners, license correctness, API correctness, endpoint correctness, migration correctness, cleanup correctness, or a relationship to RC2.

!!! warning
    Container status and matching tags are not provenance or health proof. The one supplied appliance of unknown origin cannot establish current RC2 `2608.0` behavior.

## :material-book-open-page-variant-outline: Safe Read-Only Inspection

Use restricted, read-only inspection when authorized:

```bash
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.CreatedAt}}'
docker inspect --format '{{.Name}} network={{.HostConfig.NetworkMode}} restart={{.HostConfig.RestartPolicy.Name}} image={{.Config.Image}}' <container>
docker port <container>
docker image inspect --format '{{.RepoTags}} {{.Id}} {{.Created}}' <image>
ss -lntup
systemctl --no-pager --type=service --state=running
systemctl --no-pager status coriolis-logger
cat /etc/coriolis/coriolis.release
cat /etc/os-release
uptime -s
```

!!! warning
    Do not use unrestricted `docker inspect`, `docker exec env`, Kolla password files, generated configuration, or mounted secret files. Sensitive inspection can expose credentials, tokens, keys, or other private values.

## :material-book-open-page-variant-outline: Open Questions

- Appliance OS and release value.
- Import versus upgrade history.
- Full stopped-container inventory.
- Image digests.
- Host listeners.
- Logger status.
- Exact relation to `2608.0-rc2`.
- Whether optional components can safely be excluded.

No claim is currently established for these questions.

## :material-book-open-page-variant-outline: Implementation Evidence

Local implementation references: `coriolis-docker/coriolis_ansible/appliance.yml:1-87`; `roles/coriolis/worker/tasks/setup_worker_container.yml:2-29`; `roles/common/console-editor/tasks/setup_console_editor_container.yml:7-17`; `roles/bootstrap/step-ca/tasks/setup_step_ca_container.yml:26-29`; `roles/bootstrap/step-ca/vars/main.yml`; `roles/coriolis/logger/vars/main.yml`; `coriolis-docker/kolla/deploy.sh:65-78`; and `coriolis-docker/coriolis_ansible/group_vars/all.yml:126-156`.

These line and path mappings corroborate deployment design; the runtime snapshot is separate evidence.

## :material-book-open-page-variant-outline: Related Information

[Terminology](terminology.md), [Appliance Release](appliance-release-flow.md), and [Discovery](discovery.md)
