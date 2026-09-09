# Coriolis Operator Advanced Tutorial

!!! abstract
    This tutorial takes you from an already-installed Coriolis operator in the approved development cluster to a fully Ready, LoggingReady Coriolis appliance you can log into from a browser. The complete tutorial covers appliance bring-up, an optional headless migration, a Web UI migration with observation, and cleanup.

!!! info "Validation record"
    This walkthrough was followed end to end on operator `0.5.59` with runtime `2603.4` in the approved development cluster on 2026-09-09, covering the headless and Web UI OpenStack-to-OpenStack migrations and full cleanup. Execution is tracked checkpoint by checkpoint in the [Coriolis Operator Tutorial Validation Record](operator-tutorial-validation.md). Follow that page's recording rules when you run the tutorial.

!!! info "Estimated time"
    Appliance bring-up typically converges in 5 to 15 minutes. A small migration takes 10 to 30+ minutes, depending on the source and destination cloud. The operator install reference adds time only if you choose to read it closely.

## :material-book-open-page-variant-outline: Mental Model

Four layers cooperate, each owned by a different actor:

1. **Argo CD** (`argocd/coriolis` Application) continuously deploys the operator Helm chart from the OCI registry and keeps the operator Deployment in sync. CIXpress CI publishes chart and image versions, and the live Application selects them through a wildcard chart channel rather than a user-edited pin.
2. **The operator** (a single reconciler Pod in the `coriolis` namespace) watches `CoriolisAppliance` custom resources. It validates the request, then creates dependencies, runs bootstrap, applies workloads, and exposes the runtime through Ingress.
3. **The custom resource** (`CoriolisAppliance`) is your only declaration of intent: runtime version, storage classes and sizes, resource bounds, ingress host and TLS, and logging retention. Its `.status.conditions` are the authoritative progress report.
4. **The runtime** is the set of appliance Pods: MariaDB, RabbitMQ, Memcached, Keystone, Barbican, the Coriolis services (API, Web, Conductor, Scheduler, Transfer Cron, Minion Manager, Deployer Manager, Worker), the logging stack (Loki, gateway, Alloy, adaptor), and the web UI you reach over HTTPS.

You interact with layers 3 and 4 directly, and with layer 1 and 2 only to verify they are healthy.

Two ownership classes matter when inspecting state: most generated resources (Deployments, Services, ConfigMaps, the rebuildable configuration Secret, and Ingresses) are owner-referenced and are recreated with or garbage collected alongside the CR, while the generated credential Secrets and the stateful MariaDB, RabbitMQ, and Loki data PVCs are retained ownerless resources that survive same-name appliance recreation unchanged.

## :material-book-open-page-variant-outline: Safety And Scope

!!! danger "Development environment only"
    Every command in this tutorial targets the explicit context `virt-infra-dev-buc-hq`. Do not run them against any other cluster without a separate, deliberate plan.

- **local-path storage is dev-only.** Data is bound to a single node with no backup, no failover, and no redundancy. Other environments need a production storage class.
- **The operator-deployed Worker runs privileged and as root**, with host mounts for `/dev` and `/lib/modules`. This is a known operational constraint of the migration engine, not a security endorsement. Do not treat the appliance as production-hardened.
- **Migrations write to destinations and can shut down sources.** A running migration mutates real workloads; the source instance may be powered off as part of the flow. This tutorial does not start a migration until its migration sections.
- **Keep `coriolisDebug: false`.** Enabling debug raises verbosity across all appliance components and has historically exposed sensitive request detail in logs.
- **Never force-delete, never edit finalizers or owner references, and never scale operator-owned resources by hand.** The operator is fail-closed on collisions; fighting it only creates more collisions. Normal `kubectl delete` of the appliance CR is the supported cleanup.

## :material-book-open-page-variant-outline: Operator Install Reference (Skippable)

!!! tip "Skip ahead if the operator is already deployed"
    If the next section's checks pass, the operator is already installed and managed by Argo CD. This section exists only so you understand what is installed and how you *could* install it yourself.

The live pattern is the Argo CD Application that syncs the operator chart from OCI with a wildcard `targetRevision` channel selector, automated sync, and no prune or selfHeal. The example manifest is [coriolis-operator-application.example.yaml](assets/manifests/coriolis-operator-application.example.yaml).

The operator's own runtime knobs (log level, resources, security contexts, probes, and the `regcred` pull secret) are shown in [coriolis-operator-values.example.yaml](assets/manifests/coriolis-operator-values.example.yaml). These values are the chart defaults; passing them is optional. Do not add image repository or tag overrides there: as an ordinary user you do not edit the CI-owned `Chart.yaml` version, `appVersion`, or `values.yaml` image metadata. Selecting a published chart version at install time is different and is allowed, as the command below shows.

A direct Helm install is equivalent to what Argo CD does, using a concrete chart version you obtain from the OCI registry rather than inventing one:

<!-- Install or update the operator chart from the OCI registry with the example values (reference only; the dev cluster uses Argo CD). -->
```bash
helm upgrade --install coriolis-operator oci://cr.virtomat.io/virtomat/coriolis/helm/coriolis-operator --version <OPERATOR_CHART_VERSION> --namespace coriolis --create-namespace --values docs/assets/manifests/coriolis-operator-values.example.yaml
```

??? example "Expected result"

    ```text
    Release "coriolis-operator" does not exist. Installing it now.
    NAME: coriolis-operator
    LAST DEPLOYED: <TIMESTAMP>
    NAMESPACE: coriolis
    STATUS: deployed
    REVISION: 1
    ```

## :material-book-open-page-variant-outline: CRD First Install And Upgrade Caveat

Helm installs CRDs from the chart's `crds/` directory on first install only. Helm never upgrades or removes CRDs, so an operator chart upgrade that changes the `CoriolisAppliance` schema does not update the schema by itself. The CRD carries an explicit upgrade note to this effect.

The consequence for you: before any operator chart upgrade, the new `coriolisappliances.coriolis.cloudbase.it` CRD must be applied separately from the chart sources (for example `kubectl apply -f` of the CRD file in the chart you are upgrading to). In this tutorial you only verify the CRD exists; you never upgrade the operator.

## :material-book-open-page-variant-outline: Hands-On Prerequisites

Run each check and compare with the expected result before continuing. Any mismatch means stop and fix the prerequisite, not the tutorial.

### :material-application-edit-outline: Repository Location

All file paths in this tutorial are relative to the repository root, so apply the asset from there.

<!-- Confirm the current working directory is the repository root. -->
```bash
pwd
```

??? example "Expected result"

    ```text
    /home/radu/Dev/cb-coriolis
    ```

### :material-application-edit-outline: Argo CD Application

<!-- Verify the shared coriolis Application is Synced and Healthy. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n argocd get application coriolis
```

??? example "Expected result"

    ```text
    NAME       SYNC STATUS   HEALTH STATUS
    coriolis   Synced        Healthy
    ```

### :material-application-edit-outline: Operator Deployment And CRD

<!-- Verify the operator Deployment is running in the coriolis namespace. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis get deployment coriolis-operator
```

??? example "Expected result"

    ```text
    NAME                READY   UP-TO-DATE   AVAILABLE   AGE
    coriolis-operator   1/1     1            1           <AGE>
    ```

The operator Pod should show zero restarts in the cluster baseline; sustained restarts mean stop and investigate before deploying an appliance.

