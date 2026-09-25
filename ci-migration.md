# Legacy CI Migration Baseline

## Purpose And Scope

This is a baseline for migrating two legacy Jenkins phases: build the Coriolis images inside an appliance, then run migration tests. It intentionally excludes appliance export/import, OVA publication, legacy image-publication workflows, release promotion, and deployment. Directly pushing an image produced by the proposed CIXpress build is included as part of that preliminary build design. The excluded operations appear in the Jenkins call chain only to establish where the migrated phases occur.

Facts in this document are derived from the repository paths listed below and from observational evidence for Jenkins job `4_coriolis-appliance-tests`, build 548. The Jenkins test configuration is supplied at runtime and is not checked into this repository. CIXpress is a future-state target; no CIXpress implementation is asserted here.

## Legacy Build Phase

### Role Of `coriolis-docker`

`coriolis-docker` is the legacy appliance automation project, not only a collection of Dockerfiles. It bootstraps the appliance host, generates configuration for the selected providers, clones component and provider repositories, renders and builds the Coriolis images, deploys and configures their containers, configures supporting services such as MariaDB and the Kolla-based infrastructure, validates the resulting appliance, and can publish the locally built images.

The CIXpress migration does not need to reproduce that entire appliance lifecycle. The relevant inputs to extract from `coriolis-docker` are the Dockerfile templates and their supporting files, component source repositories and branch selection, image dependency order, build-time configuration, and provider-specific worker behavior. Appliance bootstrap, service deployment, validation, legacy image-publication workflows, and release promotion remain outside the current scope. A direct registry push from the proposed CIXpress build is in scope.

The Jenkins entry point calls `Appliance.build_appliance`, which invokes `coriolis-cd build coriolis components` against the appliance. The checked-in `coriolis-cd` implementation logs the appliance into the registry, clones `coriolis-docker` under `/root/coriolis-docker` when that path is absent, generates its main and image configuration files, writes the requested provider lists and repository overrides, enables the licensing server, disables image pulls, and maps the requested release tag to `default_coriolis_docker_images_tag`. It then bootstraps the appliance, temporarily uploads the source-repository SSH key, runs `coriolis-ansible build`, removes the key, and performs remote cleanup.

Call chain:

`Jenkins ci.groovy` -> `Appliance.build_appliance` -> `coriolis-cd build coriolis components` -> `coriolis_build._run_coriolis_build` -> remote `coriolis-ansible build` -> `appliance.yml` roles -> generated `Dockerfile.j2` -> common Docker builder.

Each role uses the shared `build_dir` as Docker build context. It clones or downloads its inputs there, renders `Dockerfile.j2` as `<image>.Dockerfile`, and notifies its image handler when those tasks report changes. The common Docker builder removes the tagged local image, builds from `build_dir` with `pull: false`, applies the role tag, and retries up to ten times with a five-second delay. An explicit `docker_image_info` check also triggers a build when the tagged image is absent, while the common role separately checks for missing replicator and writer binaries. An unchanged existing image can therefore be reused, and base-image updates alone do not trigger a rebuild or pull.

The common image is a dependency for API, conductor, transfer-cron, scheduler, minion-manager, deployer-manager, and worker. Worker builds the union of configured export and import providers, then includes provider repositories and conditional package support for that union. Owner and branch overrides pass through `coriolis-cd` into `custom_repo_owner_names` and `custom_repo_branch_names`; defaults are `cloudbase` and `master` for the documented source repositories. Because the `coriolis-docker` checkout itself is cloned only when `/root/coriolis-docker` does not already exist, reusing an appliance can retain an earlier checkout instead of applying a newly requested repository URL or branch.

The legacy common Dockerfile installs the complete `coriolis-oss` Python project, including its console entry points, then adds the replicator and writer resources under `coriolis/resources/bin`. Each legacy Python-service image inherits that common image. Conductor, scheduler, transfer-cron, minion-manager, and deployer-manager are therefore effectively wrappers that select a different installed command; API is the exception because it also installs Apache and `libapache2-mod-wsgi-py3`, copies `/start-apache.sh`, and starts through that script. See `coriolis-docker/coriolis_ansible/roles/coriolis/common/templates/Dockerfile.j2`, `coriolis-docker/coriolis_ansible/roles/coriolis/common/templates/entrypoint.sh.j2`, and `coriolis-docker/coriolis_ansible/roles/coriolis/api/templates/Dockerfile.j2`.

