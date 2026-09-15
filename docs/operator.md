# Coriolis Operator

!!! abstract
    The Coriolis Operator is the Kubernetes deployment and lifecycle layer for a Coriolis runtime. It is not the migration engine: the deployed Coriolis services perform migration work.

## :material-book-open-page-variant-outline: Mental Model

Four layers cooperate, each owned by a different actor:

1. **The installer** deploys and maintains the operator Helm chart. See [Operator Installation](operator-lab-environment.md#operator-installation) for the development-lab installation model.
2. **The operator** (a single reconciler Pod in the `coriolis` namespace) watches `CoriolisAppliance` custom resources.<br>
   &emsp;⤷ It validates the request,<br>
   &emsp;&emsp;⤷ creates dependencies,<br>
   &emsp;&emsp;&emsp;⤷ runs bootstrap,<br>
   &emsp;&emsp;&emsp;&emsp;⤷ applies workloads,<br>
   &emsp;&emsp;&emsp;&emsp;&emsp;⤷ exposes the runtime through Ingress.
3. **The custom resource** (`CoriolisAppliance`) is your declaration of appliance intent:<br>
   &emsp;⟡ runtime version,<br>
   &emsp;⟡ storage classes and sizes,<br>
   &emsp;⟡ resource bounds,<br>
   &emsp;⟡ ingress host and TLS,<br>
   &emsp;⟡ logging retention.<br>
4. **The runtime** is the set of appliance Pods<br>
   &emsp;⟡ MariaDB | RabbitMQ | Memcached | Keystone | Barbican<br>
   &emsp;⟡ the Coriolis services<br>
   &emsp;&emsp;⤷ `API` | `Web` | `Conductor` | `Scheduler` | ...<br>
   &emsp;⟡ the Logging stack<br>
   &emsp;&emsp;⤷ `Loki` | `gateway` | `Alloy` | `adaptor`<br>
   &emsp;⟡ the web UI.

For normal appliance work, change the custom resource and use the runtime. Check the installer and the operator when you need to diagnose or confirm their health.

!!! note ""
    Most generated runtime resources are recreated when you recreate the CR and removed with it. Generated credential Secrets and data PVCs (MariaDB, RabbitMQ, Loki) are retained, so same-name recreation reuses them.

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

## :material-book-open-page-variant-outline: Optional Standalone Helm Installation

!!! info
    Helm values configure the operator Deployment, not the `CoriolisAppliance` runtime.<br>
    See [CR Versus Helm Values, And The Two Retention Profiles](#cr-versus-helm-values-and-the-two-retention-profiles) for the distinction.

These are the chart defaults used by the standalone installation:

??? quote "`coriolis-operator-values.yaml`"

    ```yaml
    # Container image used for the operator.
    image:
      # Registry path containing the operator image.
      repository: cr.virtomat.io/virtomat/coriolis/operator
      # Image version paired with this chart release.
      tag: "0.5.59"
      # Pull the image only when it is not already present on the node.
      pullPolicy: IfNotPresent
    # Secrets Kubernetes uses to pull the private operator image.
    imagePullSecrets:
      - name: regcred
    # Optional short name override for chart resources.
    nameOverride: ""
    # Full generated name for the operator resources.
    fullnameOverride: "coriolis-operator"
    # Service account created for the operator; an empty name uses the chart-generated name.
    serviceAccount:
      create: true
      name: ""
    # Operator log verbosity.
    logLevel: INFO
    # CPU and memory reserved for, and capped for, the operator container.
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 500m
        memory: 512Mi
    # Optional node labels that constrain where the operator runs.
    nodeSelector: {}
    # Optional scheduling tolerations for the operator Pod.
    tolerations: []
    # Optional advanced Pod scheduling rules.
    affinity: {}
    # Pod-wide security settings; run the Pod as a non-root user.
    podSecurityContext:
      runAsNonRoot: true
    # Container security restrictions for the operator.
    containerSecurityContext:
      allowPrivilegeEscalation: false
      capabilities:
        # Drop every Linux capability from the container.
        drop:
          - ALL
      readOnlyRootFilesystem: true
      runAsNonRoot: true
    # HTTP health check served by the operator.
    liveness:
      # Endpoint queried by the kubelet.
      port: 8080
      path: /healthz
      # Wait before starting health checks.
      initialDelaySeconds: 10
      # Check every ten seconds and allow one second for each response.
      periodSeconds: 10
      timeoutSeconds: 1
      # Restart the container after three consecutive failures.
      failureThreshold: 3
    ```

<!-- Install or upgrade the standalone operator release with chart defaults. -->
```bash
# use '--namespace coriolis' to deploy in namespace coriolis
helm upgrade --install coriolis-operator oci://<registry>/coriolis/helm/coriolis-operator
```

??? example "Expected result"

    ```text
    Release "coriolis-operator" does not exist. Installing it now.
    NAME: coriolis-operator
    NAMESPACE: coriolis
    STATUS: deployed
    ```

This command intentionally omits `--version`, so Helm resolves the latest published chart. See [Operator Deployment And CRD](deploy-appliance.md#operator-deployment-and-crd) for deployment and CRD checks.

## :material-book-open-page-variant-outline: CRD First Install And Upgrade Caveat

A **CRD** defines a new Kubernetes resource type. Here, it teaches Kubernetes what a `CoriolisAppliance` is, including its accepted fields and validation rules.

Helm treats files under `crds/` differently from normal chart templates:

- On the first installation, Helm creates the CRD before deploying the operator.
- During `helm upgrade`, Helm updates the operator Deployment and related resources, but skips the CRD.
- During uninstall, Helm also leaves the CRD in place to avoid accidentally deleting custom resources and their data.

This can create a mismatch:

```text
New operator version
        |
        | expects new CoriolisAppliance fields
        v
Old CRD still registered in Kubernetes
```

The Kubernetes API server may then reject, ignore, or remove fields supported by the new operator because the old CRD schema does not know about them.

Therefore, an upgrade has two separate steps:

1. Apply the `coriolisappliances.coriolis.cloudbase.it` CRD supplied with the target chart version.
2. Upgrade the operator with Helm.

The order matters because Kubernetes should understand the new schema before the new operator starts using it.

This article does not upgrade the operator. See [Operator Deployment And CRD](deploy-appliance.md#operator-deployment-and-crd) for installation checks. The caveat is here to prevent assuming that a future `helm upgrade` will update everything automatically.

## :material-book-open-page-variant-outline: CR Versus Helm Values, And The Two Retention Profiles

!!! note "Two different configuration channels"
    The operator chart's Helm values configure the **operator process itself**: its log level, resources, probes, and security contexts. The `CoriolisAppliance` custom resource is a complete, self-contained declaration of the **appliance runtime**: version, storage, ingress, logging, and per-component resources. The CR references pull Secrets by name but does not restate them; they must already exist. See the [lab manifest and environment values](operator-lab-environment.md) for the development configuration.

The CR's three logging knobs answer different questions:

| Key | Meaning |
| --- | --- |
| `retentionHours` | Logs older than this are marked for deletion by the compactor. |
| `retentionDeleteDelayMinutes` | Extra grace period before marked data is physically removed, so a mistaken retention change can be reverted. |
| `compactionIntervalMinutes` | How often stored log chunks are compacted. |

The lab asset ships the **practical profile** `24` h / `15` m / `120` m: a day of queryable history, frequent compaction, and a two-hour undo window. Prior qualification runs instead used a deliberately compressed **test profile** of `1` h / `1` m / `5` m so that retention expiry and physical deletion could be observed within a single session. Both are valid inputs; the test profile exists to make retention provable, not to be left in place. The lab environment uses the practical values because it is standing up something to live in, not benchmarking deletion.

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

## :material-book-open-page-variant-outline: Next Steps And Limitations

Review the [Lab Environment](operator-lab-environment.md), then [Deploy an Appliance](deploy-appliance.md). Continue with [Phase 1: Headless Migration](headless-migration.md), followed by [Phase 2: Web UI Migration](web-ui-migration.md). See [Technical Debt](technical-debt.md) for current limitations and open work.