<!-- Verify the CoriolisAppliance CRD is registered. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis get crd coriolisappliances.coriolis.cloudbase.it
```

??? example "Expected result"

    ```text
    NAME                                      CREATED AT
    coriolisappliances.coriolis.cloudbase.it   <CREATED_AT>
    ```

### :material-application-edit-outline: Namespace Pull Secrets

Both registry pull Secrets must exist in the `coriolis` namespace. Query name and type only; never decode or print Secret data.

<!-- List only the names and types of the two required pull Secrets. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis get secret regcred coriolis-appliance-registry -o custom-columns=NAME:.metadata.name,TYPE:.type
```

??? example "Expected result"

    ```text
    NAME                         TYPE
    regcred                      kubernetes.io/dockerconfigjson
    coriolis-appliance-registry   kubernetes.io/dockerconfigjson
    ```

`regcred` is what the operator chart references via `imagePullSecrets`; `coriolis-appliance-registry` is the prerequisite the appliance itself expects to already exist for its runtime images.

### :material-application-edit-outline: Cluster Services

The operator does not install storage, ingress, or certificate infrastructure. Confirm the three cluster services the appliance values will reference. These resources are cluster-scoped; the `-n coriolis` flag is ignored by kubectl there and is included only to keep the project convention of an explicit namespace on every dev kubectl command.

<!-- Verify the dev local-path StorageClass exists. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis get storageclass local-path
```

??? example "Expected result"

    ```text
    NAME                   PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
    local-path (default)   rancher.io/local-path   Delete          WaitForFirstConsumer   false                  <AGE>
    ```

<!-- Verify the nginx IngressClass exists. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis get ingressclass nginx
```

??? example "Expected result"

    ```text
    NAME    CONTROLLER             PARAMETERS   AGE
    nginx   k8s.io/ingress-nginx    <none>      <AGE>
    ```

<!-- Verify the letsencrypt ClusterIssuer is Ready. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis get clusterissuer letsencrypt -o jsonpath='{.metadata.name}{" ready="}{.status.conditions[?(@.type=="Ready")].status}{"\n"}'
```

??? example "Expected result"

    ```text
    letsencrypt ready=True
    ```

### :material-application-edit-outline: No Existing Appliance CR

The chosen appliance name must be free; the operator fails closed on collisions rather than adopting foreign resources.

<!-- Confirm no coriolis-appliance-advanced CR exists yet. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis get coriolisappliance coriolis-appliance-advanced
```

??? example "Expected result"

    ```text
    Error from server (NotFound): coriolisappliances.coriolis.cloudbase.it "coriolis-appliance-advanced" not found
    ```

A `NotFound` here is the success condition. If the CR already exists, stop and reconcile with its owner instead of double-applying.

## :material-book-open-page-variant-outline: Chosen Appliance Values

The tutorial uses [coriolis-appliance-advanced.yaml](assets/manifests/coriolis-appliance-advanced.yaml) unchanged. It is written directly against this dev namespace.

| Setting | Value | Why chosen |
| --- | --- | --- |
| `metadata.name` / `namespace` | `coriolis-appliance-advanced` / `coriolis` | Matches the operator namespace and keeps the tutorial isolated by name. |
| `spec.profile` | `core` | The only supported profile today. |
| `spec.version` | `"2603.4"` | The accepted, immutable runtime version the current operator supports. |
| MariaDB / RabbitMQ storage | `local-path`, `10Gi` / `1Gi` | Dev-only single-node storage; sizes proven in prior validations. |
| Ingress | `coriolis.app.cloudbase.wiki`, class `nginx`, TLS via cert-manager `letsencrypt` ClusterIssuer | The managed dev hostname with real ACME certificates. |
| Logging retention | `24` h keep, `15` min compaction, `120` min delete delay | A realistic steady-state profile (see next section). |
| `coriolisDebug` | `false` | Safe default; debug is a bounded diagnostic mode only. |
| Loki storage | `local-path`, `10Gi` | Same dev-only caveat as the databases. |
| Resource bounds: MariaDB, RabbitMQ, Loki | requests `250m` CPU / `512Mi`, limits `1` CPU / `1Gi` | Sized stateful components; explicit bounds keep scheduling predictable on the shared dev node. |
| Resource bounds: logging gateway | requests `100m` / `32Mi`, limits `1` / `64Mi` | Light NGINX sidecar bounds. |
| Resource bounds: Alloy and adaptor | requests `100m` / `128Mi`, limits `500m` / `512Mi` | Log collection and query adapters. |

## :material-book-open-page-variant-outline: CR Versus Helm Values, And The Two Retention Profiles

!!! note "Two different configuration channels"
    The operator chart's Helm values (see the values example above) configure the **operator process itself**: its log level, resources, probes, and security contexts. They are applied by Argo CD and you do not touch them in this tutorial. The `CoriolisAppliance` custom resource is a complete, self-contained declaration of the **appliance runtime**: version, storage, ingress, logging, and per-component resources. The CR references pull Secrets by name but does not restate them; they must already exist, which the prerequisites confirmed.

The CR's three logging knobs answer different questions:

| Key | Meaning |
| --- | --- |
| `retentionHours` | Logs older than this are marked for deletion by the compactor. |
| `retentionDeleteDelayMinutes` | Extra grace period before marked data is physically removed, so a mistaken retention change can be reverted. |
| `compactionIntervalMinutes` | How often stored log chunks are compacted. |

The asset ships the **practical profile** `24` h / `15` m / `120` m: a day of queryable history, frequent compaction, and a two-hour undo window. Prior qualification runs instead used a deliberately compressed **test profile** of `1` h / `1` m / `5` m so that retention expiry and physical deletion could be observed within a single session. Both are valid inputs; the test profile exists to make retention provable, not to be left in place. This tutorial keeps the practical values because you are standing up something to live in, not benchmarking deletion.

## :material-book-open-page-variant-outline: Apply The Appliance

From the repository root, apply the asset exactly as committed:

<!-- Create the CoriolisAppliance from the tutorial asset. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis apply -f docs/assets/manifests/coriolis-appliance-advanced.yaml
```

??? example "Expected result"

    ```text
    coriolisappliance.coriolis.cloudbase.it/coriolis-appliance-advanced created
    ```

## :material-book-open-page-variant-outline: Wait For Ready, Then LoggingReady

Reconciliation stages the core runtime first and the logging stack alongside it, but the conditions flip independently. Wait for each with its own bounded timeout rather than polling by eye. The whole converge typically takes around five minutes; `15m` is generous slack.

<!-- Wait for the core runtime Ready condition. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis wait --for=condition=Ready --timeout=15m coriolisappliance/coriolis-appliance-advanced
```

??? example "Expected result"

    ```text
    coriolisappliance.coriolis.cloudbase.it/coriolis-appliance-advanced condition met
    ```

<!-- Wait for the independent LoggingReady condition. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis wait --for=condition=LoggingReady --timeout=15m coriolisappliance/coriolis-appliance-advanced
```

??? example "Expected result"

    ```text
    coriolisappliance.coriolis.cloudbase.it/coriolis-appliance-advanced condition met
    ```

If either wait times out, jump to the condition inspection below and read the blocking condition's `reason` and `message` before retrying anything.

## :material-book-open-page-variant-outline: Inspect The Runtime

### :material-application-edit-outline: Conditions

The status block, not the Pod list, is the operator's own verdict. Extract only type, status, and reason: these fields never contain secret values.

<!-- Show all appliance conditions in one safe line each. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis get coriolisappliance coriolis-appliance-advanced -o json | jq -r '.status.conditions[] | "\(.type)=\(.status) reason=\(.reason)"'
```

