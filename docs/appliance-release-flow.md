# Coriolis Appliance Release Flow

!!! abstract
    This in-progress conceptual reference maps observed local implementation evidence. It is not a customer runbook and does not define an approved automated release policy.

## :material-book-open-page-variant-outline: Big Picture

The flow below describes a possible lifecycle from selected inputs to a release. It is conceptual, not proof of an automated end-to-end implementation.

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

The inspected repository has separate Jenkins scripts for setup, export, import, tests, release, and publication. It does not show automatic job chaining, parameter handoff, mandatory tests, or approval policy.

| Tool | Observed responsibility |
| --- | --- |
| Jenkins/`coriolis-ci` | Orchestrates separate job scripts and passes selected inputs to CD operations. |
| `coriolis-cd` | Handles VMware and SSH operations for boot, build, deployment, export, import, and tests. |
| `coriolis-docker` | Handles appliance-local image building, bootstrap, and deployment. |
| Ansible | Applies the appliance-local configuration and role playbooks. |
| Kolla-Ansible | Deploys Coriolis-internal support services. |
| VMware/vSphere | Stores templates and VMs, clones, exports, imports, and supplies platform readiness. |
| Artifact storage | Receives the published OVA through the observed publication script. |

### :material-application-edit-outline: Implementation Evidence

Separate entry points are under `coriolis-ci/appliance/setup.groovy:1-77`, `export.groovy:1-28`, `import.groovy:1-18`, `tests.groovy:1-53`, `release.groovy:1-69`, and `publish.groovy:1-13`.

## :material-book-open-page-variant-outline: Build Inputs

Observed job and build inputs include selected source refs, export/import provider selection, custom modules, provider repository owner and branch maps, the `coriolis-docker` ref, release or image tag, Kolla release or tag, registry and namespace, optional components, platform, base-template selection, VM identifier, and export, reboot, and cleanup flags. Jenkins configuration obtains VMware provider data from configured credentials; this page does not expose values.

`VM_IDENTIFIER` and the resulting OVA name identify a build artifact. Release identity is separate. The local pipeline does not derive release identity from Git commits, Git tags, or Jenkins build numbers.

Immutable commits and image digests are desirable inputs. Observed interfaces also permit mutable branches and tags, including `master` and `latest` defaults where local code defines them. This is evidence of a reproducibility limit, not a final policy statement. The key boundary is Jenkins invoking `coriolis-cd` operations for boot, Docker login, component build, and component deployment.

Result: selected inputs describe one attempted appliance build. They do not by themselves prove source, image, or release provenance.

### :material-application-edit-outline: Implementation Evidence

`coriolis-ci/appliance/setup.groovy:9-45`; `coriolis-ci/src/coriolis/ci/Appliance.groovy:27-163`; `coriolis-ci/vars/global_vars.groovy:6-20`; `coriolis-cd/coriolis_cd/operations/coriolis_build.py:35-53`.

## :material-book-open-page-variant-outline: Base Template And Build VM

`coriolis-cd boot base appliance` parses and validates the selected provider connection and environment JSON, then calls the VMware provider. Input selects a template and datacenter, with optional datastore and network plus a new VM identifier.

The VMware provider finds the template, cluster or resource pool, and datastore; clones the template; powers on the clone; waits for VMware Tools and an IPv4 address; and returns that address as the later SSH target. The template remains unchanged. Its clone is the build VM.

Result: platform-level boot and IP readiness for a new build VM. This does not validate Docker, Kolla, Coriolis, or migration function.

### :material-application-edit-outline: Implementation Evidence

`coriolis-ci/src/coriolis/ci/Appliance.groovy:41-60`; `coriolis-cd/coriolis_cd/cli/boot_instance.py:13-55`; `coriolis-cd/coriolis_cd/providers/vmware/provider.py:221-272`, `425-465`, `652-687`.

## :material-book-open-page-variant-outline: Remote Build Preparation

The observed order is remote registry login; clone the selected `coriolis-docker` ref; create or update `config.yml` and `docker-images-config.yml`; write provider, module, repository, licensing, image-policy, and release-tag settings; bootstrap; upload a temporary source key; build; then remove the key and registry login. The deployment operation separately reclones `coriolis-docker`.

