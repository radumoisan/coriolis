# Coriolis Discovery

!!! abstract
    In-progress first-path evidence and unvalidated gates.

## :material-book-open-page-variant-outline: Current First Path

Published appliance on VMware; VMware source; OpenStack destination; one minimal Linux VM.

A license is required. Initial scope excludes Jenkins, source builds, and image builds.

See [Home](index.md) for the repository map and [Appliance Release](appliance-release-flow.md) for the build lifecycle.

## :material-book-open-page-variant-outline: Evidence Status

- **Observed:** 2026 appliance documentation covers OpenStack image deployment, login, and initial sizing.
- **Historical evidence:** 2019-2020 VMware and OpenStack provider documentation.
- **Source evidence:** local build and deployment code.
- **Unknown:** current RC2 VMware import compatibility and endpoint schema.

- [Deploying the Coriolis appliance image](https://cloudbasedev.atlassian.net/wiki/spaces/CDS/pages/3526787074/Deploying+the+Coriolis+appliance+image) (2026-02)
- [Coriolis Trial Appliance info](https://cloudbasedev.atlassian.net/wiki/spaces/COR/pages/595524/Coriolis+Trial+Appliance+info) (2026-04)
- [VMWare vSphere Coriolis plugin](https://cloudbasedev.atlassian.net/wiki/spaces/COR/pages/1845147/VMWare+vSphere+Coriolis+plugin) (2020)
- [OpenStack Coriolis plugin](https://cloudbasedev.atlassian.net/wiki/spaces/COR/pages/1840996/OpenStack+Coriolis+plugin) (2020)
- [Coriolis 2026 Roadmap](https://cloudbasedev.atlassian.net/wiki/spaces/CDD/pages/3454599169/Coriolis+2026+Roadmap) (2026)

## :material-book-open-page-variant-outline: Appliance Bootstrap

- **Observed:** the 2026 OpenStack image guide specifies 4 vCPU, 6144 MB RAM, and 40 GB disk; this applies to that path and is not confirmed for VMware RC2.
- **Observed:** accept the EULA before login; console option 2 shows Web UI login information.
- **Historical evidence:** console networking supports DHCP or static configuration; Web UI access uses the appliance IP over HTTPS, with ports 80/443 and a self-signed certificate described.
- **Unknown:** current RC2 console, network, TLS, and port behavior.
- **Unknown:** current VMware Deploy OVF compatibility matrix.

## :material-book-open-page-variant-outline: VMware Source Preflight

**Historical evidence:**

- vCenter/ESXi API access typically uses TCP 443; CBT candidates need TCP 902; names resolve.
- First test: minimal Linux VM with ordinary virtual disks.
- Raw and passthrough disks are unsupported for CBT.
- Relevant inventory, network, DVS, port-group, snapshot, and disk-read access is required.
- Power and change-tracking access is configuration dependent.
- Match VDDK to the ESXi version.

**Unknown:** RC2 migration mode, CBT default, permissions, and VDDK compatibility.

## :material-book-open-page-variant-outline: OpenStack Destination Preflight

Historical evidence: provider material identifies endpoint fields, API reachability/capabilities, mapped destination resources, temporary workers, and cleanup behavior; validate the RC2 UI and schema. It also states that Ceph, Swift, and Cinder Backup are not required.

- Reach Keystone, Glance, Nova, Neutron, and Cinder.
- Precreate mapped networks, security groups, final flavor, and volume types.
- Provide a temporary worker cloud-init Linux image, flavor, migration network, and routing or floating IP; use a config drive where no metadata is available.
- Permit list/create/delete operations for images, networks, security groups, flavors, keypairs, Cinder volumes, snapshots, ports, temporary VMs, and floating IPs.
- Inspect residual snapshots after cleanup.

**Unknown:** numeric quotas; plan for the final workload plus transient resources.

## :material-book-open-page-variant-outline: Appliance Publication Research Snapshot

**Observed during research; current availability is unknown.**

- Candidate: `coriolis-appliance-2608.0-rc2.ova`
- OVA: `http://10.8.1.121/appliances/coriolis-appliance-2608.0-rc2.ova`
- Sidecar: `http://10.8.1.121/appliances/coriolis-appliance-2608.0-rc2.ova.sha256sum`
- SHA-256: `33ce5b8d0ca3c35b95bd8da11842eb8193fee68706cfd182ae8a11e1831a347d`
- Size: about 9.57 GB

Final `2608.0` was absent during research; `latest` is mutable.

!!! warning
    Verify the checksum before use. Never use `latest` for a repeatable exercise.

## :material-book-open-page-variant-outline: Runtime And Build Boundaries

- **Source evidence:** deployment uses Docker and Ansible; Kolla provides support services.
- **Observed:** one snapshot has application tag `2603.4` and Kolla tag `2023.1-ubuntu-jammy`.
- **Observed:** registry `401` leaves image availability unconfirmed; digests and source provenance were not inventoried.
- **Assumption:** source builds require immutable pins; current observed inputs include mutable references.

Source build is outside the first path. See [Appliance Runtime](appliance-runtime.md).

## :material-book-open-page-variant-outline: Validation Gates

1. Verify snapshot artifact, checksum, and current availability.
2. Verify VMware import and compatibility.
3. Verify RC2 boot, console, network, TLS, and license.
4. Verify vCenter access, CBT, permissions, and VDDK.
5. Verify endpoint schema and OpenStack choices.
6. Preflight resources, quotas, and temporary-worker connectivity.
7. Run controlled minimal Linux migration; validate result and cleanup.

Build closure is separate scope.

## :material-book-open-page-variant-outline: Related Information

[Home](index.md), [Terminology](terminology.md), [Appliance Runtime](appliance-runtime.md), and [Appliance Release](appliance-release-flow.md).
