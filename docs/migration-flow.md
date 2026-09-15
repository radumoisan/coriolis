# Migration Flow

!!! abstract
    Coriolis coordinates transfer executions that copy or synchronize workload disks, then separately deploys the destination VM when requested. This page describes the implemented OpenStack-to-OpenStack flow at a high level.

## :material-book-open-page-variant-outline: Migration And Replica

A transfer defines the source and destination endpoints, selected instances, and destination mappings. A migration transfer prepares data for a move to the destination. A replica transfer can be executed again later to synchronize the existing replica disks with newer source data. Neither transfer scenario should be understood as a zero-downtime guarantee; source shutdown is an execution option, not a universal step.

## :material-book-open-page-variant-outline: Lifecycle

```text
[Endpoints] -> [Transfer definition] -> [Transfer execution]
                                              |
                                [Disk transfer / synchronization]
                                              |
                                     [Transfer complete]
                                      |                \
                                      |                 -> [Separate deployment execution]
                                      |                              |
                                      |                   [Deployment complete]
                                      v
      [Later replica execution] -> [Disk transfer / synchronization]
                                        |
                                 [Transfer complete]
```

Transfer completion makes transferred disk state available; it does not create the destination VM. A deployment is a separate execution, whether started after a completed transfer or requested automatically by a transfer option.

## :material-book-open-page-variant-outline: Stages And Components

| Stage | Responsible components |
| --- | --- |
| Define endpoints and transfer | Web UI or API, Conductor, and provider plugins |
| Start or schedule a transfer execution | Conductor; Transfer Cron for scheduled executions |
| Select work capacity | Scheduler selects compatible Worker services and Minion Manager allocates pool minions when a configured pool is used |
| Transfer or synchronize disks | Worker services, the source OpenStack export provider plugin, and the destination OpenStack import provider plugin |
| Create and run a deployment | Conductor and Worker services; Deployer Manager waits for an automatic deployment when one was requested |
| Create the destination VM | Destination OpenStack import provider plugin during deployment |

## :material-book-open-page-variant-outline: OpenStack Data Path

For an OpenStack source endpoint, the OpenStack export provider plugin gathers instance and disk information, then uses the selected supported mechanism to obtain disk data. Depending on that mechanism and configuration, it can use snapshots or backups and can create operation-scoped temporary worker VMs. The synchronization path sends disk contents to destination-side storage managed by the destination OpenStack import provider plugin. Incremental synchronization is used only when the selected mechanism and available prior state support it.

The transfer leaves destination disk state available for later use. A separate deployment can create snapshots or clones as needed, prepare destination resources, and use the destination OpenStack import provider plugin to create the destination OpenStack VM with its disks and mapped networking. OS morphing, which adapts an offline guest operating-system disk for the destination environment, is optional and runs only when it is not skipped and the deployment requires it.

## :material-book-open-page-variant-outline: Status, Cleanup, And Validation

Transfers and deployments have separate executions and statuses. A completed transfer is a prerequisite for a normal deployment, but it is not proof that the deployment completed or that the destination VM is usable.

Cleanup is distributed across transfer, deployment, and provider plugin tasks. It can release allocated minions, remove temporary worker VMs and other source or destination artifacts, remove snapshots, or clean up failed deployment artifacts, depending on the path taken. It is not a single final phase common to every execution.

!!! warning
    End-to-end validation is bounded: one actual-browser development Web UI OpenStack-to-OpenStack migration proof of concept has passed on released operator 0.5.54, and the walkthrough now split into [headless](headless-migration.md) and [Web UI](web-ui-migration.md) migration phases has been followed end to end on operator 0.5.59 with runtime 2603.4. See [validation history](technical-debt.md#validation-history) for the bounded scope. All production-readiness claims remain unvalidated.