Result: remote build configuration exists on the build VM, not a final appliance. Build and deploy checkout identity is not proven to be the same.

!!! warning
    Source-access and registry arguments are sensitive operational inputs. They must not be logged in a customer procedure.

### :material-application-edit-outline: Implementation Evidence

`coriolis-cd/coriolis_cd/operations/coriolis_build.py:18-72`; `coriolis-cd/coriolis_cd/operations/coriolis_deploy.py:13-38`; `coriolis-cd/coriolis_cd/operations/common.py:16-66`.

## :material-book-open-page-variant-outline: Bootstrap

`coriolis-ansible` creates or updates configuration and passwords, then runs `bootstrap.yml`. Bootstrap applies common preparation and the Step CA role. Step CA creates local state and service configuration, bootstraps its configuration, generates or reuses certificates, and copies certificate material to Kolla and Coriolis inputs.

Kolla deployment is a later, separate stage. Result: base appliance services and PKI inputs are prepared. Existing custom certificate state and selected inputs affect the result. Bootstrap success does not prove Kolla, Coriolis, or external reachability.

### :material-application-edit-outline: Implementation Evidence

`coriolis-docker/coriolis-ansible:26-56`; `coriolis-docker/coriolis_ansible/bootstrap.yml:1-12`; `coriolis-docker/coriolis_ansible/roles/bootstrap/step-ca/tasks/setup.yml:2-136`.

## :material-book-open-page-variant-outline: Build Or Pull Images

For source builds, CD writes `docker_pull_images: false`, selects a target image tag, and invokes `coriolis-ansible build`. Build plays select `build.yml` roles, clone core and provider sources, render Dockerfiles and entrypoints, obtain external artifacts, and build images conditionally.

Core covers core, replicator, writer, and the Python client. The worker clones selected providers plus the unconditional Metal Hub client and downloads `libqemu`. Deployment can instead pull images under `docker_pull_images`; image existence is not provenance verification. This stage does not prove a release-image push.

Result: selected images may be locally built or pulled. Mutable refs, unpinned `libqemu`, and source or repository compatibility remain reproducibility limits.

### :material-application-edit-outline: Implementation Evidence

`coriolis-cd/coriolis_cd/operations/coriolis_build.py:49-67`; `coriolis-docker/coriolis-ansible:54-56`; `coriolis-docker/coriolis_ansible/appliance.yml:1-67`; `coriolis-docker/coriolis_ansible/roles/coriolis/common/tasks/build.yml:7-60`; `coriolis-docker/coriolis_ansible/roles/coriolis/worker/tasks/build.yml:10-60`; `coriolis-docker/coriolis_ansible/roles/coriolis/api/tasks/setup_api_container.yml:2-17`.

## :material-book-open-page-variant-outline: Deploy Kolla Dependencies

Kolla is Coriolis-internal support infrastructure, not a customer OpenStack cloud. The observed path configures and restarts Docker, prepares files, installs Kolla-Ansible at the selected branch, initializes passwords, globals, and policy, configures registry, namespace, release, network, TLS, and services, then deploys and post-deploys. It sources generated admin RC material and retries endpoint and secret-list commands.

Certificate inputs come from Bootstrap. A Kolla image-build path is separate from Kolla deployment. Result: internal dependencies may be deployed; the checks are narrow CLI smoke tests.

### :material-application-edit-outline: Implementation Evidence

`coriolis-cd/coriolis_cd/operations/coriolis_deploy.py:40-48`; `coriolis-docker/kolla/deploy.sh:7-84`; `coriolis-docker/kolla/build.sh:7-21`.

## :material-book-open-page-variant-outline: Deploy And Configure Coriolis

CD deployment repeats registry login, configuration initialization, and bootstrap, then runs `kolla/deploy.sh`, `coriolis-ansible deploy`, and licensing-database reset. The ordered playbook roles are MariaDB, compressor, common, logger, API, conductor, transfer cron, scheduler, minion manager, deployer manager, worker, web, web proxy, licensing server, console editor, Metal Hub, and validation. Actual optional services are configuration-dependent.

