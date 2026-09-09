# Coriolis Operator Tutorial Validation Record

!!! abstract
    This record tracks the [Advanced Tutorial](operator-advanced-tutorial.md): its 26 original command checkpoints (C1-C26), UI/cloud checks and workspace setup (S), and eight fresh-reset commands (R). The current tutorial contains 35 Bash command blocks.

!!! warning "Bounded evidence, not production readiness"
    Marking a row `validated` proves only that one tutorial checkpoint was executed successfully against the recorded operator target in the approved development cluster during the recorded run. This document is a bounded validation aid for the tutorial; it is not a release certification, a production-readiness statement, or evidence for anything outside the tutorial's declared scope.

## :material-book-open-page-variant-outline: Run Metadata

| Field | Value |
| --- | --- |
| Run ID | `adv-tut-2026-09-09-01` |
| Recorded date | 2026-09-09 |
| Run start (UTC) | 2026-09-09T18:38:53Z |
| Final observation (UTC) | 2026-09-09T22:55:30Z |
| Tutorial under validation | [Coriolis Operator Advanced Tutorial](operator-advanced-tutorial.md) |
| Operator target | `0.5.59` |
| Appliance runtime | `2603.4` |
| Appliance under test | `coriolis-appliance-advanced` in namespace `coriolis` |
| Cluster context | `virt-infra-dev-buc-hq` (development only) |
| Helm install reference method | Offline `helm template` render of the reference chart with the example values; **not** a live installation (Argo CD owns the live operator). |
| Private config workspace | `.openstack/tutorial-validation/` was repository-ignored and removed after verification; original cloud configuration files were preserved. |

### :material-application-edit-outline: Status Legend And Baseline Note

Statuses: `pending` (default, not yet executed in this run), `validated` (succeeded with recorded evidence), `render-validated` (reference render confirmed only; no live install), `blocked` (prerequisite unmet), `failed` (mismatch recorded), `n/a` (deliberately out of scope for this run).

!!! note "Prior observations are not new validations"
    A clean cluster baseline was observed during earlier read-only scouting (for example the prerequisites already passing). Those observations are **not** marked `validated` here. A row may only become `validated` when its command or step is actually executed and its expected result confirmed under this Run ID.

## :material-book-open-page-variant-outline: Phase 1 -- Operator Install Reference

| # | Checkpoint | Status | Evidence / notes |
| --- | --- | --- | --- |
| C1 | Reference Helm render: `helm template` of the operator chart (concrete OCI version) with `coriolis-operator-values.example.yaml`; render only, no live install | render-validated | Chart `coriolis-operator:0.5.59` (digest `sha256:0fda51d336e90af0eceba3c8daba4372cb9fb60caab4fcee131fbf19bae94f12`) fetched from OCI and rendered cleanly with the example values: SA, Role, RoleBinding, Deployment all named `coriolis-operator`, image `operator:0.5.59` with `regcred`. Explicitly NOT live-install validated; Argo CD owns the live operator. |

## :material-book-open-page-variant-outline: Phase 2 -- Hands-On Prerequisites

