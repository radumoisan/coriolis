# Coriolis Appliance Release Flow

!!! abstract
    This page maps observed Jenkins, `coriolis-cd`, and `coriolis-docker` behavior. It does not define a verified or automated release policy.

## :material-book-open-page-variant-outline: Big Picture

Application development starts in repositories. Appliance delivery begins with selected refs and configuration plus a base VMware template.

```
Selected source refs and build configuration
                    +
          VMware base template
                    |
                    v
       Clone appliance build VM
                    |
                    v
    Bootstrap OS, Docker, PKI, and config
                    |
                    v
       Build/pull container images
                    |
                    v
        Deploy Kolla dependencies
                    |
                    v
       Deploy and configure Coriolis
                    |
                    v
       Run basic readiness checks
                    |
                    v
          Prepare appliance state
                    |
                    v
          Export OVA + SHA-256
                    |
                    v
             Build candidate
                    |
                    v
      Verify checksum and import OVA
                    |
                    v
       Prepare independent test VM
                    |
                    v
        Run real migration tests
                    |
                    v
          Review and approve
                    |
                    v
       Publish OVA and release data
                    |
                    v
       Coriolis appliance release
```

Inspected local scripts establish individual stages, but do not prove that Jenkins automatically chains every stage or mandates every gate.

## :material-book-open-page-variant-outline: Build Inputs

The observed inputs include selected source refs, provider selection, image tag, Kolla release, registry and namespace, optional components, and VM or release identifiers. Desired inputs are immutable Git commits and image digests; the observed process still uses some mutable branch and tag inputs.

## :material-book-open-page-variant-outline: Base Template And Build VM

`coriolis-cd boot base appliance` clones and powers on a VMware template, waits for VMware Tools and an IP address, then returns an address. The base template remains unchanged; its clone is the build VM. Environment input selects the template and datacenter, with optional datastore and network selection.

## :material-book-open-page-variant-outline: Remote Build Preparation

Jenkins or CD connects to the build VM over SSH, logs into the registry, clones `coriolis-docker`, creates configuration, and sets provider, repository, and image-policy options. It uses temporary source-access material and removes it afterward. This prepares the remote build environment; it is not the final appliance yet.

## :material-book-open-page-variant-outline: Bootstrap

`coriolis-ansible bootstrap` prepares local configuration, passwords, certificate infrastructure, directories, Docker, and Kolla state. Step CA provides local certificate infrastructure. Generated state depends on the base template and selected configuration.

## :material-book-open-page-variant-outline: Build Or Pull Images

Building mode uses `docker_pull_images: false` and `coriolis-ansible build`. It obtains source and provider inputs and builds images. Deployment roles can instead pull prebuilt images. The worker image includes the selected providers.

Unpinned external inputs, including `libqemu`, are a reproducibility gap.

## :material-book-open-page-variant-outline: Deploy Kolla Dependencies

Kolla and Kolla-Ansible deploy internal service dependencies, including Keystone, Barbican, RabbitMQ, MariaDB, Memcached, and Kolla Toolbox. This is not a customer OpenStack cloud.

## :material-book-open-page-variant-outline: Deploy And Configure Coriolis

`coriolis-ansible deploy` creates the Coriolis database and Keystone service and endpoints, renders configuration, and starts the API, conductor, scheduler, transfer cron, worker, Web UI, proxy, logger, and console. Containers normally use restart policies. Actual enabled services depend on configuration.

## :material-book-open-page-variant-outline: Basic Readiness And Preparation

Observed readiness checks list Keystone endpoints, Barbican secrets, and Coriolis endpoints. They are not a complete health test. Release preparation enables the console, rotates appliance access, clears logs and cache, and may reboot.

## :material-book-open-page-variant-outline: Export OVA And Checksum

`coriolis-cd export instance` powers off the build VM and obtains VMware disk data through an export lease, generates an OVF descriptor, and packages the OVF and disks as an OVA. It does not itself generate a sidecar checksum. A Jenkins helper creates or moves the OVA and its `.ova.sha256sum`, so checksum provenance is separate from OVA export.

The OVA captures application, OS, container, and configuration state. Its output is a candidate artifact, not automatically a release.

## :material-book-open-page-variant-outline: Import Candidate

`coriolis-cd deploy appliance` gets an OVA from a URL, creates a vSphere import specification, maps OVF networking to the target network, uploads disks, powers the VM on, and waits for Tools and an IP address. This produces an independent VM.

Current import does not verify the checksum; integrity must be verified first as an operational gate. Import proves VM import and boot, not application health.

## :material-book-open-page-variant-outline: Prepare For Tests

A separate test job connects to the imported appliance, exposes APIs as needed, obtains trust material, installs a license, adds source and destination endpoints, and validates test configuration. All setup details are environment-specific and must not be treated as customer instructions.

## :material-book-open-page-variant-outline: Migration Validation

A test definition specifies source and destination provider and endpoint, source VM, maps and options, validation port, and cleanup. Validate a real workload: source VM -> transfer -> destination storage -> OS morphing worker -> destination VM -> guest connectivity.

The selected target is a minimal Linux VMware-to-OpenStack test, but no recent validation was observed for RC2.

## :material-book-open-page-variant-outline: Review, Approval, And Publication

An exact formal approval gate was not found locally. Suitable review questions cover OVA import and boot, service and API behavior, license, migration and cleanup, integrity, versions, and known issues.

A publication script uploads an OVA to external storage under a timestamp-based name and does not itself upload the checksum. The relationship to internal versioned artifacts and sidecars is unresolved. An export job name alone does not prove release status.

## :material-book-open-page-variant-outline: Artifact States

| State | Definition |
| --- | --- |
| Base template | The unchanged VMware template selected as the clone source. |
| Build VM | The template clone used for remote build and deployment work. |
| Configured appliance VM | The build VM after bootstrap, images, dependencies, Coriolis configuration, and preparation. |
| OVA build artifact | The exported OVA plus separately produced checksum sidecar, without release qualification implied. |
| Release candidate | An OVA artifact selected for import and review. |
| Validated candidate | A release candidate with recorded integrity, import, boot, and required validation evidence. |
| Published release | A validated candidate whose OVA and release data have been published through the applicable approval process. |
| Deployed customer appliance | A published OVA imported and configured in a customer environment. |

## :material-book-open-page-variant-outline: Observed Automation Limits And Open Questions

Local jobs and scripts exist for setup, export, import, tests, release, and publication. Job trigger chaining, approval policy, mandatory tests, naming, promotion metadata, and the exact checksum-publication flow remain unresolved. Existing discovery evidence separately tracks registry, source pinning, platform compatibility, and first-path validation.

## :material-book-open-page-variant-outline: Related Information

[Terminology](terminology.md) and [Discovery](discovery.md)
