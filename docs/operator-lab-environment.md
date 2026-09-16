# Lab Environment

!!! abstract
    This page defines the concrete development lab setup shared by appliance deployment and both ordered migration phases.

## :material-book-open-page-variant-outline: Operator Installation

**Argo CD** (`argocd/coriolis` Application) continuously deploys the operator Helm chart from the OCI registry and keeps the operator Deployment in sync. CIXpress CI publishes chart and image versions, and the live Application selects them through a wildcard chart channel rather than a user-edited pin.

The operator chart's Helm values are applied by Argo CD and are not changed during the lab. See [CR Versus Helm Values, And The Two Retention Profiles](operator.md#cr-versus-helm-values-and-the-two-retention-profiles) for the distinction between operator and appliance configuration.

The lab uses these concrete values:

| Setting | Value |
| --- | --- |
| Kubernetes context | `virt-infra-dev-buc-hq` |
| Namespace | `coriolis` |
| Operator Deployment | `coriolis-operator` |
| Runtime version | `2603.4` |
| Appliance host | `coriolis.app.cloudbase.wiki` |
| TLS Secret | `coriolis.app.cloudbase.wiki-tls` |
| Pull Secrets | `regcred`, `coriolis-appliance-registry` |
| StorageClass | `local-path` |
| IngressClass | `nginx` |
| ClusterIssuer | `letsencrypt` |

The operator is a single reconciler Pod in the `coriolis` namespace and watches `CoriolisAppliance` custom resources. The custom resource is the declaration of intent for the appliance runtime: version, storage, resources, ingress, logging, and retention. The operator does not install storage, ingress, or certificate infrastructure; those are cluster responsibilities.

`regcred` is what the operator chart references via `imagePullSecrets`; `coriolis-appliance-registry` is the prerequisite the appliance itself expects to already exist for its runtime images. The `local-path` storage is dev-only: data is bound to a single node and has no backup or failover. Use a production storage class elsewhere.

Complete the operational prerequisites and checks in [Deploy an Appliance](deploy-appliance.md#hands-on-prerequisites).

## :material-book-open-page-variant-outline: Chosen Appliance Values

The tutorial uses [coriolis-appliance.yaml](assets/manifests/coriolis-appliance.yaml) unchanged. It is written directly against this dev namespace.

| Setting | Value | Why chosen |
| --- | --- | --- |
| `metadata.name` / `namespace` | `coriolis-appliance-advanced` / `coriolis` | Matches the operator namespace and keeps the tutorial isolated by name. |
| `spec.profile` | `core` | The only supported profile today. |
| `spec.version` | `"2603.4"` | The accepted, immutable runtime version the current operator supports. |
| MariaDB / RabbitMQ storage | `local-path`, `10Gi` / `1Gi` | Dev-only single-node storage; sizes proven in prior validations. |
| Ingress | `coriolis.app.cloudbase.wiki`, class `nginx`, TLS via cert-manager `letsencrypt` ClusterIssuer | The managed dev hostname with real ACME certificates. |
| Logging retention | `24` h keep, `15` min compaction, `120` min delete delay | A realistic steady-state profile (see [CR Versus Helm Values, And The Two Retention Profiles](operator.md#cr-versus-helm-values-and-the-two-retention-profiles)). |
| `coriolisDebug` | `false` | Safe default; debug is a bounded diagnostic mode only. |
| Loki storage | `local-path`, `10Gi` | Same dev-only caveat as the databases. |
| Resource bounds: MariaDB, RabbitMQ, Loki | requests `250m` CPU / `512Mi`, limits `1` CPU / `1Gi` | Sized stateful components; explicit bounds keep scheduling predictable on the shared dev node. |
| Resource bounds: logging gateway | requests `100m` / `32Mi`, limits `1` / `64Mi` | Light NGINX sidecar bounds. |
| Resource bounds: Alloy and adaptor | requests `100m` / `128Mi`, limits `500m` / `512Mi` | Log collection and query adapters. |

## :material-book-open-page-variant-outline: Continue The Lab

1. Complete the [deployment lab](deploy-appliance.md) to apply and validate the appliance.
2. Continue with the [headless migration](headless-migration.md).
3. Continue with the [Web UI migration](web-ui-migration.md).