| # | Checkpoint | Status | Evidence / notes |
| --- | --- | --- | --- |
| C2 | `pwd` is the repository root | validated | `pwd` returned `/home/radu/Dev/cb-coriolis`, matching the tutorial's expected result exactly. |
| C3 | Argo CD `coriolis` Application is `Synced` / `Healthy` | validated | `kubectl -n argocd get application coriolis` returned `coriolis Synced Healthy`, matching the expected result. |
| C4 | Operator Deployment `coriolis-operator` is `1/1` with zero restarts | validated | Deployment returned `1/1` ready (AGE 18d). Restart counts are not provable from Deployment columns, so an additional final check observed the operator Pod `READY=True`, `RESTARTS=0`. |
| C5 | CRD `coriolisappliances.coriolis.cloudbase.it` is registered | validated | CRD present with `CREATED AT 2026-08-20T13:37:25Z`, matching the expected result. |
| C6 | Pull Secrets `regcred` and `coriolis-appliance-registry` exist (name and type only; never decode data) | validated | Both Secrets returned with type `kubernetes.io/dockerconfigjson`; no Secret data decoded or printed. |
| C7 | `local-path` StorageClass exists | validated | `local-path (default)` present, provisioner `rancher.io/local-path`, reclaim `Delete`, `WaitForFirstConsumer`. Tutorial expected result corrected for the `(default)` marker and `AGE` column. |
| C8 | `nginx` IngressClass exists | validated | IngressClass `nginx` returned with controller `k8s.io/ingress-nginx`, matching the expected result. |
| C9 | `letsencrypt` ClusterIssuer is `Ready=True` | validated | JSONPath query returned `letsencrypt ready=True`, matching the expected result exactly. |
| C10 | No existing `coriolis-appliance-advanced` CR (`NotFound` is the success condition) | validated | Returned `Error from server (NotFound)` for the CR, matching the tutorial's success condition exactly. |

## :material-book-open-page-variant-outline: Phase 3 -- Apply And Converge

| # | Checkpoint | Status | Evidence / notes |
| --- | --- | --- | --- |
| C11 | `kubectl apply` of `docs/assets/manifests/coriolis-appliance-advanced.yaml` reports `created` | validated | Metadata-only pre-apply baseline captured in the private ledger; `apply` returned `coriolis-appliance-advanced created`; created CR UID recorded in the private cleanup ledger for exact baseline cleanup. |
| C12 | `wait --for=condition=Ready` succeeds within the 15m bound | validated | `condition met` returned with exit code 0 after ~153s, well within the 15m bound. |
| C13 | `wait --for=condition=LoggingReady` succeeds within the 15m bound | validated | `condition met` returned with exit code 0 after ~1s, well within the 15m bound. |

## :material-book-open-page-variant-outline: Phase 4 -- Runtime Inspection

| # | Checkpoint | Status | Evidence / notes |
| --- | --- | --- | --- |
| C14 | Conditions gate: `Accepted`/`Reconciled`/`Ready`/`LoggingReady` `True`, `Progressing`/`Degraded` `False`, `Upgradeable` `False` | validated | Tutorial jq command returned all 7 conditions matching the gate; `Upgradeable=False reason=UpgradeNotSupported` matches the tutorial example. |
| C15 | Label filter returns exactly 18 appliance Pods: 17 `Running` + 1 `Completed` bootstrap, zero restarts | validated | Exactly 18 appliance Pods: 17 `Running` plus one `common-bootstrap-v3` `Completed`; machine check of all container restart counts summed to 0. Tutorial expected names corrected to the actual `coriolis-`-prefixed forms. |
| C16 | Exactly three appliance PVCs `Bound` (MariaDB 10Gi, RabbitMQ 1Gi, Loki 10Gi, all `local-path`) | validated | Exactly three appliance PVCs all `Bound` on `local-path`: mariadb-data 10Gi, rabbitmq-data 1Gi, loki-data 10Gi. Tutorial fence corrected for actual columns (`ACCESS MODES`, `VOLUMEATTRIBUTESCLASS`) and row order. |
| C17 | Five appliance Ingresses listed, all on the configured host | validated | Exactly five appliance Ingresses (adaptor, barbican-api, coriolis-api, coriolis-web, keystone), class `nginx`, all on `coriolis.app.cloudbase.wiki`, ports `80, 443`; only coriolis-web carries the `letsencrypt` annotation. |
| C18 | One `Ready=True` Certificate named per the `<host>-tls` convention | validated | Exactly one Certificate `coriolis.app.cloudbase.wiki-tls` `READY=True`, issuer ClusterIssuer `letsencrypt`. Tutorial example corrected (actual table has no `ISSUER` column). |
| C19 | `curl` of the public HTTPS endpoint returns `200` with a valid certificate | validated | Tutorial `curl` returned `200` and exit 0; `openssl s_client` confirmed leaf CN/SAN `coriolis.app.cloudbase.wiki`, issuer Let's Encrypt, validity Sep 9 17:43:29 2026 GMT - Dec 8 17:43:28 2026 GMT. |
| C20 | Keystone admin password readable from the credentials Secret (dev session only; value never recorded here) | validated | Exact Secret key retrieved and decoded privately, then filled into the browser through an encrypted handoff; the plaintext-printing variant was not used in recorded tool output. |

