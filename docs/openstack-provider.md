# OpenStack Provider Reference

!!! abstract
    Unvalidated reference derived from local OpenStack provider source. It covers OpenStack source and destination workflows for migrations and replicas; validate appliance runtime behavior before use.

## :material-book-open-page-variant-outline: Connection

The local provider platform ID is `openstack`.

| Setting | Source-code evidence |
| --- | --- |
| Required direct fields | `identity_api_version` (`2` or `3`), `username`, `password`, `project_name`, and `auth_url` |
| Optional identity scope | User and project domain name or ID |
| Image service | Glance API version `1` or `2` |
| Endpoint selection | Global or per-service region and interface |
| TLS behavior | `allow_untrusted` and `allow_untrusted_swift` |
| Secret alternative | `secret_ref` instead of direct connection values; its semantics depend on installed appliance support |

```json
{
  "identity_api_version": 3,
  "auth_url": "https://<identity-host>/v3",
  "username": "<username>",
  "password": "<secret-managed-value>",
  "project_name": "<project-name>",
  "region_name": "<region>"
}
```

!!! warning
    Validate the installed release before relying on schema defaults. Local code and schema text differ for the Glance API and Swift TLS verification defaults.

## :material-book-open-page-variant-outline: OpenStack Source

The export provider supports migration and replica workflows. Replica export mechanisms have distinct constraints:

| Mechanism | Source-code evidence |
| --- | --- |
| `swift_backups` | Requires Cinder-backed volumes and uses Cinder backups stored in Swift. |
| `ceph_backups` | Requires Cinder-backed volumes and Ceph access. |
| `ceph_snapshots` | Requires Cinder-backed volumes and Ceph access. |
| `coriolis_backups` | The only mechanism for Glance-booted instances; uses temporary source export workers. |

Ceph mechanisms require RADOS connectivity from Coriolis and appropriate read access. Confirm the needed access in the target cloud rather than treating this reference as an exhaustive permission list.

Coriolis export workers require pre-existing image, network, and flavor resources. Config drive, floating IP, boot-from-volume behavior, volume type, and volume size are optional worker settings.

```json
{
  "replica_export_mechanism": "<replica-export-mechanism>",
  "export_image": "<export-image>",
  "export_network": "<export-network>",
  "export_flavor_name": "<export-flavor-name>"
}
```

## :material-book-open-page-variant-outline: OpenStack Destination

`network_map`, `migr_network`, and `migr_flavor_name` are required. `migr_network` and `migr_flavor_name` configure temporary migration workers.

```json
{
  "network_map": {
    "<source-network>": "<destination-network>"
  },
   "migr_network": "<worker-network>",
   "migr_flavor_name": "<worker-flavor>",
   "migr_image_map": {
    "linux": "<linux-worker-image>",
    "windows": "<windows-worker-image>"
   }
 }
```

Optional destination settings cover storage and security groups; final flavor, keypair, server group, fixed or floating IP, availability zone, config drive, disk bus, and machine type. The final flavor may be omitted for automatic minimum-viable selection.

Port policies are `keep_mac`, `reuse_ports`, and `replace_mac`. A fixed IP needs a suitable subnet and CIDR. Security groups cannot be requested on a network with port security disabled. Final-instance tags allow at most 50 entries; each is at most 60 characters and cannot contain `/` or `,`.

## :material-book-open-page-variant-outline: Workers And Minions

Worker images must already exist and use cloud-init or Cloudbase-init as appropriate. The worker network must be project-visible, shared, or external, and it must be routable when no floating IP is used. Requested volume types must exist, and volume size must be positive.

The provider also exposes source and destination minion-pool support. Validate pool schema and appliance UI support against the installed release before relying on it for a migration or replica.

## :material-book-open-page-variant-outline: Validation And Cleanup

1. Validate credentials, service reachability, resource visibility, mappings, and temporary-worker connectivity in the installed appliance.
2. Run a controlled minimal workload and validate the deployed guest, disks, and networking.
3. Confirm removal of temporary source export artifacts, including artifacts created by the selected export mechanism.
4. Confirm cleanup of destination workers and their temporary ports, floating IPs, images, volumes, snapshots, and related resources without treating final workload resources as temporary.

!!! warning
    Local implementation uses HTTPS transfer TCP/5566, while current target schema text describes TCP/4433. Do not open a port from this reference until verifying the installed provider release.

## :material-book-open-page-variant-outline: Evidence

**Source-code evidence:** `coriolis-provider-openstack/coriolis_provider_openstack/common.py`, `exp.py`, `imp.py`, `replica_syncers.py`, and the provider schemas under `coriolis-provider-openstack/`.

**Historical supporting evidence:** [OpenStack Coriolis plugin](https://cloudbasedev.atlassian.net/wiki/spaces/COR/pages/1840996/OpenStack+Coriolis+plugin). Historical documentation is not runtime confirmation.
