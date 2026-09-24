# Phase 1: Headless Migration

This tutorial creates one real Coriolis live migration from the command line. The helper reads a configuration file, receives the Keystone password on standard input, validates its URLs, configuration, and saved endpoints, creates one transfer and execution, and polls them to completion. When auto-deploy is enabled, it also finds and follows the correlated deployment. It deliberately performs no cleanup.

## :material-book-open-page-variant-outline: Create Source And Destination Endpoints

Create and validate the source and destination OpenStack endpoints in the Web UI before using the helper. The endpoint names are up to you, but record both endpoint IDs after they are saved.

1. Open **Cloud Endpoints** and select **Add Endpoint** (or **New > Endpoint**).
2. Select **OpenStack** and enter the credentials and API details for one cloud.
3. Validate and save the endpoint, then repeat for the other cloud.

The helper authenticates to the appliance as a Keystone user; it does not send the source or destination cloud passwords. Those credentials remain in the saved endpoint secrets.

## :material-book-open-page-variant-outline: Headless Real Migration

!!! danger "This is a real migration"
    The run creates cloud resources, can shut down the source instance, and can deploy a destination instance. Use a disposable fixture only.

### :material-application-edit-outline: Prerequisites

- A disposable, volume-backed source instance with one bootable volume. See [OpenStack Migration Prerequisites](openstack-provider.md#openstack-migration-prerequisites).
- Saved and validated source and destination endpoints, plus their IDs, the source instance ID, and the destination resource names and IDs required by the configuration.
- Python 3 and `kubectl` access to the appliance namespace and the Secret that contains the Keystone password. See [Web Login And Visual Inspection](deploy-appliance.md#web-login-and-visual-inspection) for appliance access.
- Sufficient source and destination quota, capacity, network reachability, images, flavors, networks, security groups, keypairs, and floating-IP pools. The [Lab Environment](operator-lab-environment.md) describes a suitable test environment.

### :material-application-edit-outline: Download And Configure

In a local working directory, download these two files:

- Download [coriolis-headless-migration.py](assets/scripts/coriolis-headless-migration.py).
- Download [headless-migration.jsonc](assets/manifests/headless-migration.jsonc).

??? quote "coriolis-headless-migration.py"

    ```python
    --8<-- "assets/scripts/coriolis-headless-migration.py"
    ```

??? quote "headless-migration.jsonc"

    ```jsonc
    --8<-- "assets/manifests/headless-migration.jsonc"
    ```

The JSONC comments explain every setting. Replace every angle-bracket placeholder before continuing. `transfer.notes` must be unique for this run; `shutdown_instances` controls whether the source is powered off after migration, and `auto_deploy` controls whether the helper creates and follows the destination deployment. Keep `skip_os_morphing` enabled only for a known-compatible disposable fixture.

The helper accepts JSON or JSONC. Validate the completed file locally before making API calls:

<!-- Validate the completed JSONC file with the downloaded helper. -->
```bash
python3 coriolis-headless-migration.py --config headless-migration.jsonc --validate-config
```

??? example "Expected result"

    ```text
    PASS config
    ```

### :material-application-edit-outline: Run The Migration

Replace every angle-bracket value in this command with your appliance details. The helper defaults to the `coriolis` user and `service` project; specify `--username` and `--project-name` when the endpoints are visible in a different Keystone scope. It authenticates with the `Default` user and project domains.

The password is read through standard input rather than placed in a command argument, shell history, or configuration file. Use the correct password key from your appliance Secret.

<!-- Pipe the Keystone password into the helper without exposing it in the command line. -->
```bash
kubectl -n "<appliance-namespace>" get secret "<keystone-password-secret>" -o jsonpath='{.data.<password-key>}' | base64 -d | python3 coriolis-headless-migration.py --api-base "https://<appliance-host>/coriolis" --keystone-base "https://<appliance-host>/identity" --username "<keystone-username>" --project-name "<keystone-project>" --config headless-migration.jsonc --timeout 1800 --poll-interval 10 --run
```

??? example "Expected result"

    ```text
    PASS preflight
    PASS transfer id=<transfer-id>
    PASS execution id=<execution-id> status=COMPLETED
    PASS deployment id=<deployment-id> status=COMPLETED
    SUMMARY headless-migration passed
    ```

`--run` is an explicit acknowledgement that the command writes to both clouds. `--timeout 1800` allows up to 30 minutes for each polling phase, rather than imposing a 30-minute limit on the whole run. `--poll-interval 10` checks progress every 10 seconds. With `auto_deploy` enabled, success includes the correlated deployment; without it, the helper stops after the transfer execution completes.

The output contains fixed status lines and never prints the password, token, request payload, or error body. Keep the reported object IDs for observation. The helper does not clean up the transfer, execution, deployment, or cloud resources.

## :material-book-open-page-variant-outline: Observe The Headless Result

1. Open **Cloud Endpoints**.
   **Expected outcome:** both endpoints remain valid and usable.
2. Find the transfer with your unique notes and open its execution.
   **Expected outcome:** the execution is `COMPLETED`.
3. When auto-deploy is enabled, open the correlated deployment and its latest execution.
   **Expected outcome:** both are `COMPLETED`.
4. Review the execution and deployment task timelines.
   **Expected outcome:** all tasks are complete and none is in `ERROR`.
5. Check the source instance.
   **Expected outcome:** it is `SHUTOFF` when `shutdown_instances` is `true`.
6. Check the destination instance, boot volume, mapped network, security groups, and floating IP when requested. Verify the workload marker inside the guest.
   **Expected outcome:** the instance is `ACTIVE` and the workload is usable. A completed Coriolis workflow alone does not prove guest usability.
7. Review appliance logs around the migration window if further evidence is needed. See [Log Observation](web-ui-migration.md#log-observation).

From inside the migrated guest, confirm cloud-init has finished:

<!-- Inside the migrated guest, check cloud-init status. -->
```bash
cloud-init status
```

??? example "Expected result"

    ```text
    status: done
    ```

Check the workload marker, disks, and networking even when cloud-init reports `done`; a cloned boot disk can preserve state from the source.

## :material-book-open-page-variant-outline: Reset Before Repeating In The Web UI

1. Follow [Migration Cleanup](web-ui-migration.md#migration-cleanup) for the transfer, deployment, disks, and other run-created cloud artifacts, but keep both endpoints.
   **Expected outcome:** no migration artifacts remain while the endpoints remain available.
2. Restore or rebuild the disposable source instance so it is `ACTIVE`, attached to the expected source network, and contains the workload marker.
   **Expected outcome:** the source satisfies the migration prerequisites again.
3. Continue with [Phase 2: Full Web UI Migration Walkthrough](web-ui-migration.md#full-web-ui-migration-walkthrough) using the same endpoints.

## :material-book-open-page-variant-outline: Troubleshooting

| Symptom | Response |
| --- | --- |
| `ERROR category=config_unresolved_placeholder` | Replace every angle-bracket placeholder in `headless-migration.jsonc`, then run the local validation command again. |
| `ERROR category=preflight_failed` | No migration write occurred. Confirm the endpoint IDs are visible to the selected Keystone project and that no transfer or deployment already uses the notes value. Resolve the existing run instead of bypassing duplicate protection. |
| `ERROR category=post_ambiguous` | A create request could not be confirmed. Inspect the UI for objects with the unique notes before deciding what happened. Do not blindly retry a POST request. |
| A transient network error while polling | Polling GET requests tolerate up to three consecutive transient network failures. If the helper stops, verify appliance connectivity and the object state before running anything again. |
| Execution or deployment failure or timeout | Inspect the associated object, task timeline, endpoint validity, destination capacity, and appliance logs. `--timeout` applies separately to execution, deployment discovery, and deployment polling. |
| Any other `ERROR category=...` | The error is terminal and safely reports only a category and HTTP status. Stop and diagnose the indicated phase before retrying. |