## :material-book-open-page-variant-outline: Phase 5 -- Web Login And Visual Inspection

| # | Checkpoint | Status | Evidence / notes |
| --- | --- | --- | --- |
| S1 | UI loads over HTTPS with no browser warning; end-user agreement prompt on first visit | validated | Browser opened the HTTPS host with no warning: Welcome to Coriolis, privacy/EULA agreements, disabled Submit before consent. |
| S2 | Accepting agreements reveals the login form | validated | Checked both agreements and clicked Submit; reached /login with Username, Password, Login controls. No domain field in this deployment. |
| S3 | Login as `admin` with the session password reaches the dashboard | validated | `admin` login reached the dashboard (Signed in + Dashboard, no domain selector). Licensing card anomaly diagnosed separately: no licensing Ingress and no `LICENSING_SERVER_BASE_URL`; login validated, licensing not. |
| S4 | Transfers, Deployments, and Cloud Endpoints render with empty lists | validated | All three navigation links displayed their empty-project messages without an error banner. |
| S5 | Logs navigation lists appliance components through the adaptor | validated | Authenticated /logging showed Download/Stream tabs and component entries (coriolis-api, conductor, worker, keystone, mariadb, rabbitmq, bootstrap). Validates listing, not yet migration-window log content. |

## :material-book-open-page-variant-outline: Phase 6 -- Migration Prerequisites And Endpoints

| # | Checkpoint | Status | Evidence / notes |
| --- | --- | --- | --- |
| S6 | Preflight table confirmed: disposable volume-backed fixture `ACTIVE` with marker; Cinder backup to Swift proven; destination quota, image, network, flavor, security group, keypair, FIP pool, and volume type visible to the endpoint project | validated | Closed by read-only audit. Fixture `ACTIVE` with serial-console marker verified via SDK. Cinder backup to Swift proven concretely by the 8 GiB (8589934592-byte) task-accounted replication. Destination quota question closed: Nova limits 10 instances / 20 cores / 59392 RAM, Neutron 50 FIPs / 10 routers; both real migrations allocated resources successfully, proving scoped visibility/capacity. |
| S7 | Source endpoint created (Identity v3) and shows `Endpoint is Valid` | validated | Created through the UI with Identity API v3 explicitly selected; details > Validate Endpoint displayed `Endpoint is Valid`. Endpoint ID kept in the private run inventory. |
| S8 | Destination endpoint created and shows `Endpoint is Valid` | validated | Created with Identity v3; details > Validate Endpoint displayed `Endpoint is Valid`. Shared destination project explicitly authorized; only isolated validation resources modified. |
| S9 | Both endpoint IDs recorded for the headless config | validated | IDs taken from the two browser detail URLs and stored only in the ignored run config. |

## :material-book-open-page-variant-outline: Phase 7 -- Headless Migration

