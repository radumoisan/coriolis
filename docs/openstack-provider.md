# OpenStack Context

!!! abstract
    This page covers the initial OpenStack-to-OpenStack migration path. A transfer copies or synchronizes disks; deployment is a separate step described in [Migration Flow](migration-flow.md).

1. Source preparation: project-scoped credentials, quota, disk access, and one disposable volume-backed workload.
2. Destination preparation: project-scoped credentials, quota, mapped networking, storage, and temporary-worker resources.
3. Validation: both endpoint projects can see and use required resources, followed by migration and cleanup verification.

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

Use administrator credentials only for this one-time setup. Each cloud receives a separate `coriolis` user and project for migration; although the projects share a name, they are independent.

!!! warning
    These commands create identity state and replace project quotas. Do not rerun them blindly against existing resources.

Select secure local files for endpoint credentials, passwords, and the worker private key, then set reusable path variables.

<!-- Define local credential, password, and private-key paths. -->
```bash
# Define local credential, password, and private-key paths.
export SOURCE_ADMIN_OPENRC=/path/to/source-admin-openrc.sh \
  DESTINATION_ADMIN_OPENRC=/path/to/destination-admin-openrc.sh \
  SOURCE_CORIOLIS_OPENRC=/path/to/source-coriolis-openrc.sh \
  DESTINATION_CORIOLIS_OPENRC=/path/to/destination-coriolis-openrc.sh \
  CORIOLIS_PASSWORD_ENV=/path/to/coriolis-passwords.env \
  CORIOLIS_WORKER_PRIVATE_KEY=/path/to/coriolis-worker-key.pem
```

??? example "Expected result"

    ```text
    No output.
    ```

The password environment file must define `SOURCE_CORIOLIS_PASSWORD` and `DESTINATION_CORIOLIS_PASSWORD`. It must not be committed, and secrets must not be placed in documentation or shell history.

<!-- Load the local Coriolis project passwords. -->
```bash
# Load the local Coriolis project passwords.
source "$CORIOLIS_PASSWORD_ENV"
```

??? example "Expected result"

    ```text
    No output.
    ```

## :material-book-open-page-variant-outline: Source Preparation

### :material-application-edit-outline: Source Project

<!-- Load source-cloud administrator credentials. -->
```bash
# Load source-cloud administrator credentials.
source "$SOURCE_ADMIN_OPENRC"
```

??? example "Expected result"

    ```text
    No output.
    ```

<!-- Create the source Coriolis project and print its ID. -->
```bash
# Create the source Coriolis project and print its ID.
openstack project create --domain Default --description "Coriolis migration demo source project" -f value -c id coriolis
```

??? example "Expected result"

    ```text
    be3c7405df8149bc84e65217576c1dd4
    ```

<!-- Create the source Coriolis user and print its ID. -->
```bash
# Create the source Coriolis user and print its ID.
openstack user create --domain Default --project coriolis --project-domain Default --password "$SOURCE_CORIOLIS_PASSWORD" -f value -c id coriolis
```

??? example "Expected result"

    ```text
    340ad8ce46ea42f381fcdcf135c4baaf
    ```

<!-- Grant the source Coriolis user the member role in its project. -->
```bash
# Grant the source Coriolis user the member role in its project.
openstack role add --project coriolis --project-domain Default --user coriolis --user-domain Default member
```

??? example "Expected result"

    ```text
    No output.
    ```

<!-- Allow the source administrator to select the Coriolis project in Horizon. -->
```bash
# Allow the source administrator to select the Coriolis project in Horizon.
openstack role add --project coriolis --project-domain Default --user admin --user-domain Default member
```

??? example "Expected result"

    ```text
    No output.
    ```

