# Terminology

!!! abstract
    Definitions for Coriolis appliance deployment and provider-based migration or replication.

## :material-book-open-page-variant-outline: Virtual Appliance And Coriolis Appliance

A **virtual appliance** is a prebuilt VM containing an operating system, application, and configuration.

A **Coriolis appliance** is a VM running Coriolis and its support containers.

## :material-book-open-page-variant-outline: OVA

An **OVA** is an archive containing an OVF descriptor and virtual disks, commonly VMDK files; it is not directly executable. A checksum verifies integrity only when its source is trusted.

### :material-application-edit-outline: OVA Lifecycle

`base template -> build VM -> OVA -> verified import -> deployed appliance`

Import compatibility depends on the target hypervisor.

## :material-book-open-page-variant-outline: Terms Often Confused

| Term | Definition |
| --- | --- |
| Base appliance template | Starting VMware template for an appliance build. |
| Appliance build VM | Configured template clone before export. |
| OVA artifact | Distributable archive exported from a build VM. |
| Deployed appliance | Imported and booted appliance VM. |
| OVA import | Import of an OVA or OVF package into a supported hypervisor. |
| OpenStack import provider | Coriolis migration component, unrelated to OVA import. |
| Coriolis endpoint | Provider connection and its environment-specific configuration. |
| Source environment | Origin environment from which Coriolis reads a workload. |
| Destination environment | Target environment to which Coriolis deploys a workload. |
| Migration worker / minion | Temporary provider VM used for transfer or morphing work. |
| OSMorphing | Guest operating-system changes required for the destination platform. |
| CBT | VMware Changed Block Tracking, used to identify changed disk blocks. |
| VDDK | VMware Virtual Disk Development Kit, used for VMware virtual-disk access. |
| Migration / replica | Migration moves a workload; replica synchronizes it for later deployment. |

## :material-book-open-page-variant-outline: Related Information

[Discovery](discovery.md), [OpenStack Provider Reference](openstack-provider.md), [VMware Provider Reference](vmware-provider.md), [Appliance Runtime](appliance-runtime.md), and [Appliance Release](appliance-release-flow.md).
