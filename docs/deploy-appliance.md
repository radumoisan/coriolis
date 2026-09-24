# Deploy an Appliance

!!! abstract
    This lab uses the already-installed operator in the approved development environment to deploy a Coriolis appliance, validate `Ready` and `LoggingReady`, and log in through a browser. See [Coriolis Operator](architecture.md#coriolis-operator) for the operator explanation and Helm configuration, and [Lab Environment](operator-lab-environment.md) for the concrete lab configuration.

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

Create or use a local `coriolis-appliance.yaml` with the values shown below.

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

Use the `STATUS` values to decide whether the appliance is ready:

- `Accepted`, `Reconciled`, `Ready`, and `LoggingReady` should be `True`.
- `Progressing` and `Degraded` should be `False`.
- `Upgradeable` is expected to be `False` because upgrades are not supported yet.

The `REASON` values provide additional context and may change while the appliance starts. For example, `RuntimeStarting` and `LoggingStarting` mean that the corresponding services are still becoming ready. If reconciliation fails, the reason identifies the type of failure.

### :material-application-edit-outline: Pods

Every resource owned by the appliance carries the label `coriolis.cloudbase.it/appliance=coriolis-appliance-advanced`.

<!-- List the appliance Pods and their current status. -->
```bash
kubectl -n coriolis get pods -l coriolis.cloudbase.it/appliance=coriolis-appliance-advanced
```

??? example "Expected result"

    ```text
    NAME                                                              READY   STATUS      RESTARTS   AGE
    coriolis-appliance-advanced-adaptor-566d96f6bd-qnqdx              1/1     Running     0          30m
    coriolis-appliance-advanced-alloy-8475d6d496-86dfc                1/1     Running     0          33m
    coriolis-appliance-advanced-barbican-api-59dd6fb6-dj5x9           1/1     Running     0          33m
    coriolis-appliance-advanced-barbican-worker-584b8d5fb9-p8ltn      1/1     Running     0          33m
    coriolis-appliance-advanced-common-bootstrap-v3-lrmth             0/1     Completed   0          33m
    coriolis-appliance-advanced-coriolis-api-7d9446f8c4-mnv8z         1/1     Running     0          30m
    coriolis-appliance-advanced-coriolis-conductor-654776d579-rqs7z   1/1     Running     0          30m
    coriolis-appliance-advanced-coriolis-deployer-manager-748dkt66n   1/1     Running     0          30m
    coriolis-appliance-advanced-coriolis-minion-manager-79d89bxklkl   1/1     Running     0          30m
    coriolis-appliance-advanced-coriolis-scheduler-869cd9686d-ztbx6   1/1     Running     0          30m
    coriolis-appliance-advanced-coriolis-transfer-cron-8477564ppvwj   1/1     Running     0          30m
    coriolis-appliance-advanced-coriolis-web-fdf47cbc-qm5km           1/1     Running     0          30m
    coriolis-appliance-advanced-coriolis-worker-6889fcddb9-9qzlh      1/1     Running     0          30m
    coriolis-appliance-advanced-keystone-d7679cbd6-77m82              1/1     Running     0          33m
    coriolis-appliance-advanced-loki-0                                2/2     Running     0          34m
    coriolis-appliance-advanced-mariadb-0                             1/1     Running     0          33m
    coriolis-appliance-advanced-memcached-67dc8c9fb7-x574c            1/1     Running     0          33m
    coriolis-appliance-advanced-rabbitmq-0                            1/1     Running     0          33m
    ```

Check the following:

- The output contains 18 appliance Pods.
- Seventeen Pods are `Running` with all containers ready.
- The `loki` Pod shows `2/2` because it also contains the logging gateway sidecar.
- The one-time `common-bootstrap-v3` Pod shows `0/1 Completed`.
- Every Pod shows `0` restarts.

Pod suffixes and ages will differ. Stop if a Pod is missing, a running Pod is not fully ready, the bootstrap Pod did not complete, or any restart count is nonzero.

### :material-application-edit-outline: PVCs, Ingresses, And Certificate

<!-- List the appliance PersistentVolumeClaims. -->
```bash
kubectl -n coriolis get pvc
```

??? example "Expected result"

    ```text
    NAME                                        STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
    coriolis-appliance-advanced-loki-data       Bound    pvc-85f99a07-4ff8-465d-9476-eace63ba52a1   10Gi       RWO            local-path     <unset>                 43m
    coriolis-appliance-advanced-mariadb-data    Bound    pvc-781a0c98-61ba-4bf5-9a18-899234c872fa   10Gi       RWO            local-path     <unset>                 42m
    coriolis-appliance-advanced-rabbitmq-data   Bound    pvc-4779d7db-612a-46e8-839d-10cfe62a6cb6   1Gi        RWO            local-path     <unset>                 42m
    ```

Check the following:

- MariaDB, RabbitMQ, and Loki each have one PVC in `Bound` status.
- All three PVCs use `RWO` access and the `local-path` StorageClass.
- MariaDB and Loki have `10Gi`; RabbitMQ has `1Gi`.
- The `VOLUME` identifiers and ages are cluster-generated and will differ.

The operator retains these PVCs when the appliance CR is removed. Recreating the appliance with the same name reuses them. The [Full Fresh Reset](remove-appliance.md#full-fresh-reset) section removes them and verifies that their volumes are reclaimed.

<!-- List the appliance Ingress resources. -->
```bash
kubectl -n coriolis get ingress
```

??? example "Expected result"

    ```text
    NAME                                       CLASS   HOSTS                         ADDRESS        PORTS     AGE
    coriolis-appliance-advanced-adaptor        nginx   coriolis.app.cloudbase.wiki   10.254.11.50   80, 443   41m
    coriolis-appliance-advanced-barbican-api   nginx   coriolis.app.cloudbase.wiki   10.254.11.50   80, 443   41m
    coriolis-appliance-advanced-coriolis-api   nginx   coriolis.app.cloudbase.wiki   10.254.11.50   80, 443   41m
    coriolis-appliance-advanced-coriolis-web   nginx   coriolis.app.cloudbase.wiki   10.254.11.50   80, 443   41m
    coriolis-appliance-advanced-keystone       nginx   coriolis.app.cloudbase.wiki   10.254.11.50   80, 443   41m
    ```

Check the following:

- Five Ingress resources expose the routed appliance services.
- All use the `nginx` class and `coriolis.app.cloudbase.wiki` host.
- All show the same ingress address and ports `80, 443`.
- The `coriolis-web` Ingress requests the certificate from cert-manager.
- The `adaptor` Ingress serves the `/logs` and `/log-stream` routes.

The ingress address and ages depend on the cluster and will differ.

<!-- Check the cert-manager Certificate readiness. -->
```bash
kubectl -n coriolis get certificate
```

??? example "Expected result"

    ```text
    NAME                              READY   SECRET                            AGE
    coriolis.app.cloudbase.wiki-tls   True    coriolis.app.cloudbase.wiki-tls   42m
    ```

Check the following:

- The Certificate is `Ready=True`.
- Its Secret is `coriolis.app.cloudbase.wiki-tls`.
- The age depends on when the Certificate was created and will differ.

### :material-application-edit-outline: HTTPS And Routes

<!-- Confirm the public endpoint answers with HTTP 200 over TLS. -->
```bash
curl -I https://coriolis.app.cloudbase.wiki/
```

??? example "Expected result"

    ```text
    HTTP/2 200
    date: Thu, 24 Sep 2026 10:57:30 GMT
    content-type: text/html; charset=utf-8
    content-length: 653
    x-powered-by: Express
    accept-ranges: bytes
    cache-control: public, max-age=0
    last-modified: Fri, 10 Jul 2026 12:25:38 GMT
    etag: W/"28d-19f4bfd95d0"
    strict-transport-security: max-age=31536000; includeSubDomains
    ```

`HTTP/2 200` confirms that the HTTPS endpoint and web frontend are responding. Header values such as dates and content length may differ. The appliance exposes these routes on that host:

| Route | Serves |
| --- | --- |
| `/` | Coriolis web UI |
| `/identity` | Keystone authentication API |
| `/coriolis` | Coriolis API |
| `/barbican` | Barbican secrets API |
| `/logs`, `/log-stream` | Authenticated log list, download, and streaming APIs served by the logging adaptor |

!!! warning
    The commands below print the encoded and decoded Keystone admin password. Both are sensitive. Run them only in a private terminal, never while screen-sharing or in CI output, and do not store their output in tracked files or notes. The examples use dummy values.

<!-- Read the encoded Keystone admin password from the generated Secret. -->
```bash
kubectl get secret coriolis-appliance-advanced-infrastructure-credentials \
    -n coriolis \
    -o jsonpath='{.data.keystone_admin_password}'
```

??? example "Expected result"

    ```text
    a2sxUWNDcWxUY3diZWRfa2VsNHkzbW1wbkoyWm1NZFNKdjMwVFFPNGwwZw==
    ```

Copy the encoded value and use it in the next command. The value shown here decodes to the dummy password used in the expected result.

<!-- Decode the value returned by the previous command. -->
```bash
echo 'a2sxUWNDcWxUY3diZWRfa2VsNHkzbW1wbkoyWm1NZFNKdjMwVFFPNGwwZw==' | base64 -d; echo
```

??? example "Expected result"

    ```text
    kk1QcCqlTcwbed_kel4y3mmpnJ2ZmMdSJv30TQO4l0g
    ```

Use the decoded value to log in, then clear the terminal scrollback. The operator generates this credential once and retains it across same-name appliance recreation.

## :material-book-open-page-variant-outline: Web Login And Visual Inspection

1. Open `https://coriolis.app.cloudbase.wiki/`. Confirm that the page loads over HTTPS without a certificate warning.
2. Accept the privacy policy and EULA, then click **Submit**. The login page should appear.
3. Log in with username `admin` and the password displayed above. The Dashboard should load successfully.
4. Open **Transfers**, **Deployments**, and **Cloud Endpoints** from the sidebar. Each page should load without errors; the lists should be empty for a fresh appliance.
5. Open **Logs** from the sidebar rather than browsing directly to `/logs`. Confirm that the log viewer lists the appliance components.

!!! note "Licence Card In This Core Profile"
    The Dashboard's **Current Licence** card reports an error in this deployment: `/licensing/appliances` falls through to the Web UI and returns HTML, not a licensing API response. The core operator profile does not deploy a licensing backend or configure `LICENSING_SERVER_BASE_URL` for the conductor. Do not treat HTTP 200 on `/licensing` as a healthy licensing service or generalize this development configuration to a licensed production deployment.

!!! tip "Checkpoint"
    At this point you have a Ready and LoggingReady appliance with zero-restart Pods, three Bound PVCs, a trusted HTTPS endpoint, and a working browser login to the Dashboard with empty Transfers, Deployments, and Cloud Endpoints lists and a reachable Logs page. Continue with [Phase 1: Headless Migration](headless-migration.md), then [Phase 2: Web UI Migration](web-ui-migration.md), on this same appliance.

## :material-book-open-page-variant-outline: Next Steps

Continue with:

- [Phase 1: Headless Migration](headless-migration.md) on this appliance.
- [Phase 2: Web UI Migration](web-ui-migration.md) on the same appliance after Phase 1.
- [Remove Appliance](remove-appliance.md) when you are finished with both migrations.