<!-- Set the source Coriolis project quota. -->
```bash
# Set the source Coriolis project quota.
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

### :material-application-edit-outline: Source Disk Access

- **Glance-rooted instance:** The operating system disk is created from a Glance image and normally resides on Nova-managed ephemeral storage.
- **Volume-backed instance:** The operating system resides on an attached Cinder volume. Coriolis expects exactly one attached volume marked `bootable` so it can identify the source operating-system disk. No bootable volume, or multiple bootable volumes, makes the root disk ambiguous.
- **Select the disk path:** Decide how Coriolis will access and transfer that disk, such as Cinder backup through Swift, Ceph access, or a temporary worker VM. This choice determines the required OpenStack permissions and network connectivity.

!!! note "Demo disk path"
    This demo uses a small, disposable, volume-backed source VM with exactly one attached bootable Cinder volume. Coriolis exports it with `swift_backups`, so the source project requires both Cinder backup and Swift access.

    This path does not require a floating IP or SSH access to the source VM. The destination uses a temporary worker VM and places the cloned disk on the `__DEFAULT__` volume type. The tutorial shuts down the source after the transfer and automatically deploys the destination VM.

### :material-application-edit-outline: Source Fixture

!!! warning
    The following commands create stateful resources. Record the returned IDs and do not rerun creation commands blindly against existing resources.

The source fixture is volume-backed and uses a config drive for cloud-init. It has no router or floating IP because the `swift_backups` export path needs Cinder and Swift APIs, not SSH access to the source guest.

[Download `coriolis-source-cloud-init.yaml`](assets/manifests/coriolis-source-cloud-init.yaml){ download="coriolis-source-cloud-init.yaml" }

??? quote "coriolis-source-cloud-init.yaml"

    ```yaml
    --8<-- "assets/manifests/coriolis-source-cloud-init.yaml"
    ```

<!-- Load the local Coriolis project passwords. -->
```bash
# Load the local Coriolis project passwords.
source "$CORIOLIS_PASSWORD_ENV"
```

??? example "Expected result"

    ```text
    No output.
    ```

<!-- Load source-project credentials. -->
```bash
# Load source-project credentials.
source "$SOURCE_CORIOLIS_OPENRC"
```

??? example "Expected result"

    ```text
    No output.
    ```

<!-- Create the isolated source network in project be3c7405df8149bc84e65217576c1dd4. -->
```bash
# Create the isolated source network in project be3c7405df8149bc84e65217576c1dd4.
openstack network create -f value -c id coriolis-source-net
```

??? example "Expected result"

    ```text
    3297153b-5c2b-44fc-8f0f-02fc0b92db73
    ```

<!-- Create the DHCP-enabled source subnet. -->
```bash
# Create the DHCP-enabled source subnet.
openstack subnet create --network 3297153b-5c2b-44fc-8f0f-02fc0b92db73 --subnet-range 192.168.240.0/24 --gateway 192.168.240.1 -f value -c id coriolis-source-subnet
```

??? example "Expected result"

    ```text
    89ec32a8-93de-4b90-af24-55cf39e2882b
    ```

<!-- Create the 8 GiB bootable source volume from the validated Ubuntu image. -->
```bash
# Create the 8 GiB bootable source volume from the validated Ubuntu image.
openstack volume create --bootable --size 8 --type __DEFAULT__ --image 82e26d47-c55e-4839-81aa-5b59dd8021c6 -f value -c id coriolis-source-boot
```

??? example "Expected result"

    ```text
    596f5c90-13bf-4773-97ec-33384873e94e
    ```

Wait for the volume to become `available`. Re-run this check until it reports `available` before creating the server.

<!-- Check that the source volume is ready to attach. -->
```bash
# Check that the source volume is ready to attach.
openstack volume show 596f5c90-13bf-4773-97ec-33384873e94e -f value -c status
```

??? example "Expected result"

    ```text
    available
    ```

<!-- Boot the source VM with its only volume, config drive, and the fixture cloud-init. -->
```bash
# Boot the source VM with its only volume, config drive, and the fixture cloud-init.
openstack server create --flavor c1.small --volume 596f5c90-13bf-4773-97ec-33384873e94e --nic net-id=3297153b-5c2b-44fc-8f0f-02fc0b92db73 --security-group default --config-drive true --user-data coriolis-source-cloud-init.yaml --wait -f value -c id coriolis-source-vm
```

??? example "Expected result"

    ```text
    deb91e29-7901-466c-b799-90d439145ab6
    ```

<!-- Verify the source volume properties; attachment is verified by the server query. -->
```bash
# Verify the source volume properties; attachment is verified by the server query.
openstack volume show 596f5c90-13bf-4773-97ec-33384873e94e -f yaml -c size -c type -c bootable -c status
```

??? example "Expected result"

    ```yaml
    bootable: true
    size: 8
    status: in-use
    type: __DEFAULT__
    ```

<!-- Verify the source server is active with config drive and one attached boot volume. -->
```bash
# Verify the source server is active with config drive and one attached boot volume.
openstack server show deb91e29-7901-466c-b799-90d439145ab6 -f yaml -c status -c addresses -c security_groups -c config_drive -c volumes_attached
```

??? example "Expected result"

    ```yaml
    addresses:
      coriolis-source-net:
      - 192.168.240.196
    config_drive: 'True'
    security_groups:
    - name: default
    status: ACTIVE
    volumes_attached:
    - delete_on_termination: false
      id: 596f5c90-13bf-4773-97ec-33384873e94e
    ```

<!-- Verify the cloud-init marker through the Nova serial console. -->
```bash
# Verify the cloud-init marker through the Nova serial console.
openstack console log show deb91e29-7901-466c-b799-90d439145ab6 | grep CORIOLIS_SOURCE_MARKER
```

??? example "Expected result"

    ```text
    CORIOLIS_SOURCE_MARKER=coriolis-source-fixture
    ```

## :material-book-open-page-variant-outline: Destination Preparation

### :material-application-edit-outline: Destination Project

<!-- Load destination-cloud administrator credentials. -->
```bash
# Load destination-cloud administrator credentials.
source "$DESTINATION_ADMIN_OPENRC"
```

??? example "Expected result"

    ```text
    No output.
    ```

<!-- Create the destination Coriolis project and print its ID. -->
```bash
# Create the destination Coriolis project and print its ID.
openstack project create --domain Default --description "Coriolis migration demo destination project" -f value -c id coriolis
```

??? example "Expected result"

    ```text
    6686f045c51b4f1da7b9742dbe9622cd
    ```

<!-- Create the destination Coriolis user and print its ID. -->
```bash
# Create the destination Coriolis user and print its ID.
openstack user create --domain Default --project coriolis --project-domain Default --password "$DESTINATION_CORIOLIS_PASSWORD" -f value -c id coriolis
```

??? example "Expected result"

    ```text
    1cd2b476c942495fb7ae03e0412cdc90
    ```

<!-- Grant the destination Coriolis user the member role in its project. -->
```bash
# Grant the destination Coriolis user the member role in its project.
openstack role add --project coriolis --project-domain Default --user coriolis --user-domain Default member
```

??? example "Expected result"

    ```text
    No output.
    ```

<!-- Allow the destination administrator to select the Coriolis project in Horizon. -->
```bash
# Allow the destination administrator to select the Coriolis project in Horizon.
openstack role add --project coriolis --project-domain Default --user admin --user-domain Default member
```

??? example "Expected result"

    ```text
    No output.
    ```

<!-- Set the destination Coriolis project quota. -->
```bash
# Set the destination Coriolis project quota.
openstack quota set \
  --instances 2 --cores 4 --ram 8192 --key-pairs 2 \
  --server-groups 0 --server-group-members 0 \
  --volumes 2 --gigabytes 40 --per-volume-gigabytes 20 --snapshots 1 \
  --backups 0 --backup-gigabytes 0 \
  --networks 1 --subnets 1 --ports 6 --routers 1 --floating-ips 2 \
  --secgroups 3 --secgroup-rules 20 coriolis