??? example "Expected result"

    ```text
    Accepted=True reason=<REASON>
    Progressing=False reason=<REASON>
    Reconciled=True reason=<REASON>
    Ready=True reason=<REASON>
    Degraded=False reason=<REASON>
    Upgradeable=False reason=UpgradeNotSupported
    LoggingReady=True reason=<REASON>
    ```

The gate is the status combination, not the reason text: `Accepted`, `Reconciled`, `Ready`, and `LoggingReady` must be `True`, `Progressing` and `Degraded` must be `False`, and `Upgradeable` is expected `False` for this release. Reasons are the operator's internal detail; `UpgradeNotSupported` is shown as the expected example.

### :material-application-edit-outline: Pods

Every resource owned by the appliance carries the label `coriolis.cloudbase.it/appliance=coriolis-appliance-advanced`.

<!-- List the appliance Pods by label. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis get pods -l coriolis.cloudbase.it/appliance=coriolis-appliance-advanced
```

??? example "Expected result"

    ```text
    NAME                                                        READY   STATUS      RESTARTS   AGE
    coriolis-appliance-advanced-adaptor-...                     1/1     Running     0          <AGE>
    coriolis-appliance-advanced-alloy-...                       1/1     Running     0          <AGE>
    coriolis-appliance-advanced-barbican-api-...                1/1     Running     0          <AGE>
    coriolis-appliance-advanced-barbican-worker-...             1/1     Running     0          <AGE>
    coriolis-appliance-advanced-common-bootstrap-v3-...         0/1     Completed   0          <AGE>
    coriolis-appliance-advanced-coriolis-api-...                1/1     Running     0          <AGE>
    coriolis-appliance-advanced-coriolis-conductor-...          1/1     Running     0          <AGE>
    coriolis-appliance-advanced-coriolis-deployer-manager-...   1/1     Running     0          <AGE>
    coriolis-appliance-advanced-coriolis-minion-manager-...     1/1     Running     0          <AGE>
    coriolis-appliance-advanced-coriolis-scheduler-...          1/1     Running     0          <AGE>
    coriolis-appliance-advanced-coriolis-transfer-cron-...      1/1     Running     0          <AGE>
    coriolis-appliance-advanced-coriolis-web-...                1/1     Running     0          <AGE>
    coriolis-appliance-advanced-coriolis-worker-...             1/1     Running     0          <AGE>
    coriolis-appliance-advanced-keystone-...                    1/1     Running     0          <AGE>
    coriolis-appliance-advanced-loki-0                          2/2     Running     0          <AGE>
    coriolis-appliance-advanced-mariadb-0                       1/1     Running     0          <AGE>
    coriolis-appliance-advanced-memcached-...                   1/1     Running     0          <AGE>
    coriolis-appliance-advanced-rabbitmq-0                      1/1     Running     0          <AGE>
    ```

The label filter must return **18 appliance Pods: 17 `Running` plus exactly one `Completed` (phase `Succeeded`) bootstrap Job Pod, with zero restarts**. The namespace-wide total is 19 Pods because the already-running operator Pod joins it but carries operator labels, not the appliance label. Any `CrashLoopBackOff`, restart, or missing appliance Pod blocks the tutorial; read the relevant condition and Pod logs before acting.

### :material-application-edit-outline: PVCs, Ingresses, And Certificate

<!-- List the appliance PersistentVolumeClaims. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis get pvc
```

??? example "Expected result"

    ```text
    NAME                                        STATUS   VOLUME     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
    coriolis-appliance-advanced-loki-data       Bound    <PV>       10Gi       RWO            local-path     <unset>                 <AGE>
    coriolis-appliance-advanced-mariadb-data    Bound    <PV>       10Gi       RWO            local-path     <unset>                 <AGE>
    coriolis-appliance-advanced-rabbitmq-data   Bound    <PV>       1Gi        RWO            local-path     <unset>                 <AGE>
    ```

Exactly **three Bound PVCs**, created as direct resources with the names above (MariaDB, RabbitMQ, and Loki data), each `RWO` on `local-path` with `VOLUMEATTRIBUTESCLASS` `<unset>`. They are retained ownerless claims, so same-name recreation reuses them instead of reprovisioning.

<!-- List the appliance Ingress resources. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis get ingress
```

??? example "Expected result"

    ```text
    NAME                                          CLASS   HOSTS                          ADDRESS        PORTS     AGE
    coriolis-appliance-advanced-adaptor           nginx   coriolis.app.cloudbase.wiki   <INGRESS_IP>   80, 443   <AGE>
    coriolis-appliance-advanced-barbican-api      nginx   coriolis.app.cloudbase.wiki   <INGRESS_IP>   80, 443   <AGE>
    coriolis-appliance-advanced-coriolis-api      nginx   coriolis.app.cloudbase.wiki   <INGRESS_IP>   80, 443   <AGE>
    coriolis-appliance-advanced-coriolis-web      nginx   coriolis.app.cloudbase.wiki   <INGRESS_IP>   80, 443   <AGE>
    coriolis-appliance-advanced-keystone          nginx   coriolis.app.cloudbase.wiki   <INGRESS_IP>   80, 443   <AGE>
    ```

Five Ingress resources, all on the same host, one per routed service. Only the `coriolis-appliance-advanced-coriolis-web` Ingress carries the cert-manager ClusterIssuer annotation, so it is the resource that drives certificate issuance; the `coriolis-appliance-advanced-adaptor` Ingress serves the `/logs` and `/log-stream` routes.

<!-- Check the cert-manager Certificate readiness. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis get certificate
```

??? example "Expected result"

    ```text
    NAME                              READY   SECRET                            AGE
    coriolis.app.cloudbase.wiki-tls   True    coriolis.app.cloudbase.wiki-tls   <AGE>
    ```

The gate is one `Ready=True` Certificate whose `SECRET` is the TLS Secret for the configured host; the ingressed Secret name follows the ingress-shim `<host>-tls` convention. The issuer behind it is the `letsencrypt` ClusterIssuer annotated on the web Ingress (see above); the `get certificate` table itself does not show an `ISSUER` column.

### :material-application-edit-outline: HTTPS And Routes

<!-- Confirm the public endpoint answers with HTTP 200 over TLS. -->
```bash
curl --fail --silent --show-error -o /dev/null -w "%{http_code}\n" https://coriolis.app.cloudbase.wiki/
```

??? example "Expected result"

    ```text
    200
    ```

A `200` with a hostname-valid certificate proves the Ingress, the TLS Certificate, and the web frontend are all serving. The appliance exposes these routes on that host:

| Route | Serves |
| --- | --- |
| `/` | Coriolis web UI |
| `/identity` | Keystone authentication API |
| `/coriolis` | Coriolis API |
| `/barbican` | Barbican secrets API |
| `/logs`, `/log-stream` | Authenticated log list, download, and streaming APIs served by the logging adaptor |

!!! warning
    The next command prints a real credential to your terminal. That is acceptable only because this is the approved development environment; never run it while screen-sharing, in CI output, or against Production, and never paste the value anywhere.

