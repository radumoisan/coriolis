# Deploy an Appliance

!!! abstract
    This lab uses the already-installed operator in the approved development environment to deploy a Coriolis appliance, validate `Ready` and `LoggingReady`, and log in through a browser. See [Coriolis Operator](operator.md) for the operator explanation and Helm configuration, and [Lab Environment](operator-lab-environment.md) for the concrete lab configuration.

## :material-book-open-page-variant-outline: Hands-On Prerequisites

!!! note ""
    Commands on this page assume `virt-infra-dev-buc-hq` is already the current `kubectl` context. Confirm it before starting.

Run each check and compare with the expected result before continuing. Any mismatch means stop and fix the prerequisite, not the tutorial.

Use Bash for the workstation commands; later cleanup steps use shell variables and an array. Have `kubectl`, Helm, `jq`, `curl`, Python 3, and standard shell utilities available. Keep command tracing disabled when handling credentials.

### :material-application-edit-outline: Argo CD Application

<!-- Verify the shared coriolis Application is Synced and Healthy. -->
```bash
kubectl -n argocd get application coriolis
```

??? example "Expected result"

    ```text
    NAME       SYNC STATUS   HEALTH STATUS
    coriolis   Synced        Healthy
    ```

### :material-application-edit-outline: Operator Deployment And CRD

<!-- Verify the operator Deployment is running in the coriolis namespace. -->
```bash
kubectl -n coriolis get deployment coriolis-operator
```

??? example "Expected result"

    ```text
    NAME                READY   UP-TO-DATE   AVAILABLE   AGE
    coriolis-operator   1/1     1            1           32d
    ```

The operator Deployment should show `1/1` ready, `1` up to date, and `1` available.

<!-- Inspect the operator Pod's readiness, status, and restart count. -->
```bash
kubectl -n coriolis get pods -l app.kubernetes.io/name=coriolis-operator
```

??? example "Expected result"

    ```text
    NAME                                 READY   STATUS    RESTARTS      AGE
    coriolis-operator-749677f8f5-44ghm   1/1     Running   1 (23h ago)   14d
    ```

The operator Pod should show `1/1` ready and `Running`.

<!-- Verify the CoriolisAppliance CRD is registered. -->
```bash
kubectl -n coriolis get crd coriolisappliances.coriolis.cloudbase.it
```

??? example "Expected result"

    ```text
    NAME                                       CREATED AT
    coriolisappliances.coriolis.cloudbase.it   2026-08-20T13:37:25Z
    ```

### :material-application-edit-outline: Namespace Pull Secrets

Both registry pull Secrets must exist in the `coriolis` namespace. Query name and type only; never decode or print Secret data.

<!-- Verify the two required pull Secrets exist. -->
```bash
kubectl -n coriolis get secret regcred coriolis-appliance-registry
```

??? example "Expected result"

    ```text
    NAME                          TYPE                             DATA   AGE
    regcred                       kubernetes.io/dockerconfigjson   1      34d
    coriolis-appliance-registry   kubernetes.io/dockerconfigjson   1      34d
    ```

`regcred` is what the operator chart references via `imagePullSecrets`;<br>`coriolis-appliance-registry` is the prerequisite the appliance itself expects to already exist for its runtime images.

### :material-application-edit-outline: Cluster Services

The operator does not install storage, ingress, or certificate infrastructure. Confirm the three cluster-scoped services the appliance values will reference.

<!-- Verify the dev local-path StorageClass exists. -->
```bash
kubectl -n coriolis get storageclass local-path
```

??? example "Expected result"

    ```text
    NAME                   PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
    local-path (default)   rancher.io/local-path   Delete          WaitForFirstConsumer   false                  121d
    ```

<!-- Verify the nginx IngressClass exists. -->
```bash
kubectl -n coriolis get ingressclass nginx
```

??? example "Expected result"

    ```text
    NAME    CONTROLLER             PARAMETERS   AGE
    nginx   k8s.io/ingress-nginx   <none>       121d
    ```

