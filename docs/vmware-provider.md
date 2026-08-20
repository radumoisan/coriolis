# VMware vSphere Provider Reference

!!! abstract
    Unvalidated reference derived from local VMware provider source. The source includes export and import behavior, but historical documentation lists VMware as source-only; validate deployed appliance/runtime support before use.

## :material-book-open-page-variant-outline: Connection

The local provider platform ID is `vmware_vsphere`.

| Setting | Source-code evidence |
| --- | --- |
| Required direct fields | `host`, `username`, and `password` |
| Port | `443` by default |
| TLS behavior | Certificate validation is enabled by default; `allow_untrusted` defaults to `false` and disables it when enabled |
| Secret alternative | `secret_ref` can provide connection data |

```json
{
  "host": "<vcenter-host>",
  "username": "<username>",
  "password": "<secret-managed-value>",
  "allow_untrusted": false
}
```

!!! warning
    Do not treat this as a vCenter/ESXi compatibility or privilege matrix. Validate the installed provider and least-privilege requirements in the target environment.

## :material-book-open-page-variant-outline: VMware Source

The source uses VDDK. Its default library location is `/usr/lib/vmware-vix-disklib`; provider configuration can override that directory and set an optional VixDiskLib configuration-file path. Validate the installed provider against the environment rather than selecting a compatibility version from this reference.

```json
{
  "vixdisklib_compatibility_version": "<vddk-compatibility-version>",
  "automatically_enable_cbt": false,
  "export_hostname_as_instance_name": false,
  "verify_disk_integrity": false,
  "enable_transfer_compression": false,
  "skip_nfc_validation": false
}
```

Source options include `vixdisklib_compatibility_version`, `automatically_enable_cbt`, `export_hostname_as_instance_name`, `verify_disk_integrity`, `enable_transfer_compression`, and `skip_nfc_validation`. Dynamic option listing exposes only the compatibility setting. Do not use transfer compression for encrypted disks.

CBT uses temporary snapshots. Automatic CBT enablement fails when pre-existing snapshots prevent the required temporary snapshot. VDDK/NBDSSL is the normal disk-read path. Independent-persistent and multi-writer disks have a datastore-HTTPS fallback only while the VM is powered off. Source VMs with more than 15 disks fail destination import validation. Optional SHA-256 integrity verification and compression have performance and resource costs.

## :material-book-open-page-variant-outline: VMware Destination

The syntactic schema requires `import_datacenter`. Runtime validation also checks `import_cluster`, `import_datastore`, `migr_minion_cluster`, OS-specific `migr_template_map`, and OS-specific username/password maps. Validate these installed-provider checks against inventory paths and credentials before running a workflow.

Destination options include resource pool, folder, network and storage maps, preserve-MAC behavior, NIC model, hardware version, first-class disks, power-on, CBT, and disk controller. Relevant defaults are `genericLinuxGuest`, first-class disks enabled, import CBT disabled, power-on disabled, preserve MAC disabled, `VMXNET3`, and `SCSI`.

Migration templates require VMware Tools, IP reporting, and a SCSI controller. Minion placement can inherit from configured destination resources. Every source NIC must resolve through the destination mapping; duplicate names fail except during warning-only validation.

!!! note
    First-class-disk support is unvalidated: schema text states vSphere 6.7 while an implementation description states 6.5. Verify the installed release and target platform.

## :material-book-open-page-variant-outline: Ports And Connectivity

Source evidence identifies TCP/443 for the API, TCP/902 for NFC, and TCP/5566 for HTTPS transfer plus TCP/22 for SSH transfer. Validate these ports against the installed release and network path before configuring connectivity.

## :material-book-open-page-variant-outline: Troubleshooting

- CBT or snapshot blockers: resolve pre-existing snapshots before automatic CBT enablement and validate snapshot operations on a test VM.
- NFC failures: check DNS resolution and TCP/902 firewall reachability.
- VDDK failures: inspect provider and VDDK logs, then validate library configuration and environment compatibility.
- Concurrent reads: treat concurrency resource limits as historical supporting evidence until validated for the installed appliance.

## :material-book-open-page-variant-outline: Evidence

**Source-code evidence:** `coriolis-provider-vmware/coriolis_provider_vmware_vsphere/common.py`, `exp.py`, `imp.py`, `guestid.py`, `vixdisklib.py`, and provider schemas under `coriolis-provider-vmware/`.

**Historical supporting evidence:** [VMWare vSphere Coriolis plugin](https://cloudbasedev.atlassian.net/wiki/spaces/COR/pages/1845147/VMWare+vSphere+Coriolis+plugin) and [VMWare vSphere ESXi Common Issues](https://cloudbasedev.atlassian.net/wiki/spaces/CDS/pages/651100168/VMWare+vSphere+ESXi+Common+Issues). Historical documentation is not runtime confirmation.
