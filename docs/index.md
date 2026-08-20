# Coriolis

!!! abstract
    Coriolis migrates workloads. Its repositories separate product source, appliance assembly, delivery, and CI.

## :material-book-open-page-variant-outline: How The Repositories Work Together

Repository relationship summary, not a dependency graph.

```text
Build and delivery flow
Coriolis source -> packaging/deployment -> appliance lifecycle -> CI validation
```

## :material-book-open-page-variant-outline: Repository Roles

### :material-application-edit-outline: `coriolis-oss`

Product source for Coriolis APIs, workflows, workers, schedulers, and provider integrations.

### :material-application-edit-outline: `coriolis-docker`

Docker and Ansible packaging and deployment for Coriolis and selected support services.

### :material-application-edit-outline: `coriolis-cd`

Appliance lifecycle tooling for build VMs, deployment, export, import, and testing.

### :material-application-edit-outline: `coriolis-ci`

Jenkins automation for appliance setup and migration validation.

### :material-application-edit-outline: `coriolis-provider-openstack`

OpenStack provider implementation for Coriolis source and destination workflows.

### :material-application-edit-outline: `coriolis-provider-vmware`

VMware vSphere provider implementation for Coriolis source and destination workflows.

## :material-book-open-page-variant-outline: Kubernetes And Helm

**Observed:** no Coriolis Kubernetes or Helm deployment artifacts were found in the inspected repositories. The root chart packages this documentation site.

## :material-book-open-page-variant-outline: Documentation Map

[Discovery](discovery.md): first-path evidence and gates.

[OpenStack Provider Reference](openstack-provider.md): unvalidated local provider behavior.

[VMware Provider Reference](vmware-provider.md): unvalidated local provider behavior.

[Appliance Runtime](appliance-runtime.md): one snapshot and architecture.

[Appliance Release](appliance-release-flow.md): implementation lifecycle.

[Terminology](terminology.md): definitions.
