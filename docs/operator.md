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
   &emsp;⟡ `mariadb` | `rabbitmq` | `memcached` | `keystone` | `barbican-api` | `barbican-worker`<br>
   &emsp;⟡ the Coriolis services<br>
   &emsp;&emsp;⤷ `coriolis-api` | `coriolis-web` | `coriolis-conductor` | `coriolis-scheduler` | ...<br>
   &emsp;⟡ the Logging stack<br>
   &emsp;&emsp;⤷ `loki` | `gateway` | `alloy` | `adaptor`

For normal appliance work, change the custom resource and use the runtime. Check the installer and the operator when you need to diagnose or confirm their health.

!!! note ""
    Most generated runtime resources are recreated when you recreate the CR and removed with it. Generated credential Secrets and data PVCs (MariaDB, RabbitMQ, Loki) are retained, so same-name recreation reuses them.

## :material-book-open-page-variant-outline: Resource And Profile

The namespaced `CoriolisAppliance` custom resource selects the current `core` profile. Its conceptual settings include the runtime version, storage class and size for stateful dependencies, CPU and memory requests and limits, logging retention, and Ingress host, class, and TLS mode. The resource status records the accepted version, observed generation, and conditions.

The core profile manages these runtime categories:

- **Dependencies:** `mariadb`, `rabbitmq`, `memcached`, `keystone`, and the Barbican components `barbican-api` and `barbican-worker`.
- **Bootstrap:** the common initialization component `common-bootstrap-v3`, which runs before application workloads.
- **Coriolis services:** `coriolis-api`, `coriolis-web`, `coriolis-conductor`, `coriolis-scheduler`, `coriolis-transfer-cron`, `coriolis-minion-manager`, `coriolis-deployer-manager`, and `coriolis-worker` services.
- **Logging:** `loki`, `gateway`, `alloy`, and `adaptor`.
- **Access:** Services and Ingress resources.
- **State:** Operator state, generated retained state, and persistent claims where configured.

!!! warning ""
    The operator does not install an Ingress controller, cert-manager, or storage infrastructure. Those are cluster responsibilities.

## :material-book-open-page-variant-outline: Helm Installation