```

??? example "Expected result"

    ```text
    No output.
    ```

The destination quota reserves the project's `default`, the fixture `coriolis-worker-sg` assigned to the migrated VM, and Coriolis's temporary worker-specific group.

The `admin` membership makes the project available in Horizon's project selector. Continue to use the dedicated `coriolis` user, not `admin`, for Coriolis endpoints.

### :material-application-edit-outline: Destination Worker Flavor

Public flavors have a zero root disk, and destination Nova policy does not permit the endpoint user to direct-image-boot them. The private project-scoped `coriolis-worker` flavor provides an 8 GiB root disk for temporary workers.

<!-- Create the private destination worker flavor and print its ID. -->
```bash
# Create the private destination worker flavor and print its ID.
openstack flavor create coriolis-worker --private \
  --project 6686f045c51b4f1da7b9742dbe9622cd \
  --vcpus 2 --ram 4096 --disk 8 --ephemeral 0 --swap 0 \
  --property architecture=x86_64 -f value -c id
```

??? example "Expected result"

    ```text
    6d8ebcdc-6dc7-41c0-a4d5-943aea3d0c3e
    ```

<!-- Verify the private worker flavor and its project access. -->
```bash
# Verify the private worker flavor and its project access.
openstack flavor show 6d8ebcdc-6dc7-41c0-a4d5-943aea3d0c3e -f yaml \
  -c id -c name -c ram -c vcpus -c disk -c properties \
  -c os-flavor-access:is_public -c access_project_ids