Source checkouts are: GitHub `coriolis-compressor`, `coriolis`, `coriolis-logger`, and `coriolis-web`; Bitbucket `coriolis-replicator`, `coriolis-writer`, `coriolis-provider-<provider>`, `python-coriolismetalhubclient`, `coriolis-licensing-server`, `coriolis-metal-hub`, and `coriolis-licensing-ui`. Owner/branch overrides apply by component key, including `compressor`, `core`, `replicator`, `writer`, `logger`, `web`, each provider name, `python-metalhubclient`, `licensing-server`, `metal-hub`, and `licensing-ui`.

| Image | Template path | Base or dependency | Particularities and conditions |
| --- | --- | --- | --- |
| compressor | `coriolis-docker/coriolis_ansible/roles/coriolis/compressor/templates/Dockerfile.j2` | Go Alpine builder -> BusyBox | Clones `coriolis-compressor`; owner/branch override supported. |
| common | `coriolis-docker/coriolis_ansible/roles/coriolis/common/templates/Dockerfile.j2` | Ubuntu 22.04 | Clones core, replicator, and writer; shared base for the Python services; rebuild also follows missing replicator/writer binaries. |
| logger | `coriolis-docker/coriolis_ansible/roles/coriolis/logger/templates/Dockerfile.j2` | Go Alpine | Clones `coriolis-logger`; owner/branch override supported. |
| api | `coriolis-docker/coriolis_ansible/roles/coriolis/api/templates/Dockerfile.j2` | common image | Thin service image from the common image. |
| conductor | `coriolis-docker/coriolis_ansible/roles/coriolis/conductor/templates/Dockerfile.j2` | common image | Service command optionally uses profiling. |
| transfer-cron | `coriolis-docker/coriolis_ansible/roles/coriolis/transfer-cron/templates/Dockerfile.j2` | common image | Thin cron service image. |
| scheduler | `coriolis-docker/coriolis_ansible/roles/coriolis/scheduler/templates/Dockerfile.j2` | common image | Thin scheduler service image. |
| minion-manager | `coriolis-docker/coriolis_ansible/roles/coriolis/minion-manager/templates/Dockerfile.j2` | common image | Thin manager service image. |
| deployer-manager | `coriolis-docker/coriolis_ansible/roles/coriolis/deployer-manager/templates/Dockerfile.j2` | common image | Thin manager service image. |
| worker | `coriolis-docker/coriolis_ansible/roles/coriolis/worker/templates/Dockerfile.j2` | common image | Clones the export/import provider union; conditionally adds metal, OpenStack, oVirt, libvirt, and Nutanix support; downloads libqemu. |
| web | `coriolis-docker/coriolis_ansible/roles/coriolis/web/templates/Dockerfile.j2` | Node 18 | Clones `coriolis-web`; owner/branch override supported. |
| web-proxy | `coriolis-docker/coriolis_ansible/roles/coriolis/web-proxy/templates/Dockerfile.j2` | Ubuntu 22.04 | Renders a proxy start script and configures Apache TLS proxying. |
| licensing-server | `coriolis-docker/coriolis_ansible/roles/coriolis/licensing-server/templates/Dockerfile.j2` | Go Alpine builder -> BusyBox | Clones `coriolis-licensing-server`; owner/branch override supported. |
| console-editor | `coriolis-docker/coriolis_ansible/roles/common/console-editor/templates/Dockerfile.j2` | Ubuntu 22.04 | Also renders a README and a libvirt resource cleanup helper. |
| metal-hub | `coriolis-docker/coriolis_ansible/roles/coriolis/metal-hub/templates/Dockerfile.j2` | Go Alpine builder -> BusyBox | Clones `coriolis-metal-hub`; owner/branch override supported. |
| licensing-ui | `coriolis-docker/coriolis_ansible/roles/coriolis/licensing-ui/templates/Dockerfile.j2` | Node 11.11.0 | Built in the separate `licensing_ui` play; clones `coriolis-licensing-ui`; owner/branch override supported. |

## Legacy Test Phase

The tests job reads `TESTS_IDS`, validates that the runtime configuration is non-empty and contains every requested ID, then loads endpoints, export providers, import providers, and tests from that configuration. It registers configured non-metal endpoints, creates one parallel stage per selected test, and runs `coriolis-cd run coriolis test` with scenario, endpoint, environment, storage, instance, network map, optional validation ports, and optional resource cleanup. It always removes the temporary certificate copy and collects appliance logs after the run.

The source-environment helper dynamically creates test sources only for public-cloud and metal endpoint types. The observed active suite uses `VMware_vCenter8`, so its sources are pre-existing rather than dynamically created by that helper. Dynamic-source cleanup is likewise limited to those public-cloud and metal paths. Destination resource cleanup is passed to the external test command only when the Jenkins cleanup parameter is enabled.