| # | Checkpoint | Status | Evidence / notes |
| --- | --- | --- | --- |
| S10 | Private workspace `.openstack/tutorial-validation/` exists and is repository-ignored | validated | `mkdir -p` succeeded; `git check-ignore` confirmed the directory is ignored. Private configs are not publication artifacts. |
| C21 | Example config copied to `.openstack/tutorial-validation/headless-migration.json` | validated | Exact `cp` command succeeded with no output. |
| S11 | All `<...>` placeholders replaced with real values (helper refuses otherwise) | validated | Config resolved from the exact fixture/network/access ledgers; no placeholders remained; only the isolated destination network, SG, and imported keypair used. |
| C22 | `python3 -m json.tool` parses the edited config | validated | Exact tutorial command exited successfully with no output. |
| C23 | Helper run completes with the fixed `PASS`/`SUMMARY` contract (preflight, transfer, execution `COMPLETED`, deployment `COMPLETED`) | validated | After correcting admin/admin scope, the exact documented pipeline returned PASS preflight, PASS transfer, PASS execution COMPLETED, PASS deployment COMPLETED, and `SUMMARY headless-migration passed`; exact IDs stored privately. |

## :material-book-open-page-variant-outline: Phase 8 -- Observe The Headless Result

| # | Checkpoint | Status | Evidence / notes |
| --- | --- | --- | --- |
| S12 | Both endpoints still listed valid and usable | validated | Both endpoints remain listed in Cloud Endpoints after migration; completed provider tasks prove they were usable during the execution. |
| S13 | Transfer matching the unique notes shows one execution `COMPLETED` | validated | Transfers list matched the unique headless notes; Execution #1 displayed COMPLETED with the helper's exact execution ID, including the disk-replication timeline. |
| S14 | Correlated deployment shows `COMPLETED` | validated | Deployments list opened the helper's correlated deployment ID; its details show COMPLETED. |
| S15 | Execution and deployment task timelines fully completed, none `ERROR` | validated | All displayed execution and deployment task statuses COMPLETED, none ERROR; the deployment has six completed tasks. |
| S16 | Source VM is `SHUTOFF` in the source cloud | validated | Read-only SDK query of the exact fixture server returned `SHUTOFF`, consistent with the execution's COMPLETED `SHUTDOWN_INSTANCE` task naming that instance. Boolean proof in private `headless-cloud-result.json`. |
| S17 | Destination VM `ACTIVE` with cloned boot disk, mapped networks, requested floating IP, and marker reachable in guest | validated | Usability proof, correlated strictly by exact IDs: destination server `ACTIVE`, single NIC on the created destination network, FIP from the configured pool bound to that exact port, new clone boot volume (ID differs from source) attached `in-use` at 9 GiB (provider ceil-rounding). SSH as `ubuntu` read `/var/tmp/coriolis-tutorial-marker` equal to the run marker and `cloud-init status` `done`. |
| S18 | Logs navigation shows conductor/scheduler/worker/deployer activity for the run window | validated | Browser Stream showed live lines; authenticated downloads for 20:20-20:45 UTC returned 200 with nonempty conductor/scheduler/worker/deployer-manager streams (685/20/1191/3 lines). Raw log content not recorded. |

## :material-book-open-page-variant-outline: Phase 9 -- Reset Before Repeating In The Web UI

| # | Checkpoint | Status | Evidence / notes |
| --- | --- | --- | --- |
| S19 | Headless-run migration artifacts removed before the UI repeat | validated | UI lists empty; Delete Disks Execution #2 COMPLETED; independent cloud checks found no migration VMs, disks, snapshots, backups, ports, or FIPs. Empty source Swift container retained for the second run; fixture and endpoints intentionally kept. |
| S20 | Fixture restored: source VM ACTIVE on the same retained boot volume and network | validated | One normal Nova start restored the exact fixture in ~15s. Caveat: cloud-init runcmd is once-per-instance, so an ordinary restart does not rerun the serial marker; the first-boot marker was verified and the second migrated guest re-proved it (S32). |
| S21 | Destination VM retained or removed as a deliberate decision | validated | Removed the exact headless guest via normal Nova deletion; clone volume auto-deleted, FIP and detached port removed by exact ID; all four objects confirmed absent. Replication disk kept for Delete Transfer Disks; default SG untouched. |
| S22 | Both endpoints kept for reuse | validated | Endpoint deletion deliberately skipped during intermediate cleanup; both validated endpoint records retained for the UI wizard. |

