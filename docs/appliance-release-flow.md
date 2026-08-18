# Coriolis Appliance Release Flow

!!! abstract
    This in-progress conceptual reference maps observed local implementation evidence. It is not a customer runbook and does not define an approved automated release policy.

## :material-book-open-page-variant-outline: Lifecycle Summary

```text
selected inputs + base template -> build VM -> prepare/bootstrap
-> images/dependencies/application -> readiness -> clean/export OVA + SHA-256
-> import/test migration -> publish
```

**Source evidence:** scripts exist separately. **Unknown:** automatic chaining, mandatory gates, and approval policy.

Separate stages can be invoked with selected inputs; their presence does not establish an end-to-end release.

| Tool | Responsibility |
| --- | --- |
| Jenkins/`coriolis-ci` | Separate setup, export, import, test, release, and publish scripts. |
| `coriolis-cd` | VMware, SSH, build, deploy, export, import, and test operations. |
| `coriolis-docker` | Appliance image build, bootstrap, and deployment. |
| Ansible | Appliance configuration and roles. |
| Kolla-Ansible | Internal support-service deployment. |
| VMware | Templates, VMs, clone, export, import, and platform readiness. |
| Artifact storage | Published OVA destination. |

## :material-book-open-page-variant-outline: Build Inputs And Reproducibility

- Selected inputs group source, provider, module, and repository maps; Docker and Kolla refs; image and release tags; registry and namespace; optional components; and platform, template, VM, and operation flags.
- Provider connection and environment JSON, including custom modules, are selected inputs.
- Export and import provider selection is independent from source and destination migration providers.
- `VM_IDENTIFIER` and the OVA identify a build VM and artifact; neither defines release identity, which is not derived from Git or Jenkins.
- Registry input does not prove availability, and image pull does not verify provenance.
- Mutable branches, tags, and Kolla refs are permitted and can differ from image tags; immutable commits and digests are reproducibility controls, so inputs describe an attempted build rather than a release claim and do not establish source, image, or release provenance.

## :material-book-open-page-variant-outline: Build VM And Preparation

- VMware selects a template, clones and powers a build VM, waits for VMware Tools and IPv4, and preserves the template.
- Platform selection uses template, datacenter, cluster or resource pool, optional datastore, optional network, and VM identifier inputs.
- Remote preparation uses the selected ref and configuration, with a temporary source-key lifecycle and registry-login cleanup; deployment separately reclones `coriolis-docker`.
- Bootstrap prepares configuration, passwords, and Step CA local state and certificate material for Kolla and Coriolis.
- **Unknown:** build and deploy checkout identity; bootstrap and platform readiness do not prove Docker, Kolla, Coriolis, migration, or external reachability.

!!! warning
    Source access, registry inputs, and generated passwords are sensitive operational inputs, not customer-runbook content.

## :material-book-open-page-variant-outline: Build And Deploy

- Source builds create local images while deployment can pull them; worker reproducibility can require selected providers, the Metal Hub client, and `libqemu`.
- Source build roles clone core and provider sources, render Dockerfiles and entry points, obtain external artifacts, and build selected core, replicator, writer, Python-client, and worker images.
- Mutable refs, unpinned external artifacts, and repository compatibility limit reproducibility.
- Kolla provides internal support services, not a customer OpenStack cloud, and configures Docker, passwords, globals, registry, namespace, release, network, TLS, services, deploy, post-deploy, certificate/bootstrap inputs, and selected endpoint and secret checks.
- Coriolis deployment orders core, worker, UI, licensing, Metal Hub, and validation roles; optional services remain configuration dependent.
- Common creates the Coriolis database, Keystone user, service, and endpoints; the release file preserves version state, containers use host networking and restart policy, and deployment resets the licensing database.
- Readiness is limited to selected endpoint and secret CLI checks, not full health, UI, migration, or external-reachability validation.

## :material-book-open-page-variant-outline: Prepare And Export

- Setup and release preparation clear selected history, Docker state, logs, and cache, rotate access, update configuration, and require audit of persisted disk state.
- Setup and release are distinct flows and do not establish a complete CI sequence.
- Export requires an empty target directory and leaves the build VM powered off.
- Export temporarily removes NVRAM, uses an `ExportVm` lease for disks and OVF, creates a TAR OVA, restores NVRAM, and removes temporary files.
- The OVA captures disks and OVF, but not NVRAM, runtime memory, or external snapshots.
- A separate helper creates the SHA-256 sidecar and moves the artifact; CD export does not generate the checksum.
- The release flow may create a local password sidecar when supplied access information.
- The OVA path returned by export is local to the build flow.