The common role gathers Kolla facts, creates the Coriolis database and user, creates configuration state, and creates Keystone user, service, and public, internal, and admin endpoints. Service containers typically define host networking and restart policy. A release file creates or preserves version state, but is not sufficient provenance.

Result: a configured Coriolis appliance may be running. Full behavior remains unproven until later checks and tests.

### :material-application-edit-outline: Implementation Evidence

`coriolis-cd/coriolis_cd/operations/coriolis_deploy.py:40-61`; `coriolis-docker/coriolis_ansible/appliance.yml:1-87`; `coriolis-docker/coriolis_ansible/roles/coriolis/common/tasks/setup.yml:2-112`; `coriolis-docker/coriolis_ansible/roles/coriolis/api/tasks/setup_api_container.yml:2-17`.

## :material-book-open-page-variant-outline: Basic Readiness Checks

Kolla retries endpoint and secret-list CLI checks. Coriolis validation repeats endpoint and secret checks, lists Coriolis endpoints, and configures the default region, optional Metal Hub, and release file.

Result: selected CLI state is available. These checks are not container probes, complete API endpoint tests, migration tests, UI tests, or proof of external connectivity.

### :material-application-edit-outline: Implementation Evidence

`coriolis-docker/kolla/deploy.sh:77-84`; `coriolis-docker/coriolis_ansible/roles/coriolis/validation/tasks/deployment_check.yml:1-30`; `coriolis-docker/coriolis_ansible/roles/coriolis/validation/tasks/deploy.yml:1-6`.

## :material-book-open-page-variant-outline: Prepare Appliance State

After deploy, Jenkins setup enables console and rc-local behavior, rotates appliance and OpenStack admin access, updates relevant generated configuration, clears history, Docker client state, logs, and Landscape cache, and can export or reboot. No access values belong in this reference.

Persisted disk state is what export packages, so cleanup and rotation happen before export. This should be carefully audited rather than treated as generic sanitization. Setup and release flows are distinct from full CI. Release attempts comparable preparation and can create a password sidecar when supplied access information.

An apparent `release.groovy` variable-order issue is unresolved implementation evidence, not a confirmed runtime failure.

### :material-application-edit-outline: Implementation Evidence

`coriolis-ci/appliance/setup.groovy:47-76`; `coriolis-ci/appliance/release.groovy:41-68`; `coriolis-ci/src/coriolis/ci/Appliance.groovy:199-257`.

## :material-book-open-page-variant-outline: Export The VM

The observed VMware export sequence is:

1. Validate input and provider.
2. Require an empty target export directory.
3. Find the VM.
4. Stop the guest or force power off, then wait.
5. Read `nvram` extra configuration and temporarily clear it when present for pre-6.7 import compatibility.
6. Request an `ExportVm` lease.
7. Skip `.nvram`.
8. Download disks through lease device URLs and record disk metadata.
9. Complete the lease.
10. Generate an OVF descriptor with the VMware OVF manager.
11. Write the OVF.
12. Create a TAR OVA with the OVF followed by files.
13. Delete temporary files.
14. Restore original NVRAM.
15. Return the absolute OVA path.

Result: an OVA artifact is produced. The build VM remains in VMware and powered off; failure handling may vary.

### :material-application-edit-outline: What The OVA Captures

Observed contents are virtual disks and a VMware-produced OVF descriptor; NVRAM is intentionally excluded. The following are *typically persisted state*, not an explicit product contract: guest OS and installed packages, Coriolis configuration, container images or layers and persistent data, database and service state, PKI and certificates, console tooling, and any not-scrubbed logs, caches, licenses, or secrets.

Not captured or proven are runtime memory, CPU, or process state; snapshots or external datastore files; NVRAM; and a manifest or signature.

See [Appliance Runtime](appliance-runtime.md) for separate runtime evidence and its limitations.

### :material-application-edit-outline: Implementation Evidence