## :material-book-open-page-variant-outline: Phase 10 -- Full Web UI Migration Walkthrough

| # | Checkpoint | Status | Evidence / notes |
| --- | --- | --- | --- |
| S23 | Wizard opens on the scenario step (steps 1-2) and accepts the `live_migration` scenario | validated | New > Transfer opened /wizard/migration showing Coriolis Migration (not Replica); Next advanced to Source Cloud. |
| S24 | Source endpoint selected and `swift_backups` export mechanism accepted (steps 3-4) | validated | Selected the source endpoint via the dropdown; Source Options displayed Swift Backups and Next accepted it. |
| S25 | Fixture instance selected; inventory loads (step 5) | validated | Inventory loaded the isolated fixture as 2 vCPU / 4 GB / c1.small; selected only it (1 instance confirmed) and advanced. Unrelated source workload not selected. |
| S26 | Destination endpoint selected and all worker settings accepted (steps 6-7) | validated | Accepted unique title, c1.small, ubuntu-24.04, isolated network, dedicated keypair/SG, default worker volume type, worker and guest Use FIP=Yes, both IPv4 pool selectors, Preserve Fixed IPs=No. Note: three-position switches need the correct side selected, not the middle. |
| S27 | Every source NIC mapped; storage mapping `__DEFAULT__` (steps 8-9) | validated | Mapped the fixture's single source network to the isolated destination network; storage mapping set `__DEFAULT__` as Default Storage with backend entries inheriting. Both steps accepted Next. |
| S28 | Optional user scripts and recurring schedule skipped (steps 10-11) | validated | Left global/instance scripts and schedule empty; both steps advanced to the separate Execute step. |
| S29 | POC execution/deployment options accepted and Summary shown (step 12) | validated | Execute Now and Clone Disks already Yes; set Shutdown Instance(s), Auto Deploy, and Skip OS Morphing to Yes for this compatible Ubuntu fixture; Next reached Summary. |
| S30 | Finish creates the transfer and starts its execution (step 13) | validated | Finish returned HTTP 200 with live_migration, the exact fixture, correct endpoint IDs, clone_disks=true, skip_os_morphing=true; Executions displayed Execution #1 RUNNING. |
| S31 | Transfer execution reaches `COMPLETED`, then deployment reaches `COMPLETED` | validated | UI Execution #1 and all transfer tasks reached COMPLETED; the correlated deployment's six tasks and overall status COMPLETED, none ERROR, independently confirmed via GET-only observation of the same exact IDs. |
| S32 | Observation checks from Phase 8 repeated against the clouds for the UI-driven run | validated | Same read-only checks as S16/S17 rerun against the exact UI IDs: execution/deployment all COMPLETED; source fixture `SHUTOFF`; destination `ACTIVE` with correlated NIC, FIP, and new clone volume; SSH as `ubuntu` read the marker literal and `cloud-init status` `done`, independently re-proving the marker in the second migrated guest. Proof in private `ui-cloud-result.json`. |

## :material-book-open-page-variant-outline: Phase 11 -- Log Observation

| # | Checkpoint | Status | Evidence / notes |
| --- | --- | --- | --- |
| S33 | Producers non-empty over the run window (Memcached the documented exception) | validated | Header-authenticated (`X-Auth-Token`, never URL) sweep of `/logs` and all 14 listed components over 18:38-18:55 UTC: every producer returned 200 with nonempty bodies (3-661 lines). Memcached is the documented exception: not listed, and a probe returned 200 with an empty body. Counts only, in private `log-proof.json`. |
| S34 | Logging stack (Loki, gateway, Alloy, adaptor) readiness/readability confirmed without self-querying | validated | The same sweep proves the read path end to end without self-query: adaptor answered 200 on `/logs` and all 14 downloads via the ingress route; the Loki-derived listing and nonempty histories prove Loki reads and the Alloy collection path; no loki/gateway/alloy/adaptor appears in the list and none was queried. |
| S35 | No log search or filter used secret values | validated | Only component names, time ranges, statuses, and non-secret execution identifiers were used; credentials never search terms nor in public evidence. Browser credentials, cookies, and local state were cleared and the browser closed. |