The following 20 active selections are recorded from Jenkins job `4_coriolis-appliance-tests`, build 548. They are observational configuration evidence, not repository-defined test data. Each is a replica scenario from `VMware_vCenter8`; the operating system is inferred from the ID.

| Test ID | Source | Scenario | Destination | Guest OS | Description |
| --- | --- | --- | --- | --- | --- |
| `VMWARE_UBUNTU_24_04_OPENSTACK` | VMware_vCenter8 | replica | OpenStack_Coriolis | Ubuntu 24.04 | Replicate the pre-existing Ubuntu VM to OpenStack. |
| `VMWARE_ROCKY_9_OPENSTACK` | VMware_vCenter8 | replica | OpenStack_Coriolis | Rocky 9 | Replicate the pre-existing Rocky VM to OpenStack. |
| `VMWARE_OPENSUSE_16_OPENSTACK` | VMware_vCenter8 | replica | OpenStack_Coriolis | openSUSE 16 | Replicate the pre-existing openSUSE VM to OpenStack. |
| `VMWARE_WS2022_OPENSTACK` | VMware_vCenter8 | replica | OpenStack_Coriolis | Windows Server 2022 | Replicate the pre-existing Windows VM to OpenStack. |
| `VMWARE_UBUNTU_24_04_PROXMOX` | VMware_vCenter8 | replica | Proxmox3 | Ubuntu 24.04 | Replicate the pre-existing Ubuntu VM to Proxmox. |
| `VMWARE_ROCKY_9_PROXMOX` | VMware_vCenter8 | replica | Proxmox3 | Rocky 9 | Replicate the pre-existing Rocky VM to Proxmox. |
| `VMWARE_OPENSUSE_16_PROXMOX` | VMware_vCenter8 | replica | Proxmox3 | openSUSE 16 | Replicate the pre-existing openSUSE VM to Proxmox. |
| `VMWARE_WS2022_PROXMOX` | VMware_vCenter8 | replica | Proxmox3 | Windows Server 2022 | Replicate the pre-existing Windows VM to Proxmox. |
| `VMWARE_UBUNTU_24_04_OLVM` | VMware_vCenter8 | replica | Oracle_LVM | Ubuntu 24.04 | Replicate the pre-existing Ubuntu VM to Oracle LVM. |
| `VMWARE_ROCKY_9_OLVM` | VMware_vCenter8 | replica | Oracle_LVM | Rocky 9 | Replicate the pre-existing Rocky VM to Oracle LVM. |
| `VMWARE_OPENSUSE_16_OLVM` | VMware_vCenter8 | replica | Oracle_LVM | openSUSE 16 | Replicate the pre-existing openSUSE VM to Oracle LVM. |
| `VMWARE_WS2022_OLVM` | VMware_vCenter8 | replica | Oracle_LVM | Windows Server 2022 | Replicate the pre-existing Windows VM to Oracle LVM. |
| `VMWARE_UBUNTU_24_04_LXD` | VMware_vCenter8 | replica | Microcloud_LXD | Ubuntu 24.04 | Replicate the pre-existing Ubuntu VM to Microcloud LXD. |
| `VMWARE_ROCKY_9_LXD` | VMware_vCenter8 | replica | Microcloud_LXD | Rocky 9 | Replicate the pre-existing Rocky VM to Microcloud LXD. |
| `VMWARE_OPENSUSE_16_LXD` | VMware_vCenter8 | replica | Microcloud_LXD | openSUSE 16 | Replicate the pre-existing openSUSE VM to Microcloud LXD. |
| `VMWARE_WS2022_LXD` | VMware_vCenter8 | replica | Microcloud_LXD | Windows Server 2022 | Replicate the pre-existing Windows VM to Microcloud LXD. |
| `VMWARE_UBUNTU_24_04_HARVESTER` | VMware_vCenter8 | replica | Harvester_Coriolis | Ubuntu 24.04 | Replicate the pre-existing Ubuntu VM to Harvester. |
| `VMWARE_ROCKY_9_HARVESTER` | VMware_vCenter8 | replica | Harvester_Coriolis | Rocky 9 | Replicate the pre-existing Rocky VM to Harvester. |
| `VMWARE_OPENSUSE_16_HARVESTER` | VMware_vCenter8 | replica | Harvester_Coriolis | openSUSE 16 | Replicate the pre-existing openSUSE VM to Harvester. |
| `VMWARE_WS2022_HARVESTER` | VMware_vCenter8 | replica | Harvester_Coriolis | Windows Server 2022 | Replicate the pre-existing Windows VM to Harvester. |

