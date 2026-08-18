# Terminology

!!! abstract
    Definitions for Coriolis appliance deployment and VMware-to-OpenStack migration.

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
| Source / destination | Migration origin and target environments. |
| Migration / replica | Migration moves a workload; replica synchronizes it for later deployment. |

## :material-book-open-page-variant-outline: Related Information

[Discovery](discovery.md), [Appliance Runtime](appliance-runtime.md), and [Appliance Release](appliance-release-flow.md).
