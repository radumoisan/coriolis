# Coriolis Discovery

!!! abstract
    This in-progress map records observed product boundaries, delivery paths, and unresolved questions. It is not a deployment tutorial or finalized architecture.

## :material-book-open-page-variant-outline: Repository Landscape

- `coriolis-oss` is the core application source.
- `coriolis-docker` provides build and deployment automation.
- `coriolis-cd` provides appliance delivery and deployment CLI tooling.
- `coriolis-ci` is the Jenkins orchestrator and validation layer.
- `python-coriolismetalhubclient` is an auxiliary client.

This root repository hosts the MkDocs site and its Helm chart only. That chart is not product Helm support.

## :material-book-open-page-variant-outline: Observed Relationships

`coriolis-ci` invokes `coriolis-cd`; `coriolis-cd` invokes Docker tooling on an appliance; and `coriolis-docker` builds or deploys services. `coriolis-oss` is a source input to those builds. These relationships are not a simple linear dependency graph: repositories can be used independently and additional sources contribute to individual images.

## :material-book-open-page-variant-outline: Deployment Model

The observed application deployment model uses Docker and Ansible. Selected OpenStack supporting services are deployed by upstream Kolla and Kolla-Ansible: Keystone, Barbican, RabbitMQ, MariaDB, and Memcached. No product Helm or Kubernetes deployment artifacts were found.

## :material-book-open-page-variant-outline: Image Supply Chain

### :material-application-edit-outline: Coriolis Images

Coriolis-owned images share the `coriolis-common` base where applicable. Worker packages incorporate provider modules. The common image bundles the private replicator and writer. Application image registry and tags are configurable, but observed defaults are mutable.

### :material-application-edit-outline: External Inputs

Observed public base and runtime inputs include Ubuntu, Go, Node, Step CA, and InfluxDB. Kolla is a separate dependency image family rather than a Coriolis-owned application image family; its exact official public image mapping remains unresolved.

## :material-book-open-page-variant-outline: Investigation Target

The current intended deployment investigation targets a single Ubuntu 22.04 VM as a standard web appliance, with an OpenStack-to-OpenStack test migration and no Jenkins pipeline. The working assumption is a private registry for internally built Coriolis images and direct public pulls for public images. This is an investigation target, not a verified deployment recipe.

## :material-book-open-page-variant-outline: Confirmed Gaps And Blockers

- Kolla version/tag alignment conflicts, and the exact public Kolla image list, remain unresolved.
- The private dependency closure is incomplete.
- `coriolis_provider_vhi` is referenced, but no source location was identified.
- The worker build unconditionally clones the Metal Hub client.
- `libqemu` binary provenance is unresolved.
- Logger Dockerfile behavior needs validation.
- No public or community deployment artifact was found.
- Source and image references lack immutable pinning.
- No host sizing has been recorded.
- Endpoint, DNS, TLS, and registry image availability remain decisions or audits.

## :material-book-open-page-variant-outline: Next Discovery Gates

1. Confirm private source access and required commits.
2. Locate the `coriolis_provider_vhi` source.
3. Align the Kolla release and identify the exact required images.
4. Audit registry images, tags or digests, and entrypoints.
5. Establish third-party and binary provenance.
6. Perform a first controlled installation and migration test.
