# Coriolis Operator

!!! abstract
    The Coriolis Operator is the Kubernetes deployment and lifecycle layer for a Coriolis runtime. It is not the migration engine: the deployed Coriolis services perform migration work.

## :material-book-open-page-variant-outline: Current Status

The latest accepted evidence covers operator 0.5.40 managing runtime 2603.4 through a bounded single-node core lifecycle and same-name recreation. This is not an end-to-end migration or production-readiness result.

| Status label | Meaning | Current scope |
| --- | --- | --- |
| Implemented | Present in the operator. | Core profile reconciliation and its resource definitions. |
| Validated | Tested with accepted evidence. | Managed resource reconciliation and lifecycle behavior for dependencies, Coriolis services, and Ingress, including collision safety and normal cleanup. |
| Validated, bounded | Tested only within a stated limit. | Single-node `Ready=True` and retained-state recreation. |
| Pending | Planned work without acceptance evidence. | Provider qualification, migration POCs, logging, and browser flow. |
| Unsupported/unvalidated | Not supported as a public readiness claim. | Production HA, storage, backup, upgrades, and multi-CR routing. |

## :material-book-open-page-variant-outline: Resource And Profile

The namespaced `CoriolisAppliance` custom resource selects the current `core` profile. Its conceptual settings include the runtime version, storage class and size for stateful dependencies, CPU and memory requests and limits, and Ingress host, class, and TLS mode. The resource status records the accepted version, observed generation, and conditions.

The core profile manages these runtime categories:

| Category | Managed runtime |
| --- | --- |
| Dependencies | MariaDB, RabbitMQ, Memcached, and Keystone |
| Bootstrap | Common initialization before application workloads |
| Coriolis services | API, Web UI, Conductor, Scheduler, Transfer Cron, Minion Manager, Deployer Manager, and Worker services |
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
                                                    v
                              [bounded readiness observation]
                                                    |
                                                    v
                                      [Ready=True or Ready=False]
```

The operator reads and classifies expected resources before mutation. A conflicting object is not adopted or overwritten; reconciliation reports a collision instead. After dependencies and successful bootstrap, it applies the workload and access resources, then records operator state last. Readiness is a separate, bounded observation after reconciliation rather than a general health or repair loop.

Owned resources use owner references and are garbage collected with the custom resource. Retained state is ownerless and reused only when its identity and expected metadata match exactly. Same-name recreation is accepted only for this bounded lifecycle case: retained state is reused without mutation, while newly created owned resources belong only to the new custom-resource instance. The retry behavior covers absent or empty status, stable collisions, and in-flight reconciliation retry; it is not broad periodic drift self-healing.

## :material-book-open-page-variant-outline: Conditions

| Condition | Meaning |
| --- | --- |
| `Accepted` | The requested profile and version are supported. |
| `Progressing` | Reconciliation or bounded readiness is still in progress. |
| `Reconciled` | The desired managed resource set was applied; a collision keeps it false. |
| `Ready` | The bounded internal-core readiness observation passed. |
| `Degraded` | A collision, invalid configuration, or failed readiness observation blocks healthy status. |
| `Upgradeable` | Whether version changes are supported; it is currently false. |

!!! warning
    `Ready=True` means only that selected single-replica internal-core checks passed. It does not establish provider connectivity, browser login, migration success, HA, production storage, backup, or production readiness.

## :material-book-open-page-variant-outline: Limits And Next Work

The current core profile uses fixed single replicas. High availability, cross-node behavior, production storage, backup and restore, upgrades, and multi-CR routing remain unsupported or unvalidated. Recovery is intentionally narrow: collisions can recover when the conflicting resource is removed, but the operator does not claim broad drift self-healing.

OpenStack provider and API migration qualification are pending, as are Kubernetes-native logging, Barbican-backed UI credentials, browser login, and browser-driven migration validation. The operator-deployed Worker service runs as root and privileged, with host mounts for `/dev` and `/lib/modules`; this is a significant operational constraint, not a production-security endorsement.