## Preliminary CIXpress Mapping

Reusable capabilities are a source checkout, a container build execution environment, ordered or parallel jobs, artifacts and logs, and parameterized test jobs. CIXpress could model an image-build job and a migration-test job, with the test job consuming explicit image and environment inputs.

For image migration, static Dockerfiles remain the general materialization method for other images: each role's checked-in `templates/Dockerfile.j2` is the source from which to initialize one static `<image-name>.dockerfile`, and CIXpress will build those files directly rather than render Ansible templates. The first `coriolis-oss` migration intentionally consolidates its common image and six service variants into one static unified Dockerfile. Materialization must resolve every Ansible expression and conditional explicitly, especially provider-dependent sections of `coriolis-worker`. The generated `coriolis_ansible/build/*.Dockerfile` files may be used as comparison output from a known legacy configuration, but they are temporary build artifacts rather than source files.

The existing packaging already supports this consolidation. The common Dockerfile copies and installs the complete `coriolis-oss` project, whose package metadata exposes every service console entry point. Conductor, scheduler, transfer-cron, minion-manager, and deployer-manager then inherit common and primarily select a different `CMD`; they do not copy separate service source trees. API is the exception because its derived image adds Apache, mod_wsgi, and `/start-apache.sh`. The legacy service images are therefore different runtime embodiments of one shared code image rather than independently packaged applications.

### Proposed `CoriolisOssBuild` Template

This is preliminary design, not implemented behavior. The initial `CoriolisOssBuild` output should be one unified runtime image for the first `coriolis-oss` migration, rather than seven images. Its eventual versioned artifact should be immutable. It would contain the complete `coriolis-oss` installation and all console entry points, Apache/mod_wsgi and `/start-apache.sh`, the common entrypoint preparation, and the applicable legacy common resources from core, replicator, and writer. Worker and provider-specific behavior remain deferred.

The same immutable image should eventually serve six Kubernetes workloads: API, conductor, scheduler, transfer-cron, minion-manager, and deployer-manager. Each workload would vary only `args`: API selects `/start-apache.sh`; messaging services select the relevant `/usr/local/bin/coriolis-*` executable. The image `ENTRYPOINT` must remain in effect. Kubernetes `command` replaces `ENTRYPOINT`, whereas using only `args` preserves the common CA, logging, optional `coriolis-dbsync`, and other entrypoint preparation. API also needs its Coriolis configuration, WSGI file, and Apache site configuration as mounted inputs.

Init containers may prepare shared-volume files and permissions or wait for dependencies, but cannot mutate the main container root filesystem and must not become the long-running service selector. Preliminary guidance is to run `coriolis-dbsync` in a dedicated Job using this same image rather than have every replica run migrations; this is not an implemented deployment behavior.

The likely prototype flow is to check out the dedicated Dockerfile/support repository, prepare the core, replicator, and writer sources, then perform one build-and-push step. That repository needs one static unified Dockerfile and support/preparation scripts, not seven core service Dockerfiles or Ansible templates. No Helm update or legacy cleanup is included: conductor is expected to remove its PVC when the pipeline reaches a terminal state. The existing Kaniko executor is Helm-coupled, so the new job manifest should use an image-native contract with explicit context, Dockerfile, and destination fields rather than `helm/values.yaml`; registry credentials remain Kubernetes secret references.

Initial packaging should be complete rather than selective. Root modules and the service chain are universally shared; component-owned directories coexist with subset-shared `db`, `tasks`, `taskflow`, `schemas`, `providers`, `keystone`, `cron`, and RPC-client areas. Dynamic loading further obscures the effective dependency graph. This is why selective packaging is unsafe initially, even before worker/provider support is included.

The prototype may initially publish only `:latest`; immutable/version tagging and promotion remain unresolved. `:latest` is prototype-only: concurrent runs can overwrite it and make results non-reproducible. Until tagging and promotion are designed, development-only runs should be serialized. Existing legacy publication automation and release promotion remain excluded, while the direct push of this one build output is allowed.

Gaps are material: CIXpress does not yet implement this migration; no pipeline, job definitions, runtime test configuration, appliance-equivalent image build environment, endpoint provisioning, source inventory, or cleanup contract has been mapped. The checked-in `coriolis-cd` orchestration must either remain an explicit dependency or be decomposed into CIXpress jobs before migration. Deployment and appliance lifecycle remain out of scope.

