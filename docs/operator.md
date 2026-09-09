# Coriolis Operator

!!! abstract
    The Coriolis Operator is the Kubernetes deployment and lifecycle layer for a Coriolis runtime. It is not the migration engine: the deployed Coriolis services perform migration work.

## :material-book-open-page-variant-outline: Current Status

Accepted evidence covers operator 0.5.40 managing runtime 2603.4 through a bounded single-node core lifecycle and same-name recreation, a bounded development Web UI OpenStack-to-OpenStack migration proof of concept accepted on released operator 0.5.54, logging hardening accepted on 0.5.57, and the [Advanced Operator Tutorial](operator-advanced-tutorial.md) walkthrough followed end to end on release 0.5.59 with runtime 2603.4, recorded checkpoint by checkpoint in the [Coriolis Operator Tutorial Validation Record](operator-tutorial-validation.md). None of this is a production-readiness result; broader production readiness across HA, storage, backup, upgrades, drift, and multi-CR routing remains open.

| Status label | Meaning | Current scope |
| --- | --- | --- |
| Implemented | Present in the operator. | Core profile reconciliation and its resource definitions, including the managed logging stack. |
| Validated | Tested with accepted evidence. | Managed resource reconciliation and lifecycle behavior for dependencies, Coriolis services, and Ingress, including collision safety and normal cleanup. |
| Validated, bounded | Tested only within a stated limit. | Single-node `Ready=True` and retained-state recreation on 0.5.40; a development Web UI OpenStack-to-OpenStack migration proof of concept on 0.5.54; logging hardening on 0.5.57; the [Advanced Operator Tutorial](operator-advanced-tutorial.md) end-to-end walkthrough on 0.5.59 with runtime 2603.4, per its [Validation Record](operator-tutorial-validation.md). |
| In progress | Work with partial evidence not yet accepted end to end on the current release. | The tutorial's reference Helm operator install path, which is render-validated only; live operator installation is owned by Argo CD and not separately accepted. |
| Pending | Planned work without acceptance evidence. | Broader provider qualification and browser-flow validation beyond the bounded 0.5.54 development proof of concept and the bounded 0.5.59 tutorial walkthrough. |
| Unsupported/unvalidated | Not supported as a public readiness claim. | Production HA, storage, backup, upgrades, drift self-healing, and multi-CR routing. |

## :material-book-open-page-variant-outline: Resource And Profile

The namespaced `CoriolisAppliance` custom resource selects the current `core` profile. Its conceptual settings include the runtime version, storage class and size for stateful dependencies, CPU and memory requests and limits, logging retention, and Ingress host, class, and TLS mode. The resource status records the accepted version, observed generation, and conditions.

The core profile manages these runtime categories:

| Category | Managed runtime |
| --- | --- |
| Dependencies | MariaDB, RabbitMQ, Memcached, Keystone, and Barbican |
| Bootstrap | Common initialization before application workloads |
| Coriolis services | API, Web UI, Conductor, Scheduler, Transfer Cron, Minion Manager, Deployer Manager, and Worker services |
| Logging | Loki, the logging gateway, Alloy, and the logging adaptor |
| Access | Services and Ingress resources |
| State | Operator state, generated retained state, and persistent claims where configured |

The operator does not install an Ingress controller, cert-manager, or storage infrastructure. Those are cluster responsibilities.

## :material-book-open-page-variant-outline: Reconciliation

```text
[CoriolisAppliance]
          |
[validate and classify]
          |
          +-- collision --> [fail-closed collision status]
          |
          v
[dependencies] -> [bootstrap] -> [workloads] -> [Ingress]
                                                    |
                                                    v
                                      [operator state recorded last]
                                                    |
                                                    v
                                            [Reconciled=True]
                                                    |
                                  +-----------------+------------------+
                                  |                                    |
                                  v                                    v
                  [bounded core readiness]                [logging stack readiness]
                                  |                                    |
                                  v                                    v
                  [Ready=True or Ready=False]      [LoggingReady=True or LoggingReady=False]
```

The operator reads and classifies expected resources before mutation. A conflicting object is not adopted or overwritten; reconciliation reports a collision instead. After dependencies and successful bootstrap, it applies the workload and access resources, then records operator state last. Core readiness and logging readiness are separate, bounded observations after reconciliation; the logging stack converges independently and later. Neither is a general health or repair loop.

Owned resources use owner references and are garbage collected with the custom resource. Retained state is ownerless and reused only when its identity and expected metadata match exactly. Same-name recreation is accepted only for this bounded lifecycle case: retained state is reused without mutation, while newly created owned resources belong only to the new custom-resource instance. The retry behavior covers absent or empty status, stable collisions, and in-flight reconciliation retry; it is not broad periodic drift self-healing.

## :material-book-open-page-variant-outline: Conditions

| Condition | Meaning |
| --- | --- |
| `Accepted` | The requested profile and version are supported. |
| `Progressing` | Reconciliation or bounded readiness is still in progress. |
| `Reconciled` | The desired managed resource set was applied; a collision keeps it false. |
| `Ready` | The bounded internal-core readiness observation passed. |
| `LoggingReady` | The bounded logging-stack readiness observation passed; it converges independently from `Ready`. |
| `Degraded` | A collision, invalid configuration, or failed readiness observation blocks healthy status. |
| `Upgradeable` | Whether version changes are supported; it is currently false. |

!!! warning
    `Ready=True` alone means only that selected single-replica internal-core checks passed, and even `Ready=True` with `LoggingReady=True` is not migration or production evidence. Neither condition establishes provider connectivity, browser login, migration success, HA, production storage, backup, or production readiness.

## :material-book-open-page-variant-outline: Limits And Next Work

The current core profile uses fixed single replicas. High availability, cross-node behavior, production storage, backup and restore, upgrades, and multi-CR routing remain unsupported or unvalidated. Recovery is intentionally narrow: collisions can recover when the conflicting resource is removed, but the operator does not claim broad drift self-healing.

Barbican-backed UI credentials, browser login, and browser-driven migration have bounded accepted evidence from the 0.5.54 development Web UI proof of concept, Kubernetes-native logging has accepted evidence from the 0.5.57 hardening, and the full [Advanced Operator Tutorial](operator-advanced-tutorial.md) walkthrough on 0.5.59 with runtime 2603.4 completed end to end, recorded in its [Validation Record](operator-tutorial-validation.md). What remains open is broader, repeatable, and production-oriented validation of those flows, plus OpenStack provider and API migration qualification beyond the bounded 0.5.54 and 0.5.59 development walkthroughs. The operator-deployed Worker service runs as root and privileged, with host mounts for `/dev` and `/lib/modules`; this is a significant operational constraint, not a production-security endorsement.