<!-- Verify the letsencrypt ClusterIssuer is Ready. -->
```bash
kubectl -n coriolis get clusterissuer letsencrypt
```

??? example "Expected result"

    ```text
    NAME          READY   AGE
    letsencrypt   True    121d
    ```

### :material-application-edit-outline: No Existing Appliance CR

The chosen appliance name must be free; the operator fails closed on collisions rather than adopting foreign resources.

<!-- Confirm no coriolis-appliance-advanced CR exists yet. -->
```bash
kubectl -n coriolis get coriolisappliance coriolis-appliance-advanced
```

??? example "Expected result"

    ```text
    Error from server (NotFound): coriolisappliances.coriolis.cloudbase.it "coriolis-appliance-advanced" not found
    ```

A `NotFound` here is the success condition. If the CR already exists, stop and reconcile with its owner instead of double-applying.

<!-- Check whether the TLS Secret already exists before this run. -->
```bash
kubectl -n coriolis get secret coriolis.app.cloudbase.wiki-tls
```

??? example "Expected result"

    ```text
    Error from server (NotFound): secrets "coriolis.app.cloudbase.wiki-tls" not found
    ```

A `NotFound` for this Secret means it is absent. If the Secret exists, it predates this run: record that fact and preserve it during cleanup.

## :material-book-open-page-variant-outline: Apply The Appliance