<!-- Read the generated Keystone admin password from the appliance credentials Secret (dev only). -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis get secret coriolis-appliance-advanced-infrastructure-credentials -o jsonpath='{.data.keystone_admin_password}' | base64 -d
```

??? example "Expected result"

    ```text
    <GENERATED_ADMIN_PASSWORD>
    ```

The operator generates this credential once and retains it across same-name appliance recreations; the value is random per appliance. Use it directly for this development session only, and never store it in tracked files, notes, or command output.

## :material-book-open-page-variant-outline: Web Login And Visual Inspection

1. Open `https://coriolis.app.cloudbase.wiki/` in a browser.
   **Expected outcome:** the Coriolis web UI loads over HTTPS with a valid TLS certificate (no browser warning) and presents a Welcome screen with privacy and end-user license agreement (EULA) checkboxes and a **Submit** button.
2. Select both the privacy and EULA checkboxes, then click **Submit**.
   **Expected outcome:** the UI proceeds to `/login`, which offers only `Username` and `Password` fields and a **Login** button (there is no domain field on this form).
3. Log in with username `admin` and the `keystone_admin_password` you just displayed.
   **Expected outcome:** authentication succeeds and the Dashboard loads with a Signed in indicator, in an empty or near-empty state, because this fresh appliance has no endpoints or transfers yet.
4. Use the sidebar navigation labels **Transfers**, **Deployments**, and **Cloud Endpoints** to open each area without creating anything.
   **Expected outcome:** pages render without error banners; the transfer, deployment, and endpoint lists are empty. This confirms the UI can talk to the Coriolis API and Keystone through the ingress.
