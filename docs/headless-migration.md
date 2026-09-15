# Phase 1: Headless Migration

This first phase uses the concrete setup described in [Lab Environment](operator-lab-environment.md). It assumes the successful deployment and login described in [Web Login And Visual Inspection](deploy-appliance.md#web-login-and-visual-inspection). Prepare the endpoints through the Web UI, then perform the headless migration before continuing to Phase 2.

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

Create and save both endpoints through the Web UI before any headless test: the headless helper only works against saved endpoints that have passed validation.

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

## :material-book-open-page-variant-outline: Headless Real Migration

!!! danger "This is a real migration"
    Running the helper creates a Transfer, executes it against both live clouds, deploys the destination VM, and can shut down the source. Use it only with the disposable fixture from the prerequisites section. The helper performs one migration, never any cleanup, and leaves the transfer, execution, deployment, and all cloud objects visible in the Web UI for observation.

The helper `deploy/coriolis-headless-migration.py` works only against the two saved endpoints from the previous section. Its configuration contract is [headless-migration.example.json](assets/manifests/headless-migration.example.json).

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

The helper currently requires both the user and project to be in Keystone's `Default` domain.

A small migration often takes 10 to 30+ minutes. `--timeout 1800` gives each polling phase up to 30 minutes; it is not a total run limit.

<!-- Feed the Keystone admin password into the helper in the same project as the Web UI. -->
```bash
kubectl --context virt-infra-dev-buc-hq -n coriolis get secret coriolis-appliance-advanced-infrastructure-credentials -o jsonpath='{.data.keystone_admin_password}' | base64 -d | python3 deploy/coriolis-headless-migration.py --api-base https://coriolis.app.cloudbase.wiki/coriolis --keystone-base https://coriolis.app.cloudbase.wiki/identity --username admin --project-name admin --config .openstack/tutorial-validation/headless-migration.json --timeout 1800 --poll-interval 10 --run
```

??? example "Expected result"

    ```text
    PASS preflight
    PASS transfer id=3f205a3f-581a-48c4-8357-774525052e73
    PASS execution id=bfcd1c48-d37c-4549-b880-cbbdd473c7f6 status=COMPLETED
    PASS deployment id=cc2c27cb-877e-456f-a9ab-04828669458d status=COMPLETED
    SUMMARY headless-migration passed
    ```

The three IDs are the objects created by the current run. Your IDs will differ: record them for the observation and cleanup steps, never configure or reuse them as inputs.

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
   **Expected outcome:** conductor, scheduler, worker, and deployer activity is visible for the run; you never search logs for secret values to confirm any of this. For detailed log observation, see [Log Observation](web-ui-migration.md#log-observation).

Inside the migrated guest, reached over SSH using its floating IP and keypair, also check cloud-init. Run this in the guest, not on the Kubernetes workstation:

<!-- Inside the migrated guest, confirm cloud-init completed. -->
```bash
cloud-init status
```

??? example "Expected result"

    ```text
    status: done
    ```

If it is still running, wait and check again. Investigate errors inside the guest before declaring it usable. Even `done` does not replace reading your marker file and checking the disks and network: a cloned disk can preserve cloud-init state from the source.

!!! warning "Completion is not usability"
    `COMPLETED` statuses prove the Coriolis workflow finished. Guest usability is a separate conclusion you only reach from step 6: boot state, disks, networking, and your marker.

## :material-book-open-page-variant-outline: Reset Before Repeating In The Web UI

Do not start Phase 2 on top of the headless migration leftovers.

1. Perform the [Migration Cleanup](web-ui-migration.md#migration-cleanup) section first, for the headless transfer, deployment, disks, and cloud artifacts, but intentionally skip its endpoint-deletion step: this reset keeps both endpoints.
   **Expected outcome:** no headless transfer, deployment, or migration artifacts remain. Keep the fixture infrastructure and both endpoints; an empty run-created Swift export container may also be kept for the repeat, then removed during final cleanup.
2. Intentionally restore the fixture: restart, recreate, or rebuild the disposable source VM so it is `ACTIVE` with the marker again, on the same source network. Verify the marker before starting Phase 2.
   **Expected outcome:** the source VM matches the prerequisites table again.
3. Keep both endpoints.
   **Expected outcome:** the UI walkthrough can reuse the saved endpoints without re-entering credentials.

!!! note "Cloud-init markers run once per instance"
    A normal restart does not rerun cloud-init `runcmd` or produce a new first-boot serial marker. After restoring the source, check the persisted marker inside the guest; if you recreated or rebuilt it, verify that initialization wrote the marker again. Do not mistake an old console message or `cloud-init status: done` for proof of a new initialization run.

The reset is an explicit prerequisite for [Phase 2: Full Web UI Migration Walkthrough](web-ui-migration.md#full-web-ui-migration-walkthrough); continue with the same appliance and saved endpoints, not a fresh appliance.

## :material-book-open-page-variant-outline: Troubleshooting

| Symptom | Likely cause and response |
| --- | --- |
| Helper prints `ERROR category=post_ambiguous` | A POST's outcome could not be confirmed and the helper refused to guess. Inspect transfers and deployments for the unique notes in the UI before deciding; never blindly retry a write. |
| Any other helper `ERROR category=...` | Each category is fixed and terminal (config, preflight, authentication, network, execution/deployment failure or timeout). Stop, match the category to the phase, and diagnose before re-running. |
| Helper prints `ERROR category=preflight_failed` | No migration write occurred. Check endpoint IDs and the Keystone project scope first, then inspect existing transfers/deployments with the same notes. Resolve or clean the existing run before retrying; choose fresh notes only for a deliberately new migration, not to bypass duplicate protection. |