Create or use a local `coriolis-appliance.yaml` with the values shown below. The [chosen appliance values](operator-lab-environment.md#chosen-appliance-values) are defined in the lab environment.

??? quote "coriolis-appliance.yaml"

    ```yaml
    # CoriolisAppliance example, directly applicable to the current
    # approved dev namespace.
    #
    # Prerequisite (not part of this resource): the `coriolis-appliance-registry`
    # secret must already exist in the `coriolis` namespace before applying.
    #
    # Apply with an explicit namespace, for example:
    #   kubectl -n coriolis apply -f coriolis-appliance.yaml
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

<!-- Create the CoriolisAppliance from the local manifest. -->
```bash
kubectl -n coriolis apply -f coriolis-appliance.yaml
```

??? example "Expected result"

    ```text
    coriolisappliance.coriolis.cloudbase.it/coriolis-appliance-advanced created
    ```

## :material-book-open-page-variant-outline: Wait For Ready, Then LoggingReady

Reconciliation stages the core runtime first and the logging stack alongside it, but the conditions flip independently. Wait for each with its own bounded timeout rather than polling by eye. Convergence usually takes 5 to 15 minutes; each `15m` timeout gives the operator enough time to finish.

<!-- Wait for the core runtime Ready condition. -->
```bash
kubectl -n coriolis wait --for=condition=Ready --timeout=15m coriolisappliance/coriolis-appliance-advanced
```

??? example "Expected result"

    ```text
    coriolisappliance.coriolis.cloudbase.it/coriolis-appliance-advanced condition met
    ```

<!-- Wait for the independent LoggingReady condition. -->
```bash
kubectl -n coriolis wait --for=condition=LoggingReady --timeout=15m coriolisappliance/coriolis-appliance-advanced
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
kubectl -n coriolis get coriolisappliance coriolis-appliance-advanced -o json | jq -r '.status.conditions[] | "\(.type)=\(.status) reason=\(.reason)"'
```

??? example "Expected result"

    ```text
    Accepted=True reason=Accepted
    Progressing=False reason=RuntimeReady
    Reconciled=True reason=Reconciled
    Ready=True reason=RuntimeReady
    Degraded=False reason=NotDegraded
    Upgradeable=False reason=UpgradeNotSupported
    LoggingReady=True reason=LoggingReady
    ```

The gate is the status combination, not the reason text: `Accepted`, `Reconciled`, `Ready`, and `LoggingReady` must be `True`, `Progressing` and `Degraded` must be `False`, and `Upgradeable` is expected `False` for this release. The reasons above are the fixed converged-state values emitted by the `0.5.59` operator; while the appliance is still converging you may instead see `RuntimeStarting` or `LoggingStarting`, and a blocked reconcile carries the failure category in place of the ready reasons.

### :material-application-edit-outline: Pods

Every resource owned by the appliance carries the label `coriolis.cloudbase.it/appliance=coriolis-appliance-advanced`.

<!-- Show each component's ready/total containers, Pod phase, and restart count. -->
```bash
kubectl -n coriolis get pods -l coriolis.cloudbase.it/appliance=coriolis-appliance-advanced -o json | jq -r '.items | sort_by(.metadata.labels["coriolis.cloudbase.it/component"]) | .[] | [.metadata.labels["coriolis.cloudbase.it/component"], "\(((.status.containerStatuses // []) | map(select(.ready)) | length))/\(.spec.containers | length)", .status.phase, (((.status.containerStatuses // []) | map(.restartCount) | add) // 0)] | map(tostring) | join(" ")'
```

??? example "Expected result"

    ```text
    adaptor 1/1 Running 0
    alloy 1/1 Running 0
    barbican-api 1/1 Running 0
    barbican-worker 1/1 Running 0
    common-bootstrap-v3 0/1 Succeeded 0
    coriolis-api 1/1 Running 0
    coriolis-conductor 1/1 Running 0
    coriolis-deployer-manager 1/1 Running 0
    coriolis-minion-manager 1/1 Running 0
    coriolis-scheduler 1/1 Running 0
    coriolis-transfer-cron 1/1 Running 0
    coriolis-web 1/1 Running 0
    coriolis-worker 1/1 Running 0
    keystone 1/1 Running 0
    loki 2/2 Running 0
    mariadb 1/1 Running 0
    memcached 1/1 Running 0
    rabbitmq 1/1 Running 0
    ```

Component labels come from the operator source (the logging gateway runs as a sidecar container inside the `loki` Pod, which is why that row shows `2/2`). The gate is **18 appliance rows: 17 `Running` with all containers ready plus exactly one `Succeeded` bootstrap Job row, with zero restarts everywhere**. The namespace-wide Pod total is 19 because the already-running operator Pod joins it but carries operator labels, not the appliance label. Any nonzero restart count, a phase other than `Running`/`Succeeded`, or a missing component row blocks the tutorial; read the relevant condition and Pod logs before acting.

### :material-application-edit-outline: PVCs, Ingresses, And Certificate

<!-- List the appliance PersistentVolumeClaims; stable fields only, no volatile age. -->
```bash
kubectl -n coriolis get pvc -o custom-columns='NAME:.metadata.name,STATUS:.status.phase,VOLUME:.spec.volumeName,CAPACITY:.status.capacity.storage,STORAGECLASS:.spec.storageClassName'
```

??? example "Expected result"

    ```text
    NAME                                        STATUS   VOLUME                                     CAPACITY   STORAGECLASS
    coriolis-appliance-advanced-loki-data       Bound    pvc-6359c0f0-08c5-440a-9055-d2126e340196   10Gi       local-path
    coriolis-appliance-advanced-mariadb-data    Bound    pvc-032c16e5-a89e-40e7-892b-2a7c18523880   10Gi       local-path
    coriolis-appliance-advanced-rabbitmq-data   Bound    pvc-e35e92fd-d0b3-438b-ad43-16f76b86fd70   1Gi        local-path
    ```

Exactly **three Bound PVCs**, created as direct resources with the names above (MariaDB, RabbitMQ, and Loki data), each `RWO` on `local-path`. The `VOLUME` names are cluster-generated, so the three values shown are representative, not literal; record your actual bound PV names from this output now, because the [Full Fresh Reset](#full-fresh-reset) section verifies their automatic reclaim after claim deletion. These are retained ownerless claims, so same-name recreation reuses them instead of reprovisioning.

<!-- List the appliance Ingress resources; stable fields only, no volatile address or age (the HTTPS check below proves routing). -->
```bash
kubectl -n coriolis get ingress -o custom-columns='NAME:.metadata.name,CLASS:.spec.ingressClassName,HOST:.spec.rules[0].host'
```

??? example "Expected result"

    ```text
    NAME                                       CLASS   HOST
    coriolis-appliance-advanced-adaptor        nginx   coriolis.app.cloudbase.wiki
    coriolis-appliance-advanced-barbican-api   nginx   coriolis.app.cloudbase.wiki
    coriolis-appliance-advanced-coriolis-api   nginx   coriolis.app.cloudbase.wiki
    coriolis-appliance-advanced-coriolis-web   nginx   coriolis.app.cloudbase.wiki
    coriolis-appliance-advanced-keystone       nginx   coriolis.app.cloudbase.wiki
    ```

Five Ingress resources, all on the same class and host, one per routed service. Only the `coriolis-appliance-advanced-coriolis-web` Ingress carries the cert-manager ClusterIssuer annotation, so it is the resource that drives certificate issuance; the `coriolis-appliance-advanced-adaptor` Ingress serves the `/logs` and `/log-stream` routes.

<!-- Check the cert-manager Certificate readiness; stable fields only, no volatile age. -->
```bash
kubectl -n coriolis get certificate -o custom-columns='NAME:.metadata.name,READY:.status.conditions[?(@.type=="Ready")].status,SECRET:.spec.secretName'
```

??? example "Expected result"

    ```text
    NAME                              READY   SECRET
    coriolis.app.cloudbase.wiki-tls   True    coriolis.app.cloudbase.wiki-tls
    ```

The gate is one `Ready=True` Certificate whose `SECRET` is the TLS Secret for the configured host; the ingressed Secret name follows the ingress-shim `<host>-tls` convention. The issuer behind it is the `letsencrypt` ClusterIssuer annotated on the web Ingress (see above); the `get certificate` table itself does not show an `ISSUER` column.

<!-- Verify the Certificate's requested issuer and DNS names without reading private keys. -->
```bash
kubectl -n coriolis get certificate coriolis.app.cloudbase.wiki-tls -o jsonpath='{.spec.secretName}{" issuer="}{.spec.issuerRef.kind}{"/"}{.spec.issuerRef.name}{" dnsNames="}{.spec.dnsNames[*]}{"\n"}'
```

??? example "Expected result"

    ```text
    coriolis.app.cloudbase.wiki-tls issuer=ClusterIssuer/letsencrypt dnsNames=coriolis.app.cloudbase.wiki
    ```

These are the requested issuer and DNS subject alternative names (SANs), not proof of what the server presents. The next check verifies HTTPS with certificate and hostname validation enabled; do not add `--insecure` to make a TLS error disappear.

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
    The appliance's Keystone admin password is a real credential. The command below captures it into a shell variable without printing it. Use Bash with tracing (`set -x`) disabled, or the assignment will leak the value. Reveal it only in a private terminal, never while screen-sharing, in CI output, or against Production, and never store it in tracked files or notes.

<!-- Capture the admin password privately and fail if it cannot be read or is empty. -->
```bash
KEYSTONE_ADMIN_PASSWORD="$(set -o pipefail; kubectl -n coriolis get secret coriolis-appliance-advanced-infrastructure-credentials -o jsonpath='{.data.keystone_admin_password}' | base64 -d)" && test -n "$KEYSTONE_ADMIN_PASSWORD"
```

??? example "Expected result"

    ```text
    No output.
    ```

Success is exit status zero with no output; stop on any error or nonzero status. In that same private terminal, `printf '%s\n' "$KEYSTONE_ADMIN_PASSWORD"` reveals the value for browser login. Its output is deliberately not reproduced here. After logging in, use `unset KEYSTONE_ADMIN_PASSWORD` and clear the terminal scrollback. The operator generates the credential once and retains it across same-name appliance recreation.

## :material-book-open-page-variant-outline: Web Login And Visual Inspection

1. Open `https://coriolis.app.cloudbase.wiki/` in a browser.
   **Expected outcome:** the Coriolis web UI loads over HTTPS with a valid TLS certificate (no browser warning) and presents a Welcome screen with privacy and end-user license agreement (EULA) checkboxes and a **Submit** button.
2. Select both the privacy and EULA checkboxes, then click **Submit**.
   **Expected outcome:** the UI proceeds to `/login`, which offers only `Username` and `Password` fields and a **Login** button (there is no domain field on this form).
3. Log in with username `admin` and the password you captured into `KEYSTONE_ADMIN_PASSWORD` (reveal it in a private terminal as described above).
   **Expected outcome:** authentication succeeds and the Dashboard loads with a Signed in indicator, in an empty or near-empty state, because this fresh appliance has no endpoints or transfers yet.
4. Use the sidebar navigation labels **Transfers**, **Deployments**, and **Cloud Endpoints** to open each area without creating anything.
   **Expected outcome:** pages render without error banners; the transfer, deployment, and endpoint lists are empty. This confirms the UI can talk to the Coriolis API and Keystone through the ingress.
5. From the already-loaded and authenticated web UI, click the **Logs** navigation item (UI route `/logging`) rather than browsing directly to the host `/logs` path (those adaptor APIs require the UI's authenticated session).
   **Expected outcome:** the log viewer loads and queries the adaptor successfully, listing the appliance components (for example conductor, scheduler, API, web), confirming the Loki-backed logging path end to end.

!!! note "Licence Card In This Core Profile"
    The Dashboard's **Current Licence** card reports an error in this deployment: `/licensing/appliances` falls through to the Web UI and returns HTML, not a licensing API response. The core operator profile does not deploy a licensing backend or configure `LICENSING_SERVER_BASE_URL` for the conductor. Do not treat HTTP 200 on `/licensing` as a healthy licensing service or generalize this development configuration to a licensed production deployment.

!!! tip "Checkpoint"
    At this point you have a Ready and LoggingReady appliance with zero-restart Pods, three Bound PVCs, a trusted HTTPS endpoint, and a working browser login to the Dashboard with empty Transfers, Deployments, and Cloud Endpoints lists and a reachable Logs page. Continue with [Phase 1: Headless Migration](headless-migration.md), then [Phase 2: Web UI Migration](web-ui-migration.md), on this same appliance.

## :material-book-open-page-variant-outline: Troubleshooting

| Symptom | Likely cause and response |
| --- | --- |
| `InvalidRuntimeConfiguration` on apply | The CR omits storage or resource bounds the runtime requires of MariaDB and RabbitMQ. Apply the tutorial asset unchanged rather than a hand-trimmed minimal sample. |
| Image `ImagePullBackOff` | A namespace pull Secret is missing or wrong; re-check `regcred` and `coriolis-appliance-registry` by name and type only, as in the prerequisites. |
| No TLS / browser warning on the host | DNS for `coriolis.app.cloudbase.wiki`, the `letsencrypt` ClusterIssuer, or the Certificate is at fault; check the Certificate and its events before touching the Ingress. |
| Reconcile reports a collision and stays fail-closed | A foreign resource already owns the expected name. The operator will not adopt it; resolve the conflict with the other owner. Never edit owners or finalizers yourself. |
| `Ready=True` but `LoggingReady=False` | The logging stack converges independently and later; wait with the LoggingReady condition, then inspect its reason if it times out. |
| Logs look stale or a bootstrap Job seems missing | Natural producer activity needs time, and a successful but old bootstrap Job may simply have no log inside the selected observation window. Recreate the CR under the same name only when you intentionally want fresh startup logs, since retained state is reused unchanged; it is not routine recovery. |
| Licence card shows an error on the dashboard | Expected in this development appliance: there is no licensing backend and no licensing Ingress, so `/licensing/appliances` falls through to the Web UI single-page application and returns HTML instead of a licensing API response. It does not affect login, endpoints, or migration work; see the note in [Web Login And Visual Inspection](#web-login-and-visual-inspection). |
| Someone suggests `coriolisDebug: true` | Decline on the immutable `2603.4` runtime; debug verbosity is unsafe for log hygiene here. |
| Deleted Pod or drifted resource is not being repaired | Expected: reconciliation is retry- and collision-scoped, not broad periodic drift self-healing. Stop and follow the documented controlled recovery path; CR recreation or operator resume has lifecycle effects and must be a deliberate decision, never hand-edited operator-owned objects and not a re-apply expecting a repair. |

## :material-book-open-page-variant-outline: Next Steps

Continue with:

- [Phase 1: Headless Migration](headless-migration.md) on this appliance.
- [Phase 2: Web UI Migration](web-ui-migration.md) on the same appliance after Phase 1.
- [Lab Environment](operator-lab-environment.md) for the concrete configuration.
- [Coriolis Operator](operator.md) for operator behavior and configuration.
- [Architecture](architecture.md) for component roles.
- [Migration Flow](migration-flow.md) and [OpenStack Context](openstack-provider.md) for the migration contract.
- [Terminology](terminology.md) for the vocabulary used throughout.
- [Technical Debt](technical-debt.md) for current limitations and deferred work.

## :material-book-open-page-variant-outline: Optional Runtime Removal

Return here only when you are finished with the appliance and, if you performed migrations, have completed [migration cleanup](web-ui-migration.md#migration-cleanup) before removal.

!!! warning "The namespace is shared"
    The `coriolis` namespace also hosts the Argo CD-managed operator. Deleting an appliance never justifies deleting the namespace, the operator, or the Argo CD Application.

If you intend to perform the full fresh reset, capture the TLS Secret's UID before removal. Keep this Bash session open through cleanup; the variable is a metadata reference, not the certificate's private key.

<!-- Remember the TLS Secret identity for the optional destructive reset. -->
```bash
TUTORIAL_TLS_UID="$(kubectl -n coriolis get secret coriolis.app.cloudbase.wiki-tls -o jsonpath='{.metadata.uid}')" && test -n "$TUTORIAL_TLS_UID"
```

??? example "Expected result"

    ```text
    No output.
    ```

Proceed only on exit status zero. Recording the UID does not establish ownership: the pre-run check must also have shown this Secret absent before you can delete it during reset.

<!-- Delete the appliance CR through the operator's supported path and wait for finalization. -->
```bash
kubectl -n coriolis delete coriolisappliance coriolis-appliance-advanced --wait=true --timeout=10m
```

??? example "Expected result"

    ```text
    coriolisappliance.coriolis.cloudbase.it "coriolis-appliance-advanced" deleted
    ```

<!-- List the appliance Pods by label after deletion. -->
```bash
kubectl -n coriolis get pods -l coriolis.cloudbase.it/appliance=coriolis-appliance-advanced
```

??? example "Expected result"

    ```text
    No resources found in coriolis namespace.
    ```

<!-- List the three retained data PVCs explicitly; stable fields only, no volatile age. -->
```bash
kubectl -n coriolis get pvc coriolis-appliance-advanced-mariadb-data coriolis-appliance-advanced-rabbitmq-data coriolis-appliance-advanced-loki-data -o custom-columns='NAME:.metadata.name,STATUS:.status.phase,VOLUME:.spec.volumeName,CAPACITY:.status.capacity.storage,STORAGECLASS:.spec.storageClassName'
```

??? example "Expected result"

    ```text
    NAME                                        STATUS   VOLUME                                     CAPACITY   STORAGECLASS
    coriolis-appliance-advanced-mariadb-data    Bound    pvc-032c16e5-a89e-40e7-892b-2a7c18523880   10Gi       local-path
    coriolis-appliance-advanced-rabbitmq-data   Bound    pvc-e35e92fd-d0b3-438b-ad43-16f76b86fd70   1Gi        local-path
    coriolis-appliance-advanced-loki-data       Bound    pvc-6359c0f0-08c5-440a-9055-d2126e340196   10Gi       local-path
    ```

The three data PVCs remain `Bound` with the same `VOLUME` bindings recorded earlier: they are retained ownerless claims, exactly like the generated credential Secrets, which also survive. A same-name CR recreation therefore reuses the identical credential identities and the same persistent data; the owner-referenced workloads, configuration, and routes are what the delete removed. **Keep this retained state by default** -- it is the designed behavior, and same-name recreation is meant to reuse it. Never delete, force, edit finalizers, or reassign owners on any retained resource as improvised "cleanup". If and only if you deliberately want the namespace back to its pre-run, operator-only baseline, follow the optional [Full Fresh Reset](#full-fresh-reset) section below, which removes each retained resource by its exact recorded name under explicit safeguards.

## :material-book-open-page-variant-outline: Full Fresh Reset

!!! danger "Irreversible destruction of database, log, and credential state"
    This reset destroys the appliance databases, queues, logs, and generated credentials. Treat it as irreversible without verified external backups; a later same-name deployment gets fresh identities and empty databases. Complete [Migration Cleanup](web-ui-migration.md#migration-cleanup) first if you performed migrations. Skip external migration cleanup only if no migrations were ever performed: Kubernetes deletion does not clean resources in external OpenStack clouds, and endpoint/Barbican cleanup must be verified before erasing the backing database. Proceed only after the appliance CR and its owned workloads are gone. Delete only this run's recorded resources; preserve the shared namespace, Argo Application, operator, and both registry pull Secrets.

Retained state is kept by default (see [Optional Runtime Removal](#optional-runtime-removal)); this section is the separate, deliberate, destructive alternative that returns the namespace to the pre-run, operator-only baseline.

<!-- Enumerate the retained Secrets and PVCs by appliance label, metadata only. -->
```bash
kubectl -n coriolis get secret,pvc -l coriolis.cloudbase.it/appliance=coriolis-appliance-advanced -o json | jq -r '.items | sort_by(.kind, .metadata.name) | .[] | "\(.kind) \(.metadata.name)"'
```

??? example "Expected result"

    ```text
    PersistentVolumeClaim coriolis-appliance-advanced-loki-data
    PersistentVolumeClaim coriolis-appliance-advanced-mariadb-data
    PersistentVolumeClaim coriolis-appliance-advanced-rabbitmq-data
    Secret coriolis-appliance-advanced-barbican-credentials
    Secret coriolis-appliance-advanced-coriolis-credentials
    Secret coriolis-appliance-advanced-infrastructure-credentials
    Secret coriolis-appliance-advanced-keystone-credential-keys
    Secret coriolis-appliance-advanced-keystone-database-credentials
    Secret coriolis-appliance-advanced-keystone-fernet-keys
    Secret coriolis-appliance-advanced-logging-credentials
    ```

The gate is **exactly seven Secrets and three PVCs** with these names -- ten retained resources in total, and nothing else carrying the appliance label. Never print or decode Secret data here; name and kind only.

The `local-path` StorageClass uses `Delete` reclaim: after claim deletion, each bound PV must be deleted automatically. Capture the three actual bindings in a Bash array before deleting the claims; do not reuse the example UUIDs. Keep this session open until the PV check below. Never delete a PV directly.

<!-- Capture exactly three bound PV names from the tutorial claims. -->
```bash
TUTORIAL_PVS=($(kubectl -n coriolis get pvc coriolis-appliance-advanced-mariadb-data coriolis-appliance-advanced-rabbitmq-data coriolis-appliance-advanced-loki-data -o jsonpath='{.items[*].spec.volumeName}')) && test "${#TUTORIAL_PVS[@]}" -eq 3
```

??? example "Expected result"

    ```text
    No output.
    ```

Exit status zero confirms three names were captured. Stop if the read fails or a claim is unbound; do not continue with an empty or incomplete array.

<!-- Delete the three appliance data PVCs by exact name and wait for completion. -->
```bash
kubectl -n coriolis delete pvc coriolis-appliance-advanced-mariadb-data coriolis-appliance-advanced-rabbitmq-data coriolis-appliance-advanced-loki-data --wait=true --timeout=5m
```

??? example "Expected result"

    ```text
    persistentvolumeclaim "coriolis-appliance-advanced-mariadb-data" deleted
    persistentvolumeclaim "coriolis-appliance-advanced-rabbitmq-data" deleted
    persistentvolumeclaim "coriolis-appliance-advanced-loki-data" deleted
    ```

<!-- Check only the captured PVs; ignore NotFound responses, not other errors. -->
```bash
test "${#TUTORIAL_PVS[@]}" -eq 3 && kubectl -n coriolis get pv "${TUTORIAL_PVS[@]}" --ignore-not-found -o name
```

??? example "Expected result"

    ```text
    No output.
    ```

Exit status zero with no names means all three PVs are absent. If a name remains, wait for automatic reclaim and repeat this check. Investigate a persistent resource or API error; do not force deletion to obtain an empty result.

<!-- Delete the seven generated credential Secrets by exact name. -->
```bash
kubectl -n coriolis delete secret coriolis-appliance-advanced-barbican-credentials coriolis-appliance-advanced-coriolis-credentials coriolis-appliance-advanced-infrastructure-credentials coriolis-appliance-advanced-keystone-credential-keys coriolis-appliance-advanced-keystone-database-credentials coriolis-appliance-advanced-keystone-fernet-keys coriolis-appliance-advanced-logging-credentials
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

<!-- Confirm no Certificate or Ingress remains before deleting the TLS Secret. -->
```bash
kubectl -n coriolis get certificate,ingress -o name
```

??? example "Expected result"

    ```text
    No output.
    ```

!!! warning "The TLS Secret is separate: verify before deleting it"
    The cert-manager TLS Secret `coriolis.app.cloudbase.wiki-tls` is ownerless and unlabeled in this deployment, so the appliance-label query cannot find it and CR deletion leaves it behind. Delete it only if your baseline proves this run created it, no other workload uses it, no referencing Certificate or Ingress remains, and its UID matches your pre-removal inventory. Do not assume ownership from the name alone. Deleting it forces fresh ACME issuance on the next deployment and consumes Let's Encrypt rate limits. Keeping this Secret lets a later run reuse the certificate, but is not an exact return to the blank baseline.

<!-- Verify that the TLS Secret still has the UID captured before runtime removal. -->
```bash
test -n "${TUTORIAL_TLS_UID:-}" && test "$TUTORIAL_TLS_UID" = "$(kubectl -n coriolis get secret coriolis.app.cloudbase.wiki-tls -o jsonpath='{.metadata.uid}')"
```

??? example "Expected result"

    ```text
    No output.
    ```

Only exit status zero is success. A lost variable, changed UID, missing Secret, or API error blocks the next command. If you kept the pre-existing TLS Secret, skip both this comparison and its deletion.

<!-- Delete the run-created TLS Secret after the verification above. -->
```bash
kubectl -n coriolis delete secret coriolis.app.cloudbase.wiki-tls
```

??? example "Expected result"

    ```text
    secret "coriolis.app.cloudbase.wiki-tls" deleted
    ```

The remaining commands are verification gates for the wipe, plus the health proof that nothing shared was harmed.

<!-- Confirm no appliance-labeled workload, config, or storage resources remain. -->
```bash
kubectl -n coriolis get deploy,sts,pod,job,svc,cm,secret,pvc,ingress,sa,role,rolebinding -l coriolis.cloudbase.it/appliance=coriolis-appliance-advanced -o name
```

??? example "Expected result"

    ```text
    No output.
    ```

<!-- Confirm the operator Deployment is untouched and still ready. -->
```bash
kubectl -n coriolis get deployment coriolis-operator
```

??? example "Expected result"

    ```text
    NAME                READY   UP-TO-DATE   AVAILABLE   AGE
    coriolis-operator   1/1     1            1           32d
    ```

<!-- Confirm the Argo CD Application is still Synced and Healthy. -->
```bash
kubectl -n argocd get application coriolis
```

??? example "Expected result"

    ```text
    NAME       SYNC STATUS   HEALTH STATUS
    coriolis   Synced        Healthy
    ```

With the final resource, operator Deployment, and Argo CD Application checks green and the captured-PV check returning no names, the `coriolis` namespace is back to the pre-run, operator-only baseline: only the operator Deployment and Pod, the two pull Secrets, and the Argo CD-managed operator chart resources remain, and a fresh appliance apply will generate new credentials, new data volumes, and -- unless you kept it -- a new certificate.
