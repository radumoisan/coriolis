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

## :material-book-open-page-variant-outline: Demo Project Provisioning

Use administrator credentials only for this one-time setup. Each cloud receives a separate `coriolis` user and project for migration; although the projects share a name, they are independent.

!!! warning
    These commands create identity state and replace project quotas. Do not rerun them blindly against existing resources.

The ignored `.openstack/coriolis-passwords.env` file contains `SOURCE_CORIOLIS_PASSWORD` and `DESTINATION_CORIOLIS_PASSWORD`. Do not place password values in documentation or shell history.

<!-- Load the local Coriolis project passwords. -->
```bash
source .openstack/coriolis-passwords.env
```

??? example "Expected result"

    ```text
    No output.
    ```

### :material-application-edit-outline: Source Cloud

<!-- Load source-cloud administrator credentials. -->
```bash
source .openstack/admin-openrc-source.sh
```

??? example "Expected result"

    ```text
    No output.
    ```

<!-- Create the source Coriolis project and print its ID. -->
```bash
openstack project create --domain Default --description "Coriolis migration demo source project" -f value -c id coriolis
```

??? example "Expected result"

    ```text
    be3c7405df8149bc84e65217576c1dd4
    ```

<!-- Create the source Coriolis user and print its ID. -->
```bash
openstack user create --domain Default --project coriolis --project-domain Default --password "$SOURCE_CORIOLIS_PASSWORD" -f value -c id coriolis
```

??? example "Expected result"

    ```text
    340ad8ce46ea42f381fcdcf135c4baaf
    ```

<!-- Grant the source Coriolis user the member role in its project. -->
```bash
openstack role add --project coriolis --project-domain Default --user coriolis --user-domain Default member
```

??? example "Expected result"

    ```text
    No output.
    ```

<!-- Allow the source administrator to select the Coriolis project in Horizon. -->
```bash
openstack role add --project coriolis --project-domain Default --user admin --user-domain Default member
```

??? example "Expected result"

    ```text
    No output.
    ```

<!-- Set the source Coriolis project quota. -->
```bash
openstack quota set \
  --instances 1 --cores 2 --ram 4096 --key-pairs 1 \
  --server-groups 0 --server-group-members 0 \
  --volumes 1 --gigabytes 20 --per-volume-gigabytes 20 --snapshots 1 \
  --backups 1 --backup-gigabytes 20 \
  --networks 1 --subnets 1 --ports 5 --routers 1 --floating-ips 0 \
  --secgroups 1 --secgroup-rules 10 coriolis
```

??? example "Expected result"

    ```text
    No output.
    ```

### :material-application-edit-outline: Destination Cloud

<!-- Load destination-cloud administrator credentials. -->
```bash
source .openstack/admin-openrc-dest.sh
```

??? example "Expected result"

    ```text
    No output.
    ```

<!-- Create the destination Coriolis project and print its ID. -->
```bash
openstack project create --domain Default --description "Coriolis migration demo destination project" -f value -c id coriolis
```

??? example "Expected result"

    ```text
    6686f045c51b4f1da7b9742dbe9622cd
    ```

<!-- Create the destination Coriolis user and print its ID. -->
```bash
openstack user create --domain Default --project coriolis --project-domain Default --password "$DESTINATION_CORIOLIS_PASSWORD" -f value -c id coriolis
```

??? example "Expected result"

    ```text
    1cd2b476c942495fb7ae03e0412cdc90
    ```

<!-- Grant the destination Coriolis user the member role in its project. -->
```bash
openstack role add --project coriolis --project-domain Default --user coriolis --user-domain Default member
```

??? example "Expected result"

    ```text
    No output.
    ```

<!-- Allow the destination administrator to select the Coriolis project in Horizon. -->
```bash
openstack role add --project coriolis --project-domain Default --user admin --user-domain Default member
```

??? example "Expected result"

    ```text
    No output.
    ```

<!-- Set the destination Coriolis project quota. -->
```bash
openstack quota set \
  --instances 2 --cores 4 --ram 8192 --key-pairs 2 \
  --server-groups 0 --server-group-members 0 \
  --volumes 2 --gigabytes 40 --per-volume-gigabytes 20 --snapshots 1 \
  --backups 0 --backup-gigabytes 0 \
  --networks 1 --subnets 1 --ports 6 --routers 1 --floating-ips 2 \
  --secgroups 2 --secgroup-rules 20 coriolis
```