```

??? example "Expected result"

    ```yaml
    access_project_ids:
    - 6686f045c51b4f1da7b9742dbe9622cd
    disk: 8
    id: 6d8ebcdc-6dc7-41c0-a4d5-943aea3d0c3e
    name: coriolis-worker
    os-flavor-access:is_public: false
    properties:
      architecture: x86_64
    ram: 4096
    vcpus: 2
    ```

### :material-application-edit-outline: Destination Resources

The destination project provisions worker connectivity separately from the source fixture. Recheck the allowed SSH source `89.34.101.238/32` if the runtime egress address changes.

<!-- Load the local Coriolis project passwords. -->
```bash
# Load the local Coriolis project passwords.
source "$CORIOLIS_PASSWORD_ENV"
```

??? example "Expected result"

    ```text
    No output.
    ```

<!-- Load destination-project credentials. -->
```bash
# Load destination-project credentials.
source "$DESTINATION_CORIOLIS_OPENRC"
```

??? example "Expected result"

    ```text
    No output.
    ```

<!-- Create the isolated destination network in project 6686f045c51b4f1da7b9742dbe9622cd. -->
```bash
# Create the isolated destination network in project 6686f045c51b4f1da7b9742dbe9622cd.
openstack network create -f value -c id coriolis-destination-net
```

??? example "Expected result"

    ```text
    8f3f9804-e2f0-48ec-a9a9-d78a98234a69
    ```

<!-- Create the DHCP-enabled destination subnet with its resolver. -->
```bash
# Create the DHCP-enabled destination subnet with its resolver.
openstack subnet create --network 8f3f9804-e2f0-48ec-a9a9-d78a98234a69 --subnet-range 192.168.241.0/24 --gateway 192.168.241.1 --dns-nameserver 1.1.1.1 -f value -c id coriolis-destination-subnet
```

??? example "Expected result"

    ```text
    b8b4dc44-9b53-444a-8b9e-281e6ec29351
    ```

<!-- Create the destination router. -->
```bash
# Create the destination router.
openstack router create -f value -c id coriolis-destination-router
```

??? example "Expected result"

    ```text
    dac8f647-763d-4c31-be0c-fadea00e469c
    ```

<!-- Attach the router to the ext_net_gts external network. -->
```bash
# Attach the router to the ext_net_gts external network.
openstack router set --external-gateway c5815350-3a4c-4a6a-a567-db9f0d6e5a19 --fixed-ip subnet=08e4c993-ad01-49fe-ada4-050f7339984c dac8f647-763d-4c31-be0c-fadea00e469c
```

??? example "Expected result"

    ```text
    No output.
    ```

<!-- Attach the destination subnet to the router. -->
```bash
# Attach the destination subnet to the router.
openstack router add subnet dac8f647-763d-4c31-be0c-fadea00e469c b8b4dc44-9b53-444a-8b9e-281e6ec29351
```

??? example "Expected result"

    ```text
    No output.
    ```

<!-- Create the security group for destination worker SSH. -->
```bash
# Create the security group for destination worker SSH.
openstack security group create -f value -c id coriolis-worker-sg
```

??? example "Expected result"

    ```text
    5f10c045-785c-4003-93a9-4b3527787da9
    ```

<!-- Permit SSH only from the current Coriolis runtime egress address. -->
```bash
# Permit SSH only from the current Coriolis runtime egress address.
openstack security group rule create --ingress --ethertype IPv4 --protocol tcp --dst-port 22:22 --remote-ip 89.34.101.238/32 -f value -c id 5f10c045-785c-4003-93a9-4b3527787da9
```

??? example "Expected result"

    ```text
    1bbc103d-f302-4d0b-8710-fe42b7b057cd
    ```

<!-- Create the worker keypair without printing its private key. -->
```bash
# Create the worker keypair without printing its private key.
openstack keypair create --private-key "$CORIOLIS_WORKER_PRIVATE_KEY" -f value -c fingerprint coriolis-worker-key
```

??? example "Expected result"

    ```text
    66:12:9c:d6:3c:bd:c3:60:2e:60:dc:16:ad:ca:06:35
    ```

<!-- Restrict the generated private-key file to its owner. -->
```bash
# Restrict the generated private-key file to its owner.
chmod 0600 "$CORIOLIS_WORKER_PRIVATE_KEY"
```

??? example "Expected result"

    ```text
    No output.
    ```

<!-- Load destination-cloud administrator credentials for the scoped external-network policy. -->
```bash
# Load destination-cloud administrator credentials for the scoped external-network policy.
source "$DESTINATION_ADMIN_OPENRC"
```

??? example "Expected result"

    ```text
    No output.
    ```

<!-- Share only ext_net_gts with the destination Coriolis project. -->
```bash
# Share only ext_net_gts with the destination Coriolis project.
openstack network rbac create --type network --action access_as_shared --target-project 6686f045c51b4f1da7b9742dbe9622cd -f value -c id c5815350-3a4c-4a6a-a567-db9f0d6e5a19
```

??? example "Expected result"

    ```text
    955f7fe7-596c-4aff-98fb-14877d442fb6
    ```

Never make the external network globally shared. This RBAC policy grants `access_as_shared` only to project `6686f045c51b4f1da7b9742dbe9622cd`.

### :material-application-edit-outline: Destination Mappings

Prepare and confirm the required destination resources, mappings, quotas, and visibility before validation.

1. Map every source network interface to a destination Neutron network. A missing mapping for any source interface prevents deployment.
2. Confirm each mapped network can support the intended ports, security groups, and IP behavior. Preserving an address requires a compatible destination subnet.
3. Select visible destination storage for every required disk where storage placement is needed.
4. Confirm any selected destination flavor, security groups, keypair, server group, or floating-IP pool already exists and is visible.

Deployment creates the destination VM. See [Migration Flow](migration-flow.md#lifecycle) for the execution boundary.

### :material-application-edit-outline: Temporary Worker VMs And Connectivity

The selected path can create temporary export, disk-copy, or operating-system-morphing worker VMs. These provider-created VMs are distinct from the Coriolis Worker service. Before starting, provide a visible temporary worker VM image, network, and flavor on each side that needs a temporary worker VM. If temporary worker VMs boot from volumes, the required volume type must also be visible.

Temporary worker VM images must initialize on first boot. Use an image with the appropriate initialization support, and use a configuration drive where cloud metadata is unavailable. Ensure security controls permit the Coriolis runtime to reach OpenStack APIs and each temporary worker VM over the required management and data paths. For Ceph-based source access, the Coriolis Worker service also needs a route to the source Ceph cluster.

## :material-book-open-page-variant-outline: Validated Environment

### :material-application-edit-outline: Connection Values

| Parameter | Value (source) | Value (destination) |
| --- | --- | --- |
| Authentication URL | `https://keystone.virtomat.dev/v3` | `https://devopscentral.cloud:5000` |
| Username | `coriolis` | `coriolis` |
| Project | `coriolis` | `coriolis` |
| User domain | `Default` | `Default` |
| Project domain | `Default` | `Default` |
| Region | `RegionOne` | `RegionOne` |
| Interface | `public` | `public` |
| Identity API version | `3` | `3` |
| Glance API version | `2` | `2` |

