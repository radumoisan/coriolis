# Remove Appliance

!!! abstract
    Remove the lab appliance after migration cleanup. Choose retained-state removal by default, or use a full fresh reset to destroy all run-created state.

!!! note ""
    These commands assume `virt-infra-dev-buc-hq` is already the current `kubectl` context.

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