!!! info
    Helm values configure the operator Deployment, not the `CoriolisAppliance` runtime.<br>
    See [CR Versus Helm Values, And The Two Retention Profiles](#cr-versus-helm-values-and-the-two-retention-profiles) for the distinction.

These are the chart defaults used by the standalone installation:

??? quote "coriolis-operator-values.yaml"

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

The operator chart stores this definition at `coriolis-operator/helm/crds/coriolisappliances.yaml`.

!!! warning ""
    :material-lightbulb-on-outline: `coriolisappliances.yaml` is not an appliance configuration file. It defines the cluster-wide schema for every `CoriolisAppliance` CR: permitted fields, types, required values, defaults, and validation rules.

    ---

    :material-lightbulb-on-outline: Configure an individual appliance through a namespaced `CoriolisAppliance` CR, such as [coriolis-appliance.yaml](assets/manifests/coriolis-appliance.yaml).

    ---

    :material-lightbulb-on-outline: Adding a field to the CRD only makes it acceptable to Kubernetes; the operator reconciliation code must also implement its behavior.

The operator chart installs this CRD:

??? quote "coriolisappliances.yaml"

    ```yaml
    # Helm installs CRDs from this directory only on initial install. Apply this CRD
    # separately before upgrading the chart whenever its schema changes.
    apiVersion: apiextensions.k8s.io/v1
    kind: CustomResourceDefinition
    metadata:
      name: coriolisappliances.coriolis.cloudbase.it
      annotations:
        coriolis.cloudbase.it/upgrade-note: "Apply this CRD separately before chart upgrades; Helm does not upgrade CRDs in crds/."
    spec:
      group: coriolis.cloudbase.it
      scope: Namespaced
      names:
        plural: coriolisappliances
        singular: coriolisappliance
        kind: CoriolisAppliance
        shortNames:
          - ca
      versions:
        - name: v1alpha1
          served: true
          storage: true
          schema:
            openAPIV3Schema:
              type: object
              properties:
                apiVersion:
                  type: string
                kind:
                  type: string
                metadata:
                  type: object
                spec:
                  type: object
                  required:
                    - version
                    - logging
                  properties:
                    profile:
                      type: string
                      enum:
                        - core
                      default: core
                    version:
                      type: string
                      minLength: 1
                    storage:
                      type: object
                      properties:
                        mariadb:
                          type: object
                          required:
                            - storageClassName
                            - size
                          properties:
                            storageClassName:
                              type: string
                              minLength: 1
                            size:
                              type: string
                              minLength: 1
                        rabbitmq:
                          type: object
                          required:
                            - storageClassName
                            - size
                          properties:
                            storageClassName:
                              type: string
                              minLength: 1
                            size:
                              type: string
                              minLength: 1
                    resources:
                      type: object
                      properties:
                        mariadb:
                          type: object
                          required:
                            - requests
                            - limits
                          properties:
                            requests:
                              type: object
                              required:
                                - cpu
                                - memory
                              properties:
                                cpu:
                                  type: string
                                  minLength: 1
                                memory:
                                  type: string
                                  minLength: 1
                            limits:
                              type: object
                              required:
                                - cpu
                                - memory
                              properties:
                                cpu:
                                  type: string
                                  minLength: 1
                                memory:
                                  type: string
                                  minLength: 1
                        rabbitmq:
                          type: object
                          required:
                            - requests
                            - limits
                          properties:
                            requests:
                              type: object
                              required:
                                - cpu
                                - memory
                              properties:
                                cpu:
                                  type: string
                                  minLength: 1
                                memory:
                                  type: string
                                  minLength: 1
                            limits:
                              type: object
                              required:
                                - cpu
                                - memory
                              properties:
                                cpu:
                                  type: string
                                  minLength: 1
                                memory:
                                  type: string
                                  minLength: 1
                    ingress:
                      type: object
                      default:
                        host: coriolis.app.cloudbase.wiki
                        ingressClassName: nginx
                        tls:
                          mode: certManager
                      properties:
                        host:
                          type: string
                          default: coriolis.app.cloudbase.wiki
                        ingressClassName:
                          type: string
                          default: nginx
                        tls:
                          type: object
                          default:
                            mode: certManager
                          properties:
                            mode:
                              type: string
                              enum:
                                - certManager
                                - existingSecret
                              default: certManager
                            clusterIssuer:
                              type: string
                            tlsSecretName:
                              type: string
                    logging:
                      type: object
                      required:
                        - retentionHours
                        - storage
                        - resources
                      properties:
                        retentionHours:
                          type: integer
                          minimum: 1
                        compactionIntervalMinutes:
                          type: integer
                          minimum: 1
                          default: 15
                        retentionDeleteDelayMinutes:
                          type: integer
                          minimum: 1
                          default: 120
                        coriolisDebug:
                          type: boolean
                          default: false
                        storage:
                          type: object
                          required:
                            - loki
                          properties:
                            loki:
                              type: object
                              required:
                                - storageClassName
                                - size
                              properties:
                                storageClassName:
                                  type: string
                                  minLength: 1
                                size:
                                  type: string
                                  minLength: 1
                        resources:
                          type: object
                          required:
                            - loki
                            - gateway
                            - alloy
                            - adaptor
                          properties:
                            loki:
                              type: object
                              required:
                                - requests
                                - limits
                              properties:
                                requests:
                                  type: object
                                  required:
                                    - cpu
                                    - memory
                                  properties:
                                    cpu:
                                      type: string
                                      minLength: 1
                                    memory:
                                      type: string
                                      minLength: 1
                                limits:
                                  type: object
                                  required:
                                    - cpu
                                    - memory
                                  properties:
                                    cpu:
                                      type: string
                                      minLength: 1
                                    memory:
                                      type: string
                                      minLength: 1
                            gateway:
                              type: object
                              required:
                                - requests
                                - limits
                              properties:
                                requests:
                                  type: object
                                  required:
                                    - cpu
                                    - memory
                                  properties:
                                    cpu:
                                      type: string
                                      minLength: 1
                                    memory:
                                      type: string
                                      minLength: 1
                                limits:
                                  type: object
                                  required:
                                    - cpu
                                    - memory
                                  properties:
                                    cpu:
                                      type: string
                                      minLength: 1
                                    memory:
                                      type: string
                                      minLength: 1
                            alloy:
                              type: object
                              required:
                                - requests
                                - limits
                              properties:
                                requests:
                                  type: object
                                  required:
                                    - cpu
                                    - memory
                                  properties:
                                    cpu:
                                      type: string
                                      minLength: 1
                                    memory:
                                      type: string
                                      minLength: 1
                                limits:
                                  type: object
                                  required:
                                    - cpu
                                    - memory
                                  properties:
                                    cpu:
                                      type: string
                                      minLength: 1
                                    memory:
                                      type: string
                                      minLength: 1
                            adaptor:
                              type: object
                              required:
                                - requests
                                - limits
                              properties:
                                requests:
                                  type: object
                                  required:
                                    - cpu
                                    - memory
                                  properties:
                                    cpu:
                                      type: string
                                      minLength: 1
                                    memory:
                                      type: string
                                      minLength: 1
                                limits:
                                  type: object
                                  required:
                                    - cpu
                                    - memory
                                  properties:
                                    cpu:
                                      type: string
                                      minLength: 1
                                    memory:
                                      type: string
                                      minLength: 1
                status:
                  type: object
                  properties:
                    acceptedVersion:
                      type: string
                      minLength: 1
                    observedGeneration:
                      type: integer
                      format: int64
                      minimum: 0
                    conditions:
                      type: array
                      x-kubernetes-list-type: map
                      x-kubernetes-list-map-keys:
                        - type
                      items:
                        type: object
                        required:
                          - type
                          - status
                          - observedGeneration
                          - lastTransitionTime
                          - reason
                          - message
                        properties:
                          type:
                            type: string
                            minLength: 1
                          status:
                            type: string
                            enum:
                              - "True"
                              - "False"
                              - "Unknown"
                          observedGeneration:
                            type: integer
                            format: int64
                            minimum: 0
                          lastTransitionTime:
                            type: string
                            format: date-time
                          reason:
                            type: string
                            minLength: 1
                          message:
                            type: string
                            minLength: 1
          subresources:
            status: {}
    ```

Helm treats files under a chart's `crds/` directory differently from normal chart templates:

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

1. Apply the `coriolisappliances.coriolis.cloudbase.it` 
&emsp;&emsp;⤷ CRD supplied with the target chart version.
2. Upgrade the operator with Helm.

The order matters because Kubernetes should understand the new schema before the new operator starts using it.

!!! note ""
    This article does not upgrade the operator. The caveat is here to prevent assuming that a future `helm upgrade` will update everything automatically.

## :material-book-open-page-variant-outline: CR Versus Helm Values, And The Two Retention Profiles

Helm values, the CRD, and a CR have three different roles:

- **Helm values** in `coriolis-operator/helm/values.yaml` configure the operator Deployment itself: its image, log level, resources, probes, and security contexts.
- **The CRD** in `coriolis-operator/helm/crds/coriolisappliances.yaml` defines the fields a `CoriolisAppliance` CR may contain, along with their types, required values, defaults, and validation rules.
- **A `CoriolisAppliance` CR** supplies the values for one namespaced appliance runtime: version, storage, ingress, logging, and per-component resources.

The lab uses this appliance CR:

??? quote "coriolis-appliance.yaml"

    ```yaml
    # CoriolisAppliance example, directly applicable to the current
    # approved dev namespace.
    #
    # Prerequisite (not part of this resource): the `coriolis-appliance-registry`
    # secret must already exist in the `coriolis` namespace before applying.
    #
    # Apply with an explicit context and namespace, for example:
    #   kubectl --context virt-infra-dev-buc-hq -n coriolis apply -f coriolis-appliance.yaml
    apiVersion: coriolis.cloudbase.it/v1alpha1
    kind: CoriolisAppliance
    metadata:
      name: coriolis-appliance-advanced
      namespace: coriolis
    spec:
      profile: core
      # Supported immutable Coriolis runtime version deployed by the operator.
      version: "2603.4"
      storage:
        # local-path storage is dev-only: data is bound to a single node and has
        # no backup or failover. Use a production storage class elsewhere.
        mariadb:
          storageClassName: local-path
          size: 10Gi
        rabbitmq:
          storageClassName: local-path
          size: 1Gi
      resources:
        mariadb:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: "1"
            memory: 1Gi
        rabbitmq:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: "1"
            memory: 1Gi
      ingress:
        host: coriolis.app.cloudbase.wiki
        ingressClassName: nginx
        tls:
          mode: certManager
          clusterIssuer: letsencrypt
      logging:
        # retentionHours: logs older than this are marked for deletion.
        retentionHours: 24
        # compactionIntervalMinutes: how often stored log chunks are compacted.
        compactionIntervalMinutes: 15
        # retentionDeleteDelayMinutes: extra grace period before marked data is physically removed,
        # so retention changes can be reverted safely.
        retentionDeleteDelayMinutes: 120
        # coriolisDebug stays false: enabling it raises verbosity of all appliance components and can
        # expose sensitive request detail in logs.
        coriolisDebug: false
        storage:
          # local-path Loki volume is dev-only (single node, no redundancy).
          loki:
            storageClassName: local-path
            size: 10Gi
        resources:
          loki:
            requests:
              cpu: 250m
              memory: 512Mi
            limits:
              cpu: "1"
              memory: 1Gi
          gateway:
            requests:
              cpu: 100m
              memory: 32Mi
            limits:
              cpu: "1"
              memory: 64Mi
          alloy:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 512Mi
          adaptor:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 512Mi
    ```

The operator translates the CR into the runtime resources:

```text
coriolisappliances.yaml (allowed structure)
        |
        v
CoriolisAppliance CR (one appliance's values)
        |
        v
operator reconciliation
        |
        v
Deployments, StatefulSets, Services, Ingresses, Secrets, and PVCs
```

To change an existing appliance setting, edit its CR. To introduce a new configurable field, update both the CRD schema and the operator reconciliation code; editing only the CRD does not implement runtime behavior.

The CR references pull Secrets by name but does not restate them. Those Secrets must already exist before the appliance is deployed.

The CR's three logging knobs answer different questions:

- `retentionHours`: logs older than this are marked for deletion by the compactor.
- `retentionDeleteDelayMinutes`: extra grace period before marked data is physically removed, so a mistaken retention change can be reverted.
- `compactionIntervalMinutes`: how often stored log chunks are compacted.

!!! info ""
    Compaction is Loki's periodic maintenance process: it combines smaller index files into optimized files and marks expired log data for retention cleanup. `compactionIntervalMinutes` controls how often this process runs; physical deletion still waits for `retentionDeleteDelayMinutes`.

The lab asset ships the **practical profile** `24` h / `15` m / `120` m: a day of queryable history, frequent compaction, and a two-hour undo window.

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

The operator turns a `CoriolisAppliance` CR into the resources needed to run the appliance. It creates the dependencies first, runs the bootstrap process, and then deploys the Coriolis services and access resources. If an existing resource with the same name belongs to something else, the operator stops instead of replacing it.

Most resources belong to the CR and are removed with it. Data PVCs and generated credentials are retained so that an appliance recreated with the same name can reuse them.

The operator reports core readiness and logging readiness separately because the logging stack can take longer to become ready.

## :material-book-open-page-variant-outline: Conditions

- `Accepted` - The requested profile and version are supported.
- `Progressing` - Reconciliation or bounded readiness is still in progress.
- `Reconciled` - The desired managed resource set was applied; a collision keeps it false.
- `Ready` - The bounded internal-core readiness observation passed.
- `LoggingReady` - The bounded logging-stack readiness observation passed; it converges independently from `Ready`.
- `Degraded` - A collision, invalid configuration, or failed readiness observation blocks healthy status.
- `Upgradeable` - Whether version changes are supported; it is currently false.

!!! warning
    `Ready=True` alone means only that selected single-replica internal-core checks passed, and even `Ready=True` with `LoggingReady=True` is not migration or production evidence. Neither condition establishes provider connectivity, browser login, migration success, HA, production storage, backup, or production readiness.

## :material-book-open-page-variant-outline: Next Steps And Limitations

Review the [Lab Environment](operator-lab-environment.md), then [Deploy an Appliance](deploy-appliance.md). Continue with [Phase 1: Headless Migration](headless-migration.md), followed by [Phase 2: Web UI Migration](web-ui-migration.md). See [Technical Debt](technical-debt.md) for current limitations and open work.