Both projects can see the public `c1.small` flavor, public `ubuntu-24.04` image, and `__DEFAULT__` volume type. The destination `coriolis` endpoint user can also resolve the private `coriolis-worker` flavor (`6d8ebcdc-6dc7-41c0-a4d5-943aea3d0c3e`) for direct image boot.

!!! warning
    Unified project quotas cap Nova, Neutron, and Cinder resources but do not enforce a Swift byte quota in this environment. Use the demo project only for migration-related object storage and monitor its usage separately.

### :material-application-edit-outline: Provisioned Resources

| Resource | Validated value |
| --- | --- |
| Source project | `be3c7405df8149bc84e65217576c1dd4`; `coriolis-source-net` (`3297153b-5c2b-44fc-8f0f-02fc0b92db73`), `coriolis-source-subnet` (`89ec32a8-93de-4b90-af24-55cf39e2882b`), `192.168.240.0/24`, gateway `192.168.240.1`, DHCP; image `ubuntu-24.04` (`82e26d47-c55e-4839-81aa-5b59dd8021c6`). |
| Source workload | `coriolis-source-boot` (`596f5c90-13bf-4773-97ec-33384873e94e`), 8 GiB, `__DEFAULT__`, bootable at `/dev/vda`; `coriolis-source-vm` (`deb91e29-7901-466c-b799-90d439145ab6`), `ACTIVE`, `c1.small`, `192.168.240.196`, default security group, config drive, one volume; marker `CORIOLIS_SOURCE_MARKER=coriolis-source-fixture`; no router or floating IP. |
| Destination project | `6686f045c51b4f1da7b9742dbe9622cd`; `coriolis-destination-net` (`8f3f9804-e2f0-48ec-a9a9-d78a98234a69`), `coriolis-destination-subnet` (`b8b4dc44-9b53-444a-8b9e-281e6ec29351`), `192.168.241.0/24`, gateway `192.168.241.1`, DHCP, DNS `1.1.1.1`. |
| Destination access | Router `coriolis-destination-router` (`dac8f647-763d-4c31-be0c-fadea00e469c`) uses external network `ext_net_gts` (`c5815350-3a4c-4a6a-a567-db9f0d6e5a19`) and external subnet `08e4c993-ad01-49fe-ada4-050f7339984c`; floating-IP payload `c5815350-3a4c-4a6a-a567-db9f0d6e5a19/08e4c993-ad01-49fe-ada4-050f7339984c`. |
| Destination worker | `coriolis-worker-sg` (`5f10c045-785c-4003-93a9-4b3527787da9`) with TCP/22 rule `1bbc103d-f302-4d0b-8710-fe42b7b057cd` from `89.34.101.238/32`; `coriolis-worker-key` fingerprint `66:12:9c:d6:3c:bd:c3:60:2e:60:dc:16:ad:ca:06:35`, private key `$CORIOLIS_WORKER_PRIVATE_KEY` mode `0600`; destination image `b480e10c-edc9-400a-8b70-49883cb68392`; private flavor `coriolis-worker` (`6d8ebcdc-6dc7-41c0-a4d5-943aea3d0c3e`), 2 vCPUs, 4096 MiB RAM, 8 GiB root disk, `architecture=x86_64`, for direct image boot. |
| Scoped sharing | RBAC policy `955f7fe7-596c-4aff-98fb-14877d442fb6`, `access_as_shared`, network `c5815350-3a4c-4a6a-a567-db9f0d6e5a19`, target project `6686f045c51b4f1da7b9742dbe9622cd`. |

These validated values feed the [headless configuration](assets/manifests/headless-migration.yaml), including source and destination resource mappings.

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
