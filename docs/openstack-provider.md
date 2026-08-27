# OpenStack Context

!!! abstract
    This page covers the initial OpenStack-to-OpenStack migration path. A transfer copies or synchronizes disks; deployment is a separate step described in [Migration Flow](migration-flow.md).

## :material-book-open-page-variant-outline: Current Scope

Use this guidance to prepare one source workload and its destination resources. It is not an exhaustive provider reference or a production-readiness claim.

See [Terminology](terminology.md) for definitions used on this page.

## :material-book-open-page-variant-outline: Cloud Prerequisites

Connect both endpoints with project-scoped permissions required by the selected transfer and deployment path and permitted by cloud policy. The identity and policy model is cloud-specific, but the project must allow Coriolis to perform the required read and lifecycle actions on the resources below.

| Service | Required access for the selected path |
| --- | --- |
| Nova | Read the source instance and attachments; create, inspect, and remove temporary worker VMs and create the destination Nova server during deployment. |
| Neutron | Read source and destination networking; create, inspect, attach, and remove temporary worker VM ports or destination ports and floating IPs when used. |
| Glance | Read source images and temporary worker VM images; create and remove temporary images when the path requires them. |
| Cinder | Read source volumes and create, attach, snapshot, clone, back up, and remove volumes as required by the selected disk path. |

Verify that the source and destination projects expose the selected images, networks, flavors, volume types, security groups, keypairs, and availability zones. Shared resources are usable only when visible to the endpoint project.

## :material-book-open-page-variant-outline: Source Disk Access

First decide whether the transfer is a migration or a repeatable replica, because their source disk-access prerequisites differ. The source boot method further limits the usable path.

| Source disk path | When it applies | Access and temporary resources |
| --- | --- | --- |
| Cinder backup through object storage | Replica of Cinder-backed disks | Requires Cinder backup access and object-storage access. |
| Ceph-backed Cinder backup or snapshot | Replica of Cinder-backed disks | Requires Cinder snapshot or backup access plus Coriolis Worker service reachability to the source Ceph cluster. |
| Temporary source worker VM | Migration path or selected replica path; required for a Glance-rooted replica source | Creates source snapshots and temporary storage resources, then uses a temporary worker VM to export disk data. |

A Glance-rooted instance has an image root disk. For a volume-backed instance, exactly one attached Cinder volume must be marked bootable for normal source inventory and export. Select the disk path before requesting permissions or connectivity.

## :material-book-open-page-variant-outline: Destination Mappings

Prepare and confirm the required destination resources, mappings, quotas, and visibility before validation.

1. Map every source network interface to a destination Neutron network. A missing mapping for any source interface prevents deployment.
2. Confirm each mapped network can support the intended ports, security groups, and IP behavior. Preserving an address requires a compatible destination subnet.
3. Select visible destination storage for every required disk where storage placement is needed.
4. Confirm any selected destination flavor, security groups, keypair, server group, or floating-IP pool already exists and is visible.

Deployment creates the destination VM. See [Migration Flow](migration-flow.md#lifecycle) for the execution boundary.

## :material-book-open-page-variant-outline: Temporary Worker VMs And Connectivity

The selected path can create temporary export, disk-copy, or operating-system-morphing worker VMs. These provider-created VMs are distinct from the Coriolis Worker service. Before starting, provide a visible temporary worker VM image, network, and flavor on each side that needs a temporary worker VM. If temporary worker VMs boot from volumes, the required volume type must also be visible.

Temporary worker VM images must initialize on first boot. Use an image with the appropriate initialization support, and use a configuration drive where cloud metadata is unavailable. Ensure security controls permit the Coriolis runtime to reach OpenStack APIs and each temporary worker VM over the required management and data paths. For Ceph-based source access, the Coriolis Worker service also needs a route to the source Ceph cluster.

## :material-book-open-page-variant-outline: Cleanup And Validation

1. Validate endpoint API access, source disk access, resource visibility, per-network mappings, and temporary worker VM initialization before a workload transfer.
2. Run a small controlled transfer, then separately deploy and verify the destination VM, disks, and networking.
3. Confirm cleanup of temporary worker VMs, ports, floating IPs, snapshots, cloned volumes, backups, and temporary images created by the selected path.
4. Do not classify the destination VM, its disks, or its intended network resources as temporary artifacts.

!!! warning
    OpenStack provider qualification and end-to-end migration validation remain pending. Verify the installed release and your cloud policies with a controlled workload before relying on this path.