??? example "Expected result"

    ```text
    No output.
    ```

The `admin` membership makes the project available in Horizon's project selector. Continue to use the dedicated `coriolis` user, not `admin`, for Coriolis endpoints.

Use these validated connection values: source auth URL `https://keystone.virtomat.dev/v3`; destination auth URL `https://devopscentral.cloud:5000`; username and project `coriolis`; user and project domains `Default`; region `RegionOne`; interface `public`; Identity API version `3`; and Glance API version `2`. Both projects can see the public `c1.small` flavor, public `ubuntu-24.04` image, and `__DEFAULT__` volume type.

!!! warning
    Unified project quotas cap Nova, Neutron, and Cinder, not Swift bytes. The safely verified source RGW account is `AUTH_be3c7405df8149bc84e65217576c1dd4` and currently has no byte quota. A reseller-admin request with the explicit target path resolved to the admin account, so no byte quota was applied; do not use this project for unrelated object storage.

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

## :material-book-open-page-variant-outline: OpenStack Migration Prerequisites

!!! danger "Migrations write real state and can shut down the source"
    The Quick Start migration operates on real OpenStack clouds. A transfer execution copies disk data, creates destination resources, and the selected execution options power the source VM off. Prepare only a small, disposable, volume-backed fixture you own and can destroy.

This checklist is the concrete preflight for the Quick Start's single OpenStack-to-OpenStack live migration of one disposable VM. The provider contract and stage boundaries live in [Migration Flow](migration-flow.md).

- **Source fixture:** Use one small, disposable, volume-backed source VM with a known marker on its boot volume. It must be `ACTIVE`, have exactly one attached bootable `in-use` volume, and have its marker verified in the guest or through serial-console/cloud-init evidence.
- **Source data path:** The source endpoint project needs Cinder backups and Swift APIs for `swift_backups`; API discovery alone is not proof. Fixture task progress must demonstrate successful Cinder-backup/Swift replication.
- **Destination capacity:** Ensure quota headroom for volumes, snapshots, ports, floating IPs, fixture disks, and one temporary worker VM plus its port.
- **Worker resources:** The endpoint project needs a visible Linux image that boots and initializes, worker network, flavor, security group permitting required API and data paths, keypair, free floating IPs, and a worker volume type when applicable; otherwise `__DEFAULT__` is acceptable.
- **Network mappings:** Map every source NIC/network to a destination network ID before deployment.
- **Endpoint access:** The appliance must reach both clouds' identity and service endpoints, and `Validate and save` must succeed. Project-scoped endpoint credentials, not an administrator account, must see every listed image, network, flavor, security group, keypair, floating-IP pool, and volume type.

!!! note "Source Floating IPs Are Not Required By `swift_backups`"
    Coriolis requests source Cinder backups and reads the staged data through Swift APIs; this path does not require SSH into the source VM. Verify the source marker through a guest read or a serial-console check without borrowing an unrelated floating IP. The destination pool still needs free addresses for temporary workers and the migrated guest. Quota headroom alone does not prove that its external subnet allocation pool has free addresses.

## :material-book-open-page-variant-outline: Cleanup And Validation

1. Validate endpoint API access, source disk access, resource visibility, per-network mappings, and temporary worker VM initialization before a workload transfer.
2. Run a small controlled transfer, then separately deploy and verify the destination VM, disks, and networking.
3. Confirm cleanup of temporary worker VMs, ports, floating IPs, snapshots, cloned volumes, backups, and temporary images created by the selected path.
4. Do not classify the destination VM, its disks, or its intended network resources as temporary artifacts.

!!! warning
    One bounded development Web UI OpenStack-to-OpenStack migration proof of concept has passed on released operator 0.5.54, and the walkthrough, including one [headless migration](headless-migration.md) and one [Web UI migration](web-ui-migration.md), has been followed end to end on operator 0.5.59 with runtime 2603.4. See [validation history](technical-debt.md#validation-history) for the bounded scope. Broader provider qualification and all production-readiness claims remain unvalidated. Verify the installed release and your cloud policies with a controlled workload before relying on this path.