`coriolis-cd/coriolis_cd/cli/export_instance.py:13-57`; `coriolis-cd/coriolis_cd/providers/vmware/provider.py:408-423`, `489-649`, `749-791`.

## :material-book-open-page-variant-outline: Generate The Checksum

Checksum generation is separate from export. A CI helper moves the exported OVA to an artifact directory, runs SHA-256 to create an `.ova.sha256sum` sidecar, and sets permissions. CD itself does not create the checksum. The local artifact is an OVA plus sidecar; release export can also create a local password sidecar when supplied access information.

The publisher receives one OVA file only. Separate checksum and sidecar publication paths are unresolved. A checksum establishes local byte identity, not a signature, provenance, independent verification, or release status.

### :material-application-edit-outline: Implementation Evidence

`coriolis-ci/src/coriolis/ci/Appliance.groovy:260-282`; `coriolis-ci/appliance/scripts/publish_appliance.sh:5-17`; `coriolis-ci/appliance/scripts/cleanup_exported_appliances.sh:5-7`.

## :material-book-open-page-variant-outline: Import Candidate

The observed import sequence is:

1. Validate input and provider.
2. Connect and select a datacenter.
3. Select the configured datastore, or the largest datastore.
4. Select an optional network and the first cluster or resource pool.
5. Download the OVA.
6. Locate and read the first OVF in the TAR.
7. Map every OVF network to the supplied target when one is supplied.
8. Create an ImportSpec and reject errors.
9. Import the VApp, wait for the lease, and keep it alive.
10. Match every OVF item, TAR disk, and lease URL, then upload.
11. Complete the lease, or abort and delete a partial VM on upload error.
12. Locate and power the imported VM.
13. Wait for state, delete the local OVA, and wait for Tools and IP.

The imported validation appliance VM is independent of the base template, build VM, migration source workload VM, and migrated workload VM. If no network is supplied, resulting platform behavior is unverified VMware behavior.

!!! warning
    Current code does not verify SHA-256 or source provenance. Operationally, verification must occur before importing. Import proves only vSphere import, power, Tools, and IP, not Coriolis health, licensing, endpoints, or migration.

### :material-application-edit-outline: Implementation Evidence

`coriolis-cd/coriolis_cd/cli/deploy_appliance.py:13-58`; `coriolis-cd/coriolis_cd/providers/vmware/provider.py:178-187`, `275-394`, `713-746`.

## :material-book-open-page-variant-outline: Prepare For Tests

The test job accepts separate appliance IP and SSH inputs rather than import output. Local code therefore does not show import-to-test handoff. Test configuration parses JSON test IDs, requires nonempty IDs, and requires every ID to exist. Its schema validates endpoints, providers, and tests.

The operation obtains appliance trust and admin state, exposes the API, adds a temporary license, and adds endpoints. Existing scripts do not show one full preparation sequence or a clean VM reset, and use environment-specific inputs. This is not customer instruction.

Result: a test environment may be prepared, but the full setup boundary remains unresolved.

### :material-application-edit-outline: Implementation Evidence

`coriolis-ci/appliance/tests.groovy:3-51`; `coriolis-ci/src/coriolis/ci/Appliance.groovy:338-470`; `coriolis-cd/coriolis_cd/testing/schemas/testing_config.json:1-135`; `coriolis-cd/coriolis_cd/operations/coriolis_test.py:83-149`.

## :material-book-open-page-variant-outline: Run Migration Validation

The observed validation sequence is:

1. Parse environment JSON and default storage.
2. Authenticate a Coriolis session.
3. Resolve endpoints.
4. Create a transfer with scenarios, maps, and VM.
5. Run the first transfer and wait.
6. Run a second incremental transfer.
7. Create a deployment and wait.
8. Extract candidate IPv4, falling back to destination-provider lookup.
9. Test each configured TCP port.
10. Optionally delete the deployment and transfer disks.

Validation covers execution success or status, IP discovery, and TCP connectivity only. It does not prove protocol behavior, application behavior, or data integrity. Test IDs run in parallel in Jenkins and logs are collected in `finally`. The imported appliance validation VM, migration source workload VM, and migrated destination workload VM are different objects.