## :material-book-open-page-variant-outline: Phase 12 -- Migration Cleanup

| # | Checkpoint | Status | Evidence / notes |
| --- | --- | --- | --- |
| S36 | Any active execution/deployment canceled to a terminal state first | n/a | Both real migrations and deployments completed normally; there was no active execution to cancel. No cancellation/force-cancellation behavior is claimed as validated. |
| S37 | Deployment record deleted; destination VM handling is a separate deliberate decision | validated | UI Delete Deployment removed the second completed record; separately, normal Nova deletion removed its guest, auto-deleted the clone, and its FIP and detached port were deleted by exact ID; all four absent; default SG and preexisting infrastructure untouched. |
| S38 | Actions > Delete Disks cleanup execution reaches `COMPLETED` | validated | Confirmed Delete Transferred Disks; the UI run's Execution #2 reached COMPLETED before its transfer was deleted. |
| S39 | Transfer deleted; absent from the UI | validated | Confirmed Delete Transfer after cleanup completion; the Transfers list is now empty. |
| S40 | Both endpoints deleted; list empty and Barbican-backed credentials removed with them | validated | Both endpoints deleted via the UI; empty list confirmed. Both exact Barbican secret metadata URLs returned 200 before deletion and 404 afterward; no secret payload read. |
| S41 | Independent cloud verification: no validation-owned cloud artifacts remain | validated | All exact created IDs absent on both clouds; source counts restored to baseline (1 server, 17 networks/subnets, 57 ports, 2 FIPs, 40 SGs, 1 keypair, no volumes/snapshots/backups, 2 original Swift containers) with the router's original gateway and 14 ports restored; destination baseline SG/net/router/FIP IDs retained and validation-prefixed resources absent. Caveat: the initial Cinder inventory missed 2 preexisting infra volumes/snapshots due to an SDK filter; both verified to predate the run with non-residual attachments. Source baseline lacked FIP bindings; no API ever wrote bindings. |

## :material-book-open-page-variant-outline: Phase 13 -- Optional Runtime Removal

| # | Checkpoint | Status | Evidence / notes |
| --- | --- | --- | --- |
| C24 | `kubectl delete coriolisappliance coriolis-appliance-advanced` completes through the supported path | validated | Metadata-only PVC/PV/TLS inventory captured; CR UID matched the creation ledger. Exact --wait=true --timeout=10m command returned deleted with no manual finalizer edits or force flags. Retained state was checked separately before the full reset. |
| C25 | Appliance label Pod list is empty after deletion (`No resources found`) | validated | 2026-09-09 run: the exact label command returned `No resources found in coriolis namespace.` immediately after the C24 deletion; no wait or mutation needed. |
| C26 | Three data PVCs remain Bound after CR deletion, before full reset | validated | All three remained Bound on local-path (10Gi/1Gi/10Gi), matching the pre-deletion inventory. Confirmed retention first; later R2 deliberately removed the claims for a fresh start. |

## :material-book-open-page-variant-outline: Phase 14 -- Full Fresh Reset

Rows are ordered chronologically as executed; note that R6 ran before R4 (it was the TLS-Secret deletion prerequisite).

