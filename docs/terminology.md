# Terminology

!!! abstract
    This page defines terms used by Coriolis appliance deployment and VMware-to-OpenStack migration documentation.

## :material-book-open-page-variant-outline: Virtual Appliance And Coriolis Appliance

**Virtual appliance** is a prebuilt virtual machine (VM) for a specific workload. It contains a guest operating system, the Coriolis application, its dependencies, and initial configuration. Coriolis supporting services run as containers inside the appliance VM.

**Coriolis appliance** can mean either the configured VM before it is exported, or the VM after an OVA is imported and deployed.

## :material-book-open-page-variant-outline: OVA

**OVA**, commonly called Open Virtual Appliance, is a single archive used to distribute a virtual appliance. It generally contains an OVF descriptor, virtual disks (often VMDK), and optional manifest, checksum, or signature files. An OVA is commonly a TAR archive of an OVF package and is not directly executable.

### :material-application-edit-outline: OVA Lifecycle

The usual lifecycle is:

1. Base VMware template
2. Configured appliance build VM
3. Exported or published OVA and checksum
4. Verified download
5. VMware OVA or OVF import
6. Booted deployed appliance

OVA import may require a supported target hypervisor and does not guarantee compatibility across hypervisors.

## :material-book-open-page-variant-outline: OVA On OpenStack

OpenStack usually does not consume an OVA directly. The documented path is to extract the OVA, obtain the VMDK, convert it to QCOW2, upload it to Glance, and create a VM. This is separate from the selected OVA-on-VMware-first path.

## :material-book-open-page-variant-outline: Terms Often Confused

| Term | Definition |
| --- | --- |
| Base appliance template | The starting VMware template used to build an appliance. |
| Appliance build VM | The configured VM created from the base template before export. |
| OVA artifact | The distributable OVA archive produced from an appliance build VM. |
| Deployed appliance | The appliance VM after import and boot on a target platform. |
| OVA import | Importing an OVA or OVF package into a supported hypervisor. |
| OpenStack import provider | A Coriolis component that migrates workloads into OpenStack; it is unrelated to OVA import. |
| Source / destination | The origin environment and target environment of a migration. |
| Migration / replica | A migration moves a workload to its destination; a replica continuously synchronizes it for disaster recovery and later deployment. |

## :material-book-open-page-variant-outline: What An OVA Is Not

An OVA is not an ISO installer, Docker image, or Coriolis source code, and it is normally not executed directly. A checksum verifies integrity only when the checksum source is trusted.

## :material-book-open-page-variant-outline: Related Information

Terminology prose supports [Discovery](discovery.md) and [Appliance Runtime](appliance-runtime.md).