!!! warning
    Cleanup is optional and can fail. The observed code has no final residual-resource inventory.

### :material-application-edit-outline: Implementation Evidence

`coriolis-ci/appliance/tests.groovy:7-50`; `coriolis-cd/coriolis_cd/operations/coriolis_test.py:12-80`; `coriolis-cd/coriolis_cd/testing/coriolis_tester.py:232-364`; `coriolis-cd/coriolis_cd/testing/deployment/validation.py:12-41`.

## :material-book-open-page-variant-outline: Review, Approval, And Publication

| Activity | Observed state |
| --- | --- |
| Technical validation | Test scripts exist, but their result is not linked to publication locally. |
| Review | Not linked in local automation. A proposed review gate asks about OVA, import, boot, API, license, migration, cleanup, hash, version, and known issues. |
| Approval | No formal local approval gate is shown. |
| Publication | Directly represented by a script that uploads one OVA. |

The publish script accepts one file, gives the blob a timestamped name, and uploads the OVA only. It does not inspect test results, checksum, or approval, and does not publish sidecars. No exact public URL is asserted here. Release status is operational or external policy, not an export job name or upload alone.

### :material-application-edit-outline: Implementation Evidence

`coriolis-ci/appliance/publish.groovy:4-11`; `coriolis-ci/appliance/scripts/publish_appliance.sh:5-18`.

## :material-book-open-page-variant-outline: Artifact States And Object Map

| Artifact state | Meaning |
| --- | --- |
| Base template | Unchanged VMware clone source. |
| Build VM | Template clone used to build and configure the appliance. |
| Configured appliance VM | Build VM after bootstrap, deployment, readiness, and preparation. |
| OVA build artifact | Exported OVA, with checksum sidecar produced separately. |
| Candidate | Policy or inference, not a code state. |
| Validated candidate | Proposed evidence definition; no generated manifest is observed. |
| Published release | Upload is observed, not a release manifest. |
| Customer appliance | Outside observed CI. |

| Object | Role |
| --- | --- |
| Base template | Source for the appliance build clone. |
| Build VM | VM modified and exported by the build flow. |
| Imported validation appliance VM | Independent VM used to assess an imported OVA. |
| Migration source workload VM | Workload selected for migration validation. |
| Migrated destination workload VM | Destination workload created by migration validation. |

Names can all look like VM names, but these roles are distinct.

### :material-application-edit-outline: Implementation Evidence

The object boundaries are observed across `coriolis-cd/coriolis_cd/providers/vmware/provider.py:221-394`, `408-649`, and `713-791`; candidate and validated-state labels are proposed documentation distinctions.

## :material-book-open-page-variant-outline: Observed Automation Limits And Open Questions

- Separate job scripts exist, but no trigger or orchestration proof connects them.
- Setup and release are distinct flows; neither proves a full CI sequence.
- `release.groovy` appears to call `enable_console_script(appliance_ssh_info)` before variable initialization at lines 46 and 48. Runtime behavior is unconfirmed.
- Checksum ownership and publisher handling of sidecars are unresolved.
- Import-to-test handoff is unknown.
- Cleanup and log collection are optional separate behavior.
- No RC marker, version derivation, or promotion manifest is observed.
- No formal approval gate is observed.
- External Jenkins configuration may fill gaps, but this is unresolved.

The separate Discovery page tracks registry and source pinning, platform compatibility, and first migration questions.

### :material-application-edit-outline: Implementation Evidence

`coriolis-ci/appliance/setup.groovy:1-77`; `coriolis-ci/appliance/export.groovy:1-28`; `coriolis-ci/appliance/import.groovy:1-18`; `coriolis-ci/appliance/tests.groovy:1-53`; `coriolis-ci/appliance/release.groovy:1-69`; `coriolis-ci/appliance/publish.groovy:1-13`.

## :material-book-open-page-variant-outline: Related Information

[Terminology](terminology.md), [Appliance Runtime](appliance-runtime.md), and [Discovery](discovery.md)