| # | Checkpoint | Status | Evidence / notes |
| --- | --- | --- | --- |
| R1 | Label-filtered metadata enumeration returns exactly the seven retained credential Secrets and three retained data PVCs (KIND/NAME only, no Secret data) | validated | 2026-09-09 run: the exact label query returned exactly 10 rows -- the seven credential/key Secrets and the three Bound data PVCs -- matching the expected result; no Secret data decoded. The unlabeled cert-manager TLS Secret persists outside this query and is handled separately by R4. |
| R2 | Delete the three data PVCs by exact name with `--wait=true --timeout=5m`; three `deleted` lines | validated | All PVC UIDs verified against inventory, deleted by exact name with three `deleted` confirmations; all three recorded PVs returned NotFound via automatic Delete reclaim; no PV manually deleted. |
| R3 | Delete the exact seven credential Secrets by name; seven `deleted` lines | validated | Exact command returned seven `deleted` confirmations for the generated credential/key Secrets; both registry pull Secrets excluded. |
| R6 | Namespace-wide `get certificate,ingress -o name` returns nothing | validated | Executed before the R4 TLS Secret deletion; exited with no output. This prerequisite was moved earlier in the tutorial and its expected output corrected. |
| R4 | Delete the run-created TLS Secret only after confirming it is not baseline/shared, no remaining Certificate/Ingress references, and the recorded run UID matches | validated | R6 confirmed no remaining Certificate/Ingress references; the TLS Secret UID matched the run-created inventory and it was absent from baseline; the exact delete command succeeded. |
| R5 | Label-filtered sweep of deploy, sts, pod, job, svc, cm, secret, pvc, ingress, sa, role, rolebinding returns nothing | validated | Exact multi-kind label query returned nothing; recorded PVs already confirmed NotFound in R2. Final namespace inventory: only the operator Pod/Deployment/SA/Role/RoleBinding, the default SA, the kube-root CA ConfigMap, and two pull Secrets -- no appliance resources, PVs, retained PVCs, or TLS Secret. |
| R7 | Operator Deployment `coriolis-operator` still `1/1` | validated | Final exact command reports READY 1/1, UP-TO-DATE 1, AVAILABLE 1; the operator remained installed throughout cleanup. |
| R8 | Argo CD `coriolis` Application still `Synced` / `Healthy` | validated | Final exact command returned `coriolis Synced Healthy`; the shared Argo Application was not modified. |

## :material-book-open-page-variant-outline: Recording Rules

- Update rows in place with the Run ID of this file; open a new run section (new Run ID) for any re-run rather than overwriting evidence.
- `C` numbers identify the original command checkpoints, not current line positions. `S` groups related UI/cloud checks and includes workspace creation; `R` identifies fresh-reset commands. Tutorial step numbering can change as instructions are corrected.
- Evidence cells must stay secret-free: no passwords, tokens, endpoint credentials, or raw config content. Non-secret identifiers (endpoint IDs, transfer IDs) may be noted where the tutorial itself records them.
- A run is only complete when every row is `validated`, `render-validated`, or an explicitly justified `n/a`, and the final section below is filled.

### :material-application-edit-outline: Run Outcome Summary

| Item | Value |
| --- | --- |
| Completed on | 2026-09-09T22:55:30Z (run start 2026-09-09T18:38:53Z) |
| Rows validated | 73 of 75 (26 C + 41 S + 8 R rows) |
| Rows render-validated or `n/a` and justification | C1 `render-validated`: chart `0.5.59` rendered cleanly but was deliberately not live-installed (Argo CD owns the live operator). S36 `n/a`: both migrations completed normally, so there was no active execution to cancel. |
| Final housekeeping | Complete: private workspace, temporary keys/configs, verification scripts, and this run's Python caches removed. Original cloud configs and a pre-existing historical helper cache preserved. Browser session cleared and closed; only this sanitized public record remains as the run summary. |
| Overall verdict | Bounded hands-on PASS: every checkpoint actually executed in run `adv-tut-2026-09-09-01` succeeded with recorded evidence, subject to the render-only (C1) and N/A (S36) caveats. This is not a claim that everything was tested beyond the tutorial's declared scope. |

## :material-book-open-page-variant-outline: Related Pages

- [Coriolis Operator Advanced Tutorial](operator-advanced-tutorial.md) -- the procedure being validated.
- [Coriolis Operator](operator.md) -- operator's own validated scope.
- [Migration Flow](migration-flow.md) and [OpenStack Context](openstack-provider.md) -- migration contract.
