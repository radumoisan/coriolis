# Phase 1: Headless Migration

This tutorial creates one real Coriolis live migration from the command line. The helper reads a configuration file and the Keystone password from `CORIOLIS_KEYSTONE_PASSWORD` (with standard input as a fallback), validates its URLs, configuration, and saved endpoints, creates one transfer and execution, and polls them to completion. When auto-deploy is enabled, it also finds and follows the correlated deployment. It deliberately performs no cleanup.

## :material-book-open-page-variant-outline: Create Source And Destination Endpoints

The helper requires two saved, validated endpoints. Create the source endpoint first, then repeat these same three steps for the destination using that cloud's values.

1. Open **Cloud Endpoints**.<br>
   &emsp;⤷ Choose **Add Endpoint** (or **New > Endpoint** for a non-empty list).<br>
   &emsp;&emsp;⤷ Select **OpenStack**.
2. Fill in the required parameters:

    | Parameter | Value (source) | Value (destination) |
    | --- | --- | --- |
    | Name | `source-openstack` | `destination-openstack` |
    | Description | `Source OpenStack cloud` | `Destination OpenStack cloud` |
    | Username | `coriolis` | `coriolis` |
    | Password | `Passw0rd123!` | `Passw0rd123!` |
    | Authentication URL | `https://keystone.virtomat.dev/v3` | `https://devopscentral.cloud:5000` |
    | Project Name | `coriolis` | `coriolis` |
    | Glance API Version | `2` | `2` |
    | Identity API Version | `3` | `3` |
    | User Domain | `Default` | `Default` |
    | Project Domain | `Default` | `Default` |
    | Region | `RegionOne` | `RegionOne` |
    | Interface | `public` | `public` |

    !!! warning "Replace the placeholder password"
        `Passw0rd123!` is an example only. Enter the actual password for each cloud's `coriolis` user before validating the endpoints.

3. Validate and save

!!! tip "Where the credentials actually live"
    The operator-managed Barbican on this appliance stores the encrypted connection payload as a Barbican secret; the Coriolis endpoint object itself contains only the returned `secret_ref`. That is why the UI reports the endpoint valid only after both the secret is `ACTIVE` and the provider connection test succeeds, and why deleting the endpoint is expected to remove its Barbican-backed credential as part of cleanup.

## :material-book-open-page-variant-outline: Headless Real Migration

!!! danger "This is a real migration"
    The run creates cloud resources, can shut down the source instance, and can deploy a destination instance. Use a disposable fixture only.

### :material-application-edit-outline: Configuration

In a local working directory, create these two files using the content below:

??? quote "coriolis-headless-migration.py"

    ```python
    --8<-- "assets/scripts/coriolis-headless-migration.py"
    ```

??? quote "headless-migration.yaml"

    ```yaml
    --8<-- "assets/manifests/headless-migration.yaml"
    ```

- The YAML is prefilled with the resource names and IDs created in the linked source and destination setup sections.
- `transfer.notes: headless-real-migration` identifies this migration. It is unused now, but after running a migration, use a different value for another run unless the previous transfer and deployment were removed.
- `skip_os_morphing: true` skips guest OS adaptation. Keep it enabled only for this tested disposable VM; other workloads may require OS morphing.

Install PyYAML in the Python environment that runs the helper:

<!-- Install the YAML dependency for the helper. -->
```bash
python3 -m pip install PyYAML
```

??? example "Expected result"

    ```text
    Successfully installed PyYAML-6.0.3
    ```

Validate the completed YAML file locally before making API calls:

<!-- Validate the completed YAML file with the helper. -->
```bash
python3 coriolis-headless-migration.py --config headless-migration.yaml --validate-config
```

??? example "Expected result"

    ```text
    PASS config
    ```

### :material-application-edit-outline: Run The Migration

The appliance `admin` user in the `admin` project owns the saved endpoint objects, so the helper authenticates in that same Keystone scope.

The helper reads `CORIOLIS_KEYSTONE_PASSWORD`; the password is not placed in command arguments, configuration, or command history.

<!-- Store and export the decoded Keystone password for the helper. -->
```bash
export CORIOLIS_KEYSTONE_PASSWORD="$(
  kubectl --context virt-infra-dev-buc-hq -n coriolis get secret coriolis-appliance-advanced-infrastructure-credentials -o jsonpath='{.data.keystone_admin_password}' | base64 -d
)"
```

??? example "Expected result"

    ```text
    No output.
    ```

<!-- Run the migration with the exported Keystone password. -->
```bash
python3 coriolis-headless-migration.py \
    --api-base "https://coriolis.app.cloudbase.wiki/coriolis" \
    --keystone-base "https://coriolis.app.cloudbase.wiki/identity" \
    --username admin --project-name admin \
    --config headless-migration.yaml \
    --timeout 1800 \
    --poll-interval 10 \
    --run
```

??? example "Expected result"

    ```text
    PASS preflight
    PASS transfer id=<transfer-id>
    PASS execution id=<execution-id> status=COMPLETED
    PASS deployment id=<deployment-id> status=COMPLETED
    SUMMARY headless-migration passed
    ```

!!! note ""
    `--run` is an explicit acknowledgement that the command writes to both clouds.

    `--timeout 1800` allows up to 30 minutes for each polling phase, rather than imposing a 30-minute limit on the whole run.

    `--poll-interval 10` checks progress every 10 seconds.

The output contains fixed status lines and never prints the password, token, request payload, or error body. Keep the reported object IDs for observation. The helper does not clean up the transfer, execution, deployment, or cloud resources.

After the helper finishes, remove the password from the current shell:

<!-- Remove the Keystone password from the current shell. -->
```bash
unset CORIOLIS_KEYSTONE_PASSWORD
```

??? example "Expected result"

    ```text
    No output.
    ```

## :material-book-open-page-variant-outline: Observe The Headless Result

1. Open **Cloud Endpoints**.<br>
   &emsp;⤷ **Expected outcome:** both endpoints remain valid and usable.
2. Find the transfer with your unique notes and open its execution.<br>
   &emsp;⤷ **Expected outcome:** the execution is `COMPLETED`.
3. When auto-deploy is enabled, open the correlated deployment and its latest execution.<br>
   &emsp;⤷ **Expected outcome:** both are `COMPLETED`.
4. Review the execution and deployment task timelines.<br>
   &emsp;⤷ **Expected outcome:** all tasks are complete and none is in `ERROR`.
5. Check the source instance.<br>
   &emsp;⤷ **Expected outcome:** it is `SHUTOFF` when `shutdown_instances` is `true`.
6. Check the destination instance, boot volume, mapped network, security groups, and floating IP when requested. Verify the workload marker inside the guest.<br>
   &emsp;⤷ **Expected outcome:** the instance is `ACTIVE` and the workload is usable.
7. Review appliance logs around the migration window if further evidence is needed. See [Log Observation](web-ui-migration.md#log-observation).<br>
   &emsp;⤷ **Expected outcome:** the logs corroborate the completed tasks without migration errors.

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
