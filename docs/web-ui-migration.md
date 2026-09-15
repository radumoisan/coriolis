# Phase 2: Web UI Migration

This second phase follows [Reset Before Repeating In The Web UI](headless-migration.md#reset-before-repeating-in-the-web-ui). Reuse the `Ready`/`LoggingReady` appliance from the [Lab Environment](operator-lab-environment.md), both saved and validated endpoints, and the restored source fixture from Phase 1.

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
7. In the simple target options set: a unique **Title** (this run's notes), the worker **Migration Flavor** name `c1.small` (a searchable field), the Linux entry of the **Migration Image Map** (in this example, the `ubuntu-24.04` image, matching the source and destination guest OS), and the dedicated **Migration Network**.
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
15. Verify the new transfer has the correct endpoints and one instance, and its **Execution #1** starts. Confirm creation from the Executions tab; browser network inspection can provide an additional check.
    **Expected outcome:** the UI opens the transfer's Executions tab and shows the running execution, not merely a saved transfer record.
16. Watch **Executions** until the transfer reaches `COMPLETED`, then open the correlated entry in **Deployments** and inspect its **Tasks** tab. A small migration often takes 10 to 30+ minutes, depending on the source and destination cloud.
    **Expected outcome:** both execution and deployment reach `COMPLETED`, with no failed tasks. Completion alone does not prove guest usability; perform the observation checks below.
17. If any task or execution shows an `ERROR` status, stop.
    **Expected outcome:** you diagnose through the task details and the Logs navigation before touching anything; a failed execution is not blindly re-run.

Then, once your current UI execution actually completes, repeat the observation checks from [Observe The Headless Result](headless-migration.md#observe-the-headless-result) against the clouds, rather than checking prior run IDs.

## :material-book-open-page-variant-outline: Log Observation

The Logs navigation queries the appliance's own Loki-backed logging through the authenticated UI session.

- Look around the migration window for `coriolis-conductor`, `coriolis-scheduler`, `coriolis-worker`, `coriolis-deployer-manager`, `coriolis-api`, and `coriolis-web`. Quiet components need not emit continuously, and retention removes older entries.
- A successful log request can return empty content for Memcached; that alone is not a logging failure. An adaptor error or missing logs across active producers needs investigation. Loki, gateway, Alloy, and adaptor are excluded from the application's producer listing to avoid self-collection; use their Kubernetes readiness and container logs when diagnosing the logging stack itself.
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
5. Delete both endpoints. This is the full final cleanup and is the step deliberately skipped during [Reset Before Repeating In The Web UI](headless-migration.md#reset-before-repeating-in-the-web-ui).
   **Expected outcome:** the endpoint list is empty and, because each endpoint's connection payload lives in Barbican behind a `secret_ref`, the Barbican-backed endpoint credentials are removed with them.
6. Independently verify both clouds are back to the baseline: no temporary worker VMs, no leftover ports or floating IPs from workers, no Cinder backups or Swift objects from the export path, no snapshots or temporary images, and only the intentional source and destination VMs remain.
   **Expected outcome:** every artifact you can attribute to the run is gone or explicitly kept by decision.

An empty Swift export container can remain after disk cleanup. In this run the source container `coriolis` was absent before validation and empty afterward; final reset removed it. Delete an empty container only when the baseline and migration evidence establish that this run created it. Never remove a pre-existing/shared container or delete unknown objects to make it empty. Also remove any disposable fixture infrastructure you created, restoring only your recorded router interfaces and leaving pre-existing networks, keys, security groups, and floating IP bindings untouched.

After completing migration cleanup for both phases in the same environment, you can optionally [remove the runtime](deploy-appliance.md#optional-runtime-removal) or perform a [full fresh reset](deploy-appliance.md#full-fresh-reset).