5. From the already-loaded and authenticated web UI, click the **Logs** navigation item (UI route `/logging`) rather than browsing directly to the host `/logs` path (those adaptor APIs require the UI's authenticated session).
   **Expected outcome:** the log viewer loads and queries the adaptor successfully, listing the appliance components (for example conductor, scheduler, API, web), confirming the Loki-backed logging path end to end.

!!! note "Licence Card In This Core Profile"
    The Dashboard's **Current Licence** card reports an error in this deployment: `/licensing/appliances` falls through to the Web UI and returns HTML, not a licensing API response. The core operator profile does not deploy a licensing backend or configure `LICENSING_SERVER_BASE_URL` for the conductor. Do not treat HTTP 200 on `/licensing` as a healthy licensing service or generalize this development configuration to a licensed production deployment.

!!! tip "Checkpoint"
    At this point you have a Ready and LoggingReady appliance with zero-restart Pods, three Bound PVCs, a trusted HTTPS endpoint, and a working browser login to the Dashboard with empty Transfers, Deployments, and Cloud Endpoints lists and a reachable Logs page. Stop here for now; endpoint registration and the first migration continue in the next section.

## :material-book-open-page-variant-outline: OpenStack Migration Prerequisites

!!! danger "Migrations write real state and can shut down the source"
    Every action in the remaining sections operates on real OpenStack clouds. A transfer execution copies disk data, creates destination resources, and the selected execution options power the source VM off. Prepare only a small, disposable, volume-backed fixture you own and can destroy.

The migration path here is a single OpenStack-to-OpenStack live migration of one disposable VM. The provider contract and stage boundaries live in [OpenStack Context](openstack-provider.md) and [Migration Flow](migration-flow.md); this table is the concrete preflight for this tutorial.

| Input | Why it is needed | Expected preflight result |
| --- | --- | --- |
| One small disposable volume-backed source VM with a known marker (a unique file on its boot volume) | Proves the disk actually moved and the destination boots your state | VM is `ACTIVE`, exactly one attached volume is marked bootable and `in-use`, and the marker is verified -- either read inside the guest (for example over SSH) or proven hypervisor-side from the server's serial console output (for example a cloud-init `runcmd` line plus a `final_message` completion line fetched through the Compute API). |
| Source project permission for Cinder backups plus Swift object storage | The selected export mechanism (`swift_backups`) stages disk data through Cinder backups read from Swift | Both APIs are available to the endpoint project. The controlled fixture migration must then demonstrate successful Cinder-backup/Swift replication in its task progress; API discovery alone is not data-path proof. |
| Destination project quota for volumes, snapshots, ports, floating IPs, and temporary worker VMs | Transfer and deployment create real destination and temporary resources | Quota headroom covers the fixture disks plus one temporary worker VM and its port. |
| Visible destination Linux image for temporary workers | Worker VMs boot from it and must initialize on first boot (cloud-init or config drive) | Image is shared to or present in the endpoint project and boots. |
| Visible destination worker network, flavor, and security group | The temporary worker VM needs a management path back to the OpenStack APIs | Each resource exists in the endpoint project; the security group permits the required API and data paths. |
| Destination keypair | The worker VM and the migrated VM are launched with it | Keypair exists in the endpoint project. |
| Destination floating-IP pool(s) | Worker reachability and the migrated VM's own floating IP | Pool has free addresses visible to the project. |
| Destination volume type for worker boot volumes, if workers boot from volume | Placement of temporary worker storage | Type is visible; `__DEFAULT__` placement is otherwise acceptable. |
| A destination network mapped for every source NIC | A missing per-interface mapping blocks deployment | Each source network name is matched to a destination network ID up front. |
| API connectivity from the appliance to both clouds' identity and service endpoints | Conductor and Worker call both APIs | `Validate and save` in the next section reports the endpoint valid. |

!!! note
    Confirm source and destination resource visibility with project-scoped credentials before creating endpoints. The endpoint project, not an administrator account, must see every image, network, flavor, security group, keypair, pool, and volume type listed above.

!!! note "Source Floating IPs Are Not Required By `swift_backups`"
    Coriolis requests source Cinder backups and reads the staged data through Swift APIs; this path does not require SSH into the source VM. Verify the source marker through a guest read or a serial-console check without borrowing an unrelated floating IP. The destination pool still needs free addresses for temporary workers and the migrated guest. Quota headroom alone does not prove that its external subnet allocation pool has free addresses.

## :material-book-open-page-variant-outline: Create Source And Destination Endpoints

Create both endpoints through the Web UI before any headless test: the headless helper only works against existing, validated endpoints.

1. In the web UI, open **Cloud Endpoints**, choose **Add Endpoint** on an empty list or **New > Endpoint**, then select the **OpenStack** logo.
   **Expected outcome:** the endpoint creation form appears with OpenStack connection fields.
2. Give the endpoint a distinct name. Change **Identity API Version** from its default `2` to `3`, then provide the source username, password, project name, auth URL (normally ending `/v3`), user domain, and project domain. Domain fields appear after selecting version `3`; use domain names when the selector says **Name**. Supply region and interface in **Advanced** only when required.
   **Expected outcome:** all required fields are accepted and the **Validate and save** button becomes enabled.
3. Click **Validate and save**, open the saved endpoint's details, and click **Validate Endpoint**.
   **Expected outcome:** the creation form closes and the endpoint appears in the list. The explicit validation dialog then shows `Endpoint is Valid` and `All tests passed succesfully.` Click **Dismiss** and use the details back arrow to return to the list.
4. Repeat steps 1 to 3 for the destination cloud with its own credentials.
   **Expected outcome:** a second endpoint listed with `Endpoint is Valid`.
5. Open each endpoint's details page and record the non-secret endpoint ID shown in the page URL or details for the headless config file.
   **Expected outcome:** you hold two endpoint ID strings; no credential value is recorded anywhere.

!!! tip "Where the credentials actually live"
    The operator-managed Barbican on this appliance stores the encrypted connection payload as a Barbican secret; the Coriolis endpoint object itself contains only the returned `secret_ref`. That is why the UI reports the endpoint valid only after both the secret is `ACTIVE` and the provider connection test succeeds, and why deleting the endpoint is expected to remove its Barbican-backed credential as part of cleanup.

## :material-book-open-page-variant-outline: Optional Headless Real Migration

!!! danger "This is a real migration"
    Running the helper creates a Transfer, executes it against both live clouds, deploys the destination VM, and can shut down the source. Use it only with the disposable fixture from the prerequisites section. The helper performs one migration, never any cleanup, and leaves the transfer, execution, deployment, and all cloud objects visible in the Web UI for observation.

The helper `deploy/coriolis-headless-migration.py` works only against the two existing validated endpoints from the previous section. Its configuration contract is [headless-migration.example.json](assets/manifests/headless-migration.example.json).

### :material-application-edit-outline: Prepare The Config File

The edited config contains real cloud identifiers, so keep it in `.openstack/tutorial-validation/` at the repository root. The `.openstack/` directory is repository-ignored; never force-add private files or include their contents in documentation.

<!-- Create the private, repository-ignored tutorial workspace. -->
```bash
mkdir -p .openstack/tutorial-validation
```

??? example "Expected result"

    ```text
    No output.
    ```

<!-- Copy the example config into the private ignored workspace. -->
```bash
cp docs/assets/manifests/headless-migration.example.json .openstack/tutorial-validation/headless-migration.json
```

??? example "Expected result"

    ```text
    No output.
    ```

In `.openstack/tutorial-validation/headless-migration.json`, replace **every** `<...>` placeholder with a real value; the helper refuses to run while any placeholder remains (`config_unresolved_placeholder`). The keys mean:

| Key | What to set |
| --- | --- |
| `transfer.notes` | A unique label for this run; the helper preflights that no transfer or deployment already carries it. |
| `transfer.origin_endpoint_id` / `destination_endpoint_id` | The two endpoint IDs you recorded from the Web UI. |
| `transfer.instances` | The fixture VM's source instance ID. |
| `source_environment.replica_export_mechanism` | `swift_backups`, matching the source permissions you verified. |
| `destination_environment.migr_image_map.linux`, `migr_network`, `migr_flavor_name`, `migr_fip_pool_name`, `security_groups`, `keypair_name`, `migr_worker_volume_type` | The destination temporary-worker resources: Linux image ID, network ID, flavor name, floating-IP pool, worker security group, keypair, and worker volume type (`__DEFAULT__` if unset placement is fine). |
| `destination_environment.use_floating_ip` / `floating_ip_pool` | Whether and from which pool the migrated destination VM gets its own floating IP. |
| `network_map` | One entry per source NIC: each source network name mapped to a destination network ID. |
| `storage_mappings` | `{"default": "__DEFAULT__"}` to let the destination place disks. |
| `clone_disks` | `true` for this POC path. |
| `skip_os_morphing` | `true` **only** for the known-compatible disposable fixture; use `false` otherwise. |
| `execution.shutdown_instances` / `auto_deploy` | `true` / `true` for this tutorial flow: shut the source down and deploy automatically. |

<!-- Parse the edited config to catch JSON syntax errors before any API call. -->
```bash
python3 -m json.tool .openstack/tutorial-validation/headless-migration.json > /dev/null
```

??? example "Expected result"

    ```text
    No output.
    ```

### :material-application-edit-outline: Run The Headless Migration

Use the same Keystone project as the Web UI: this walkthrough logs in as `admin` in project `admin`. The helper defaults to `coriolis` in project `service`, which cannot see these UI-created endpoints; the explicit `--username admin --project-name admin` options below are required. The pipeline reads the corresponding admin password from the retained infrastructure Secret directly into stdin without printing it. The public `/identity` and `/coriolis` bases already include the Ingress version rewrites, so the helper appends only `/auth/tokens` and `/<project_id>` itself.

The helper currently authenticates both the user and project in Keystone's `Default` domain; other domains are outside this example's supported scope.

<!-- Feed the Keystone admin password into the helper in the same project as the Web UI. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis get secret coriolis-appliance-advanced-infrastructure-credentials -o jsonpath='{.data.keystone_admin_password}' | base64 -d | python3 deploy/coriolis-headless-migration.py --api-base https://coriolis.app.cloudbase.wiki/coriolis --keystone-base https://coriolis.app.cloudbase.wiki/identity --username admin --project-name admin --config .openstack/tutorial-validation/headless-migration.json --timeout 1800 --poll-interval 10 --run
```

??? example "Expected result"

    ```text
    PASS preflight
    PASS transfer id=<TRANSFER_ID>
    PASS execution id=<EXECUTION_ID> status=COMPLETED
    PASS deployment id=<DEPLOYMENT_ID> status=COMPLETED
    SUMMARY headless-migration passed
    ```

The helper's output contract is fixed and safe to keep on screen:

- It prints only the `PASS` lines above and the final `SUMMARY`; no password, token, request payload, or error body is ever printed.
- `--timeout 1800` is a per-phase polling budget (execution, deployment discovery, deployment), not a total run limit.
- GET-only polling tolerates up to three consecutive transient network failures; POST requests are never retried.
- Writes are never blindly retried: an ambiguous transfer or execution POST fails with the fixed `post_ambiguous` category instead of guessing.
- The unique `notes` value is collision-checked against existing transfers and deployments during preflight, so a second run with the same notes is refused.
- Nothing is cleaned up: objects and cloud resources remain for the observation and cleanup sections.
- Any `ERROR category=...` line is terminal: stop, record the category, and diagnose before re-running.

## :material-book-open-page-variant-outline: Observe The Headless Result

Verify the same facts a UI-driven run would show, through the Web UI and the clouds:

1. Open **Cloud Endpoints**.
   **Expected outcome:** both endpoints still list as valid and usable.
2. Open the migrations area and find the transfer matching your unique notes; open its executions.
   **Expected outcome:** the single transfer execution shows `COMPLETED`.
3. Open the correlated deployment (same notes, deployed automatically).
   **Expected outcome:** the deployment and its last execution show `COMPLETED`.
4. Expand the execution and deployment task timelines.
   **Expected outcome:** every task is completed; no task is in `ERROR`.
5. Check the source VM in the source cloud.
   **Expected outcome:** it is `SHUTOFF`, because `shutdown_instances` was `true`.
6. Check the destination VM in the destination cloud: power state, attached cloned boot disk, mapped networks, floating IP if requested, security groups, and the marker file inside the guest.
   **Expected outcome:** the VM is `ACTIVE` with the expected disks and networking, and the marker is reachable (for example over its floating IP and keypair). In this run the guest security groups contained the dedicated group plus the existing default group, and the cloned boot volume reported 9Gi on the destination against a nominal 8Gi source disk because the provider rounds sizes up: compare disk content and layout, not the exact nominal size.
7. Open the Logs navigation and browse the appliance components around the migration window.
   **Expected outcome:** conductor, scheduler, worker, and deployer activity is visible for the run; you never search logs for secret values to confirm any of this.

!!! warning "Completion is not usability"
    `COMPLETED` statuses prove the Coriolis workflow finished. Guest usability is a separate conclusion you only reach from step 6: boot state, disks, networking, and your marker.

## :material-book-open-page-variant-outline: Reset Before Repeating In The Web UI

If you ran the headless migration, do not start the walkthrough below on top of its leftovers.

1. Perform the [Migration Cleanup](#migration-cleanup) section first, for the headless transfer, deployment, disks, and cloud artifacts, but intentionally skip its endpoint-deletion step: this reset keeps both endpoints.
   **Expected outcome:** no headless transfer, deployment, or migration artifacts remain. Keep the fixture infrastructure and both endpoints; an empty run-created Swift export container may also be kept for the repeat, then removed during final cleanup.
2. Intentionally restore the fixture: restart, recreate, or rebuild the disposable source VM so it is `ACTIVE` with the marker again, on the same source network.
   **Expected outcome:** the source VM matches the prerequisites table again.
3. Remove or keep the destination VM according to who owns the test result; it is a real VM, not an automatic leftover.
   **Expected outcome:** the destination project state is a deliberate choice, not an accident.
4. Keep both endpoints.
   **Expected outcome:** the UI walkthrough below can reuse the validated endpoints without re-entering credentials.

## :material-book-open-page-variant-outline: Full Web UI Migration Walkthrough

!!! note "Session and URL cautions"
    A long pause anywhere in the wizard can expire the authenticated session; treat step failures that look like lost state as a session problem rather than a wizard bug. Never share the wizard's URL between steps: it encodes wizard state that contains resource IDs and references.

1. From the dashboard choose **New > Transfer**.
   **Expected outcome:** the transfer wizard opens with the **Coriolis Migration** scenario selected by default (the `live_migration` scenario).
2. Keep **Migration** selected and click **Next**.
   **Expected outcome:** the source cloud step appears. Remember a migration is a move, not a zero-downtime live re-place, and the backup-based disk path stages source data through Cinder backups in Swift.
3. On the source cloud step, pick the existing source endpoint from the **Select** dropdown under the OpenStack logo, then click **Next**; do not click the logo itself.
   **Expected outcome:** the source options step appears for that endpoint.
4. Confirm the source options show the **Swift Backups** export mechanism, then click **Next**.
   **Expected outcome:** the wizard presents the mechanism consistent with the permissions you preflighted.
5. On the VM selection step, choose only the disposable fixture, verify **1 instance selected**, and click **Next**.
   **Expected outcome:** the destination cloud step appears with the instance inventory (disks and NICs) loaded.
6. On the destination cloud step, pick the existing destination endpoint from its **Select** dropdown and click **Next**.
   **Expected outcome:** the target options step appears.
7. In the simple target options set: a unique **Title** (this run's notes), the worker **Migration Flavor** name `c1.small` (a searchable field), the Linux entry of the **Migration Image Map** (in this validated run the `ubuntu-24.04` image, matching the source and destination guest OS), and the dedicated **Migration Network**.
   **Expected outcome:** the form accepts every worker field.
8. Expand the target options **Advanced** section to reach the remaining fields: **Keypair Name**, **Security Groups**, **Floating IP Pool**, **Use Floating IP**, **Migration Floating IP Pool Name**, **Migration Worker Use FIP**, **Migration Worker Volume Type** (set `__DEFAULT__`), and **Preserve Fixed IPs**. Wherever a pool dropdown lists candidates, its labels are network/subnet pairs (for example `ext_net_gts/ext_subnet_gts`); choose the IPv4 entry, not the IPv6 one.
   **Expected outcome:** every advanced field is accepted and each pool selection resolves to an IPv4 network/subnet label.
9. Set the tri-state toggles: both **Use Floating IP** and **Migration Worker Use FIP** to **Yes**, and **Preserve Fixed IPs** to **No**. The switch reads left = No, middle = not set, right = Yes; verify each displayed value, then click **Next**.
   **Expected outcome:** each toggle's visible text matches its intended value.
10. On the networks step, map every source NIC: each source network name is matched to a destination network selection; no interface may be left unmapped.
    **Expected outcome:** each source network has a destination mapping.
11. On the storage step, set **Default Storage** to `__DEFAULT__` and leave backend and per-disk entries at their **Default**, which inherits it.
    **Expected outcome:** storage mappings show the default everywhere.
12. Skip the scripts step (empty is fine for the fixture) and the schedule step without clicking **Add Schedule**.
    **Expected outcome:** the wizard advances to the execute step with no scripts and no schedule.
13. On the execute step choose **Execute Now**. **Clone Disks** starts at **Yes**; **Shutdown Instances**, **Auto Deploy**, and **Skip OS Morphing** start at **No** -- set all three to **Yes** only for the known-compatible fixture, otherwise leave `Skip OS Morphing` at **No**.
    **Expected outcome:** the summary review step appears with those options.
14. On the summary, verify exactly one instance is listed, then click the **Finish** button (it is Finish, not Confirm).
    **Expected outcome:** the wizard submits the transfer.
15. Verify the new transfer has the correct endpoints and one instance, and its **Execution #1** starts. Browser network inspection can additionally confirm the successful creation request; a transient toast is not required evidence.
    **Expected outcome:** the UI opens the transfer's Executions tab and shows the running execution, not merely a saved transfer record.
16. Watch **Executions** until the transfer reaches `COMPLETED`, then open the correlated entry in **Deployments** and inspect its **Tasks** tab.
    **Expected outcome:** both execution and deployment reach `COMPLETED`, with no failed tasks. Completion alone does not prove guest usability; perform the observation checks below.
17. If any task or execution shows an `ERROR` status, stop.
    **Expected outcome:** you diagnose through the task details and the Logs navigation before touching anything; a failed execution is not blindly re-run.

Then, once your execution actually completes, repeat the observation checks from [Observe The Headless Result](#observe-the-headless-result) against the clouds.

## :material-book-open-page-variant-outline: Log Observation

The Logs navigation queries the appliance's own Loki-backed logging through the authenticated UI session.

- Natural producer activity appears over time: as components emit logs they show up in the viewer. An initially quiet component is not a failure; the run you just did should have produced volume across conductor, scheduler, worker, deployer, API, and web.
- The audited expectations from the logging qualification are that producers are non-empty over a window, with Memcached as the explicit non-empty-log exception. The logging infrastructure (Loki, gateway, Alloy, adaptor) is handled separately: it is self-excluded from natural correlation so the stack never queries itself, while its own health is audited for readiness and readability.
- Never search, filter, or display log output for secret values, tokens, or endpoint credentials; confirm facts from status and cloud state instead.

!!! warning "Debug mode is unsafe on this runtime"
    `coriolisDebug: true` remains a schema-allowed diagnostic mode, but it is unsafe here: on the immutable `2603.4` runtime it raises verbosity across all appliance components, has historically exposed sensitive request detail in logs, and cannot meet value-safe log acceptance. Keep `coriolisDebug: false`.

## :material-book-open-page-variant-outline: Migration Cleanup

Delete through the Web UI in this order; each step gates the next.

1. If any execution or deployment is still active, cancel it. Use the normal cancel first; force only if the UI workflow explicitly requires it after you diagnosed why the normal cancel did not settle, and never reach for Kubernetes force-deletion as a substitute.
   **Expected outcome:** the operation reaches a canceled terminal state before you delete anything.
2. Delete the deployment record, then handle the destination VM as a separate deliberate decision.
   **Expected outcome:** the deployment record is gone from the UI; record deletion says nothing about the VM, so you independently inspect the destination cloud and intentionally retain or remove the VM according to who owns the test result, never assuming the record removal handled it. When you do remove the guest, note that in this run a normal Nova deletion automatically removed the attached cloned boot volume but left the floating IP and the detached precreated Neutron port behind: verify those two by their exact IDs and delete them only if still present. Never delete the default security group.
3. On the transfer, open **Actions** and choose **Delete Disks**, then click **Yes** in the **Delete Transferred Disks?** confirmation dialog. The cleanup spawns a new execution visible under the transfer's **Executions**; wait for it to show `COMPLETED` before deleting the transfer itself.
   **Expected outcome:** destination disks created by the transfer are removed and the cleanup execution reaches `COMPLETED`.
4. Delete the transfer itself.
   **Expected outcome:** the transfer no longer appears in the UI.
5. Delete both endpoints. This is the full final cleanup and is the step deliberately skipped during the headless reset above.
   **Expected outcome:** the endpoint list is empty and, because each endpoint's connection payload lives in Barbican behind a `secret_ref`, the Barbican-backed endpoint credentials are removed with them.
6. Independently verify both clouds are back to the baseline: no temporary worker VMs, no leftover ports or floating IPs from workers, no Cinder backups or Swift objects from the export path, no snapshots or temporary images, and only the intentional source and destination VMs remain.
   **Expected outcome:** every artifact you can attribute to the run is gone or explicitly kept by decision.

An empty Swift export container can remain after disk cleanup. In this run the source container `coriolis` was absent before validation and empty afterward; final reset removed it. Delete an empty container only when the baseline and migration evidence establish that this run created it. Never remove a pre-existing/shared container or delete unknown objects to make it empty. Also remove any disposable fixture infrastructure you created, restoring only your recorded router interfaces and leaving pre-existing networks, keys, security groups, and floating IP bindings untouched.

## :material-book-open-page-variant-outline: Optional Runtime Removal

!!! warning "The namespace is shared"
    The `coriolis` namespace also hosts the Argo CD-managed operator. Deleting an appliance never justifies deleting the namespace, the operator, or the Argo CD Application.

<!-- Delete the appliance CR through the operator's supported path and wait for finalization. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis delete coriolisappliance coriolis-appliance-advanced --wait=true --timeout=10m
```

??? example "Expected result"

    ```text
    coriolisappliance.coriolis.cloudbase.it "coriolis-appliance-advanced" deleted
    ```

<!-- List the appliance Pods by label after deletion. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis get pods -l coriolis.cloudbase.it/appliance=coriolis-appliance-advanced
```

??? example "Expected result"

    ```text
    No resources found in coriolis namespace.
    ```

<!-- List the three retained data PVCs explicitly. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis get pvc coriolis-appliance-advanced-mariadb-data coriolis-appliance-advanced-rabbitmq-data coriolis-appliance-advanced-loki-data
```

??? example "Expected result"

    ```text
    NAME                                        STATUS   VOLUME     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
    coriolis-appliance-advanced-mariadb-data    Bound    <PV>       10Gi       RWO            local-path     <unset>                 <AGE>
    coriolis-appliance-advanced-rabbitmq-data   Bound    <PV>       1Gi        RWO            local-path     <unset>                 <AGE>
    coriolis-appliance-advanced-loki-data       Bound    <PV>       10Gi       RWO            local-path     <unset>                 <AGE>
    ```

The three data PVCs remain `Bound`: they are retained ownerless claims, exactly like the generated credential Secrets, which also survive. A same-name CR recreation therefore reuses the identical credential identities and the same persistent data; the owner-referenced workloads, configuration, and routes are what the delete removed. **Keep this retained state by default** -- it is the designed behavior, and same-name recreation is meant to reuse it. Never delete, force, edit finalizers, or reassign owners on any retained resource as improvised "cleanup". If and only if you deliberately want the namespace back to its pre-run, operator-only baseline, follow the optional [Full Fresh Reset](#full-fresh-reset) section below, which removes each retained resource by its exact recorded name under explicit safeguards.

## :material-book-open-page-variant-outline: Full Fresh Reset

!!! danger "Irreversible destruction of database, log, and credential state"
    This reset destroys the appliance databases, queues, logs, and generated credentials. Treat it as irreversible without verified external backups; a later same-name deployment gets fresh identities and empty databases. Complete [Migration Cleanup](#migration-cleanup) first: Kubernetes deletion does not clean resources in external OpenStack clouds, and endpoint/Barbican cleanup must be verified before erasing the backing database. Proceed only after the appliance CR and its owned workloads are gone. Delete only this run's recorded resources; preserve the shared namespace, Argo Application, operator, and both registry pull Secrets.

Retained state is kept by default (see [Optional Runtime Removal](#optional-runtime-removal)); this section is the separate, deliberate, destructive alternative that returns the namespace to the pre-run, operator-only baseline.

<!-- R1: Enumerate the retained Secrets and PVCs by appliance label, metadata only. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis get secret,pvc -l coriolis.cloudbase.it/appliance=coriolis-appliance-advanced -o custom-columns=KIND:.kind,NAME:.metadata.name
```

??? example "Expected result"

    ```text
    KIND                     NAME
    Secret                   coriolis-appliance-advanced-barbican-credentials
    Secret                   coriolis-appliance-advanced-coriolis-credentials
    Secret                   coriolis-appliance-advanced-infrastructure-credentials
    Secret                   coriolis-appliance-advanced-keystone-credential-keys
    Secret                   coriolis-appliance-advanced-keystone-database-credentials
    Secret                   coriolis-appliance-advanced-keystone-fernet-keys
    Secret                   coriolis-appliance-advanced-logging-credentials
    PersistentVolumeClaim    coriolis-appliance-advanced-loki-data
    PersistentVolumeClaim    coriolis-appliance-advanced-mariadb-data
    PersistentVolumeClaim    coriolis-appliance-advanced-rabbitmq-data
    ```

The gate is **exactly seven Secrets and three PVCs** with these names -- ten retained resources in total, and nothing else carrying the appliance label. Never print or decode Secret data here; name and kind only.

Before deleting the claims, note the `VOLUME` (PersistentVolume) name bound to each PVC in the `get pvc` output from the previous section. The `local-path` StorageClass uses `Delete` reclaim, so once a claim is gone its bound PV must be released and deleted automatically; after the next command, confirm each of the three previously recorded PV names returns `NotFound` (a targeted get of each recorded name). Never delete a PV directly.

<!-- R2: Delete the three appliance data PVCs by exact name and wait for completion. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis delete pvc coriolis-appliance-advanced-mariadb-data coriolis-appliance-advanced-rabbitmq-data coriolis-appliance-advanced-loki-data --wait=true --timeout=5m
```

??? example "Expected result"

    ```text
    persistentvolumeclaim "coriolis-appliance-advanced-mariadb-data" deleted
    persistentvolumeclaim "coriolis-appliance-advanced-rabbitmq-data" deleted
    persistentvolumeclaim "coriolis-appliance-advanced-loki-data" deleted
    ```

<!-- R3: Delete the seven generated credential Secrets by exact name. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis delete secret coriolis-appliance-advanced-barbican-credentials coriolis-appliance-advanced-coriolis-credentials coriolis-appliance-advanced-infrastructure-credentials coriolis-appliance-advanced-keystone-credential-keys coriolis-appliance-advanced-keystone-database-credentials coriolis-appliance-advanced-keystone-fernet-keys coriolis-appliance-advanced-logging-credentials
```

??? example "Expected result"

    ```text
    secret "coriolis-appliance-advanced-barbican-credentials" deleted
    secret "coriolis-appliance-advanced-coriolis-credentials" deleted
    secret "coriolis-appliance-advanced-infrastructure-credentials" deleted
    secret "coriolis-appliance-advanced-keystone-credential-keys" deleted
    secret "coriolis-appliance-advanced-keystone-database-credentials" deleted
    secret "coriolis-appliance-advanced-keystone-fernet-keys" deleted
    secret "coriolis-appliance-advanced-logging-credentials" deleted
    ```

<!-- R6: Confirm no Certificate or Ingress remains before deleting the TLS Secret. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis get certificate,ingress -o name
```

??? example "Expected result"

    ```text
    No output.
    ```

!!! warning "The TLS Secret is separate: verify before deleting it"
    The cert-manager TLS Secret `coriolis.app.cloudbase.wiki-tls` is **not** part of the appliance's retained set: the label query above cannot see it because cert-manager's ingress-shim created it ownerless and unlabeled, and it persists after CR deletion. It was created by this run's certificate issuance flow, not by the namespace baseline, and it is not shared with any other workload. Delete it explicitly only after confirming that no `Certificate` or `Ingress` resource referencing it remains (the namespace-wide sweep in R6 proves this) and that the Secret still matches the UID recorded for this run in your pre-removal metadata inventory. Deleting it forces a **fresh ACME issuance** on the next appliance deployment, which consumes Let's Encrypt rate limits; **keeping this one Secret is an accepted shortcut** so a future run reuses the certificate, but a kept TLS Secret means the namespace is not at the exact blank baseline.

<!-- R4: Delete the run-created TLS Secret after the verification above. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis delete secret coriolis.app.cloudbase.wiki-tls
```

??? example "Expected result"

    ```text
    secret "coriolis.app.cloudbase.wiki-tls" deleted
    ```

The remaining commands are verification gates for the wipe, plus the health proof that nothing shared was harmed.

<!-- R5: Confirm no appliance-labeled workload, config, or storage resources remain. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis get deploy,sts,pod,job,svc,cm,secret,pvc,ingress,sa,role,rolebinding -l coriolis.cloudbase.it/appliance=coriolis-appliance-advanced -o name
```

??? example "Expected result"

    ```text
    No output.
    ```

<!-- R7: Confirm the operator Deployment is untouched and still ready. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis get deployment coriolis-operator
```

??? example "Expected result"

    ```text
    NAME                READY   UP-TO-DATE   AVAILABLE   AGE
    coriolis-operator   1/1     1            1           <AGE>
    ```

<!-- R8: Confirm the Argo CD Application is still Synced and Healthy. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n argocd get application coriolis
```

??? example "Expected result"

    ```text
    NAME       SYNC STATUS   HEALTH STATUS
    coriolis   Synced        Healthy
    ```

With R5 to R8 green (and the three recorded PV names `NotFound`), the `coriolis` namespace is back to the pre-run, operator-only baseline: only the operator Deployment and Pod, the two pull Secrets, and the Argo CD-managed operator chart resources remain, and a fresh appliance apply will generate new credentials, new data volumes, and -- unless you kept it -- a new certificate.

## :material-book-open-page-variant-outline: Troubleshooting

| Symptom | Likely cause and response |
| --- | --- |
| `InvalidRuntimeConfiguration` on apply | The CR omits storage or resource bounds the runtime requires of MariaDB and RabbitMQ. Apply the tutorial asset unchanged rather than a hand-trimmed minimal sample. |
| Image `ImagePullBackOff` | A namespace pull Secret is missing or wrong; re-check `regcred` and `coriolis-appliance-registry` by name and type only, as in the prerequisites. |
| No TLS / browser warning on the host | DNS for `coriolis.app.cloudbase.wiki`, the `letsencrypt` ClusterIssuer, or the Certificate is at fault; check the Certificate and its events before touching the Ingress. |
| Reconcile reports a collision and stays fail-closed | A foreign resource already owns the expected name. The operator will not adopt it; resolve the conflict with the other owner. Never edit owners or finalizers yourself. |
| `Ready=True` but `LoggingReady=False` | The logging stack converges independently and later; wait with the LoggingReady condition, then inspect its reason if it times out. |
| Logs look stale or a bootstrap Job seems missing | Natural producer activity needs time, and a successful but old bootstrap Job may simply have no log inside the selected observation window. Recreate the CR under the same name only when you intentionally want to refresh startup evidence, since retained state is reused unchanged; it is not routine recovery. |
| Helper prints `ERROR category=post_ambiguous` | A POST's outcome could not be confirmed and the helper refused to guess. Inspect transfers and deployments for the unique notes in the UI before deciding; never blindly retry a write. |
| Any other helper `ERROR category=...` | Each category is fixed and terminal (config, preflight, authentication, network, execution/deployment failure or timeout). Stop, match the category to the phase, and diagnose before re-running. |
| Helper prints `ERROR category=preflight_failed` | No migration write occurred. Check endpoint IDs and the Keystone project scope first, then inspect existing transfers/deployments with the same notes. Resolve or clean the existing run before retrying; choose fresh notes only for a deliberately new migration, not to bypass duplicate protection. |
| Licence card shows an error on the dashboard | Expected in this development appliance: there is no licensing backend and no licensing Ingress, so `/licensing/appliances` falls through to the Web UI single-page application and returns HTML instead of a licensing API response. It does not affect login, endpoints, or migration work; see the note in [Web Login And Visual Inspection](#web-login-and-visual-inspection). |
| Someone suggests `coriolisDebug: true` | Decline on the immutable `2603.4` runtime; debug verbosity is unsafe for log hygiene here. |
| Deleted Pod or drifted resource is not being repaired | Expected: reconciliation is retry- and collision-scoped, not broad periodic drift self-healing. Stop and follow the documented controlled recovery path; CR recreation or operator resume has lifecycle effects and must be a deliberate decision, never hand-edited operator-owned objects and not a re-apply expecting a repair. |

## :material-book-open-page-variant-outline: Limits And Next Steps

!!! info "Scope of what you just did"
    This tutorial demonstrates a bounded development-capability path, not a production endorsement.

- Single-replica development appliance only; the `local-path` storage has no HA and no backups.
- Upgrades, production storage classes, multi-CR routing, and drift self-healing are not production-accepted.
- The bounded `0.5.54` UI migration evidence and the `0.5.57` logging evidence informed the expected outcomes above, and the current `0.5.59` walkthrough on this page has been followed end to end on that release, as recorded in the [Coriolis Operator Tutorial Validation Record](operator-tutorial-validation.md). That is bounded development evidence on one disposable fixture; no production claim is made.

Continue with:

- [Coriolis Operator](operator.md) for the operator's own validated scope.
- [Architecture](architecture.md) for component roles.
- [Migration Flow](migration-flow.md) and [OpenStack Context](openstack-provider.md) for the migration contract.
- [Terminology](terminology.md) for the vocabulary used throughout.