!!! warning
    A checksum is not a signature or provenance proof; publisher sidecar handling is unresolved.

See [Appliance Runtime](appliance-runtime.md) for persistence limits.

## :material-book-open-page-variant-outline: Import And Test

- Import selects datacenter, datastore, optional network, and cluster or resource pool; downloads the OVA, reads OVF, maps networks, uploads lease disks, powers on, and waits for Tools and IP.
- Without a datastore, the provider selects the largest; without a network, platform behavior is unknown.
- Import matches OVF items, TAR disks, and lease URLs; upload errors abort the lease and delete a partial VM.
- Import does not validate checksum or provenance and proves only vSphere import, power, Tools, and IP.
- Test configuration uses separate appliance inputs; import-to-test handoff is unknown, and its schema validates endpoints, providers, and nonempty listed test IDs.
- License and endpoint preparation are environment-specific, not a customer runbook.
- Migration validation runs transfer, incremental transfer, deployment, IP/TCP checks, and optional deletion.
- Jenkins runs configured test IDs in parallel and collects logs in `finally`.
- Proof is limited to execution status, IP discovery, and TCP connectivity, not application behavior, data integrity, or protocol behavior.
- Cleanup requires destination inventory inspection; the imported appliance, migration source workload, and migrated destination workload are distinct VMs.

!!! warning
    Cleanup is optional; the code has no final residual-resource inventory.

## :material-book-open-page-variant-outline: Publication And Object Boundaries

- Publish uploads one timestamped OVA only, not test results, checksum, approval, or sidecars.
- No exact public URL or release manifest is established by local code.
- Object roles: base template is the build-clone source; build VM is modified and exported; imported validation appliance VM is an independent import-test VM; migration source workload VM is selected for validation; migrated destination workload VM is the migration target.
- Candidate, validated, and published are policy labels, not code states.
- Customer appliance state is outside the observed CI implementation.
- Upload does not inspect validation results and is not validation or release status.

## :material-book-open-page-variant-outline: Observed Automation Limits

- No job chaining, handoff, or mandatory technical validation is shown.
- Setup and release are distinct.
- Checksum sidecar publication is unresolved.
- Import-test handoff is unknown.
- Cleanup and log collection are separate.
- No RC, version, promotion, or approval manifest is observed; external Jenkins configuration may add behavior but was not inspected.

See [Discovery](discovery.md) for platform and first-migration gates.

## :material-book-open-page-variant-outline: Implementation Evidence

`coriolis-ci/appliance/setup.groovy:1-77`; `coriolis-ci/appliance/export.groovy:1-28`; `coriolis-ci/appliance/import.groovy:1-18`; `coriolis-ci/appliance/tests.groovy:1-53`;
`coriolis-ci/appliance/release.groovy:1-69`; `coriolis-ci/appliance/publish.groovy:1-13`; `coriolis-ci/src/coriolis/ci/Appliance.groovy:27-282,338-470`;
`coriolis-ci/appliance/scripts/publish_appliance.sh:5-18`; `coriolis-cd/coriolis_cd/cli/boot_instance.py:13-55`; `coriolis-cd/coriolis_cd/cli/export_instance.py:13-57`;
`coriolis-cd/coriolis_cd/cli/deploy_appliance.py:13-58`; `coriolis-cd/coriolis_cd/operations/coriolis_build.py:18-72`; `coriolis-cd/coriolis_cd/operations/coriolis_deploy.py:13-61`;
`coriolis-cd/coriolis_cd/operations/coriolis_test.py:12-149`; `coriolis-cd/coriolis_cd/providers/vmware/provider.py:178-791`; `coriolis-docker/coriolis-ansible:26-56`;
`coriolis-docker/coriolis_ansible/appliance.yml:1-87`; `coriolis-docker/coriolis_ansible/bootstrap.yml:1-12`; `coriolis-docker/kolla/deploy.sh:7-84`.

## :material-book-open-page-variant-outline: Related Information

[Terminology](terminology.md), [Appliance Runtime](appliance-runtime.md), and [Discovery](discovery.md).