The provisional pilot is OpenStack-to-OpenStack replica testing with Ubuntu 22.04, Ubuntu 24.04, Rocky 9, openSUSE 16, and Windows Server 2022. Ubuntu 22.04 is historical; the other four guests derive from the active VMware-source suite. The current 20 selections cannot be copied directly because every source is VMware. Two OpenStack environments are documented, but source/destination endpoint assignment is TBD. Only Ubuntu 20.04 and Ubuntu 22.04 pre-existing OpenStack source VMs are documented, so the pilot needs source-VM preparation or a smaller initial matrix before it can cover the other guests.

## Facts, Assumptions, And References

Facts: the Jenkins call, `coriolis-cd` translation, build roles, generated files, handler behavior, and test runner behavior are checked-in code. The 20 selections are Jenkins build-548 observation. The CIXpress mapping and pilot are preliminary design inputs, not an implementation or validation claim.

Open questions: confirm the final image name, immutable tagging, and promotion model; identify the exact revisions and access method for replicator and writer sources; define API configuration delivery; decide whether external helper binaries are included before initial worker support; confirm the durable source for the Jenkins runtime configuration and exact identifier spelling before automation; assign the two documented OpenStack environments to source and destination roles; define how source VMs are created, retained, validated, and cleaned; and choose whether CIXpress should invoke `coriolis-cd` or directly implement its configuration and build orchestration.

Repository references:

| Subject | Source |
| --- | --- |
| Jenkins call chain and test-stage selection | `coriolis-ci/appliance/ci.groovy:23-108` |
| Standalone test selection and parallel execution | `coriolis-ci/appliance/tests.groovy:11-46` |
| Jenkins build command | `coriolis-ci/src/coriolis/ci/Appliance.groovy:88-134` |
| Build CLI arguments and release-tag input | `coriolis-cd/coriolis_cd/cli/build.py:13-113` |
| Remote configuration and Ansible invocation | `coriolis-cd/coriolis_cd/operations/coriolis_build.py:9-72` |
| Remote checkout and configuration helpers | `coriolis-cd/coriolis_cd/operations/common.py:11-59` |
| Runtime config validation and test execution/cleanup | `coriolis-ci/src/coriolis/ci/Appliance.groovy:324-359, 542-631` |
| Appliance role ordering | `coriolis-docker/coriolis_ansible/appliance.yml:8-87` |
| Common image inputs and rebuild conditions | `coriolis-docker/coriolis_ansible/roles/coriolis/common/tasks/build.yml:7-94` |
| Worker provider union and conditional inputs | `coriolis-docker/coriolis_ansible/roles/coriolis/worker/tasks/build.yml:7-78`; `coriolis-docker/coriolis_ansible/roles/coriolis/worker/templates/Dockerfile.j2:1-64` |
| Shared Docker build behavior | `coriolis-docker/coriolis_ansible/roles/common/docker/tasks/build_image.yml:2-20` |
| Coriolis console entry points | `coriolis-oss/setup.cfg:26-35` |
| Coriolis resource build | `coriolis-oss/setup.py:7-20` |
| Common image, entrypoint, and API Apache wrapper | `coriolis-docker/coriolis_ansible/roles/coriolis/common/templates/Dockerfile.j2:22-38`; `coriolis-docker/coriolis_ansible/roles/coriolis/common/templates/entrypoint.sh.j2:1-62`; `coriolis-docker/coriolis_ansible/roles/coriolis/api/templates/Dockerfile.j2:5-24`; `coriolis-docker/coriolis_ansible/roles/coriolis/common/templates/start-apache.sh.j2` |
| API container configuration mounts | `coriolis-docker/coriolis_ansible/roles/coriolis/api/templates/Dockerfile.j2:11-24`; `coriolis-docker/coriolis_ansible/roles/coriolis/api/tasks/setup_api_container.yml:11-17` |
| Service, RPC, and request-context chain | `coriolis-oss/coriolis/cmd/`; `coriolis-oss/coriolis/conductor/`; `coriolis-oss/coriolis/rpc.py`; `coriolis-oss/coriolis/context.py` |
| Schemas and package resources | `coriolis-oss/coriolis/schemas/`; `coriolis-oss/coriolis/resources/` |

External references:

- [New Coriolis environments](https://cloudbasedev.atlassian.net/wiki/spaces/CDS/pages/2706014209/New+Coriolis+environments)
- [Coriolis CI Testing prerequisites](https://cloudbasedev.atlassian.net/wiki/spaces/CDS/pages/3720577028/Coriolis+CI+Testing+prerequisites)
- [How to Run Tests in Jenkins Using the Coriolis CI Pipelines](https://cloudbasedev.atlassian.net/wiki/spaces/~628e01cfc65b72006961efae/pages/3394273282/How+to+Run+Tests+in+Jenkins+Using+the+Coriolis+CI+Pipelines)
