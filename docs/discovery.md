# Coriolis Discovery

!!! abstract
    This in-progress, evidence-based map supports an OVA-first newcomer path. It is not a finalized architecture, installation guide, or tutorial.

## :material-book-open-page-variant-outline: Repository Landscape

The root repository contains this MkDocs site and its own Helm chart only. It is not the product deployment repository.

- `coriolis-oss` is the core application source.
- `coriolis-docker` contains Docker and Ansible build/deployment work.
- `coriolis-cd` supplies CD and appliance/configuration tooling.
- `coriolis-ci` orchestrates Jenkins builds and validation.
- `python-coriolismetalhubclient` is an auxiliary Metal Hub client.

The relationships are non-linear: CI invokes CD/configuration, Docker/Ansible consumes source inputs, and individual images use additional dependencies. These repositories are not a single linear stack.

## :material-book-open-page-variant-outline: Observed Appliance Workflow

The following is an observed VMware appliance workflow, not proof of a clean Ubuntu 22.04 installation:

1. Start from a VMware base template.
2. Pull the tools image.
3. Use CD/configuration tooling.
4. Build Coriolis images through Docker/Ansible.
5. Deploy Kolla dependencies.
6. Configure the appliance.
7. Export an OVA.
8. Import the OVA.
9. Validate a migration.

Evidence: [appliance setup build](http://10.8.1.121:8080/job/1_coriolis-appliance-setup/860/) and [CI build 1395](http://10.8.1.121:8080/job/coriolis-ci/1395/).

## :material-book-open-page-variant-outline: Current First Path

The first target is a published appliance with a VMware source, OpenStack destination, and one minimal Linux VM. It initially excludes Jenkins and source/image builds. OpenStack-to-OpenStack and a clean Ubuntu 22.04 host path are deferred, not disproven.

## :material-book-open-page-variant-outline: Appliance Publication

Publication base: `http://10.8.1.121/appliances/`

Recommended fixed candidate: `coriolis-appliance-2608.0-rc2.ova`

- OVA: `http://10.8.1.121/appliances/coriolis-appliance-2608.0-rc2.ova`
- SHA-256 sidecar: `http://10.8.1.121/appliances/coriolis-appliance-2608.0-rc2.ova.sha256sum`
- SHA-256: `33ce5b8d0ca3c35b95bd8da11842eb8193fee68706cfd182ae8a11e1831a347d`
- Size: about 9.57 GB.

Final `2608.0` was not present during research. `coriolis-appliance-latest.ova` is mutable. OVAs are external publication artifacts, not Jenkins archived artifacts.

!!! warning
    Verify the downloaded OVA against the SHA-256 above. Do not use `latest` for a repeatable exercise.

## :material-book-open-page-variant-outline: Deployment And Images

Application deployment uses Docker/Ansible. Kolla/Kolla-Ansible supplies selected support services. No product Helm or Kubernetes artifacts were found.

Successful Jenkins setup evidence uses private `registry.cloudbase.it`, the `appliance` namespace, `kolla_branch: 2023.1-eol`, `kolla_openstack_release: 2023.1`, and Kolla tag `2023.1`. Observed private Kolla image families are Barbican API, Barbican Keystone listener, Barbican worker, cron, fluentd, Kolla toolbox, and RabbitMQ tagged `2023.1-ubuntu-jammy`. Keystone, MariaDB/Galera, Memcached, InfluxDB, and Step CA were configured/deployed, but their complete image names were not observed.

Application and dependency digests are not yet inventoried. The desired public-image design is not Jenkins-validated because Jenkins used the private namespace. The registry was reachable over TLS, but supplied authentication returned `401` without a challenge; private registry image availability is therefore not confirmed.

Local source shows public build/runtime inputs of Ubuntu 22.04, Go Alpine, Node 18, Step CA latest, and InfluxDB 1.7. Mutable references must be pinned for a source build.

## :material-book-open-page-variant-outline: Future Build Version Evidence

| Component | Requested ref | Observed resolved commit |
| --- | --- | --- |
| Stable pipeline Docker | `stable/2608` | Not observed |
| Core | `master` | Not observed |
| OpenStack provider | `1.2.9` | Not observed |
| VMware provider | `1.2.4` | `591a34d0b75391138a2cc2c928f5e54b6f70e834` |
| Replicator | `1.0.5` | Not observed |
| Writer | `1.0.4` | Not observed |
| Logger | `1.0.5` | Not observed |
| Web | `1.8.1` | Not observed |
| Python client | `1.2.5` | Not observed |
| Metal Hub client | `1.0.1` | Not observed |
| CI build | N/A | `0a38d27b3cb7bcd80b719ca9062b0ea44ec64242` |
| Kolla-Ansible | N/A | `2714e566e2f5a284a0b994d0b9b034ff08c8292a` |

These are requested refs; most resolved commits were not observed. No exact provider commit is asserted where it was not observed.

## :material-book-open-page-variant-outline: Provider Scope

The immediate scope is VMware export and OpenStack import only. VHI and Metal Hub are not on this path. `coriolis_provider_vhi` remains referenced in local configuration, but was not observed in Jenkins or OpenStack provider CI and requires no action unless it blocks the target path. The worker build unconditionally clones the Metal Hub client, but it is not part of the OVA-first path.

## :material-book-open-page-variant-outline: Logger And Libqemu

The logger image is a Go build environment that builds a static host binary run by systemd; its shell `CMD` is intentional. `libqemu.so.gz` is downloaded from `https://cloudbase.it/downloads/libqemu.so.gz`, with no configured Ansible checksum pin. Jenkins observed SHA-1 `46de5b0c05b3123a89a6eac8795813073708774b`; SHA-1 is not adequate provenance or pinning control and this does not verify the file.

## :material-book-open-page-variant-outline: Migration Evidence

Current Jenkins examples validated OLVM-to-OpenStack in CI build 1395. Historical tests covered VMware-to-LXD, VMware-to-Proxmox, and VMware-to-CloudStack. No recent validated OpenStack-to-OpenStack test was found. VMware-to-OpenStack is common and supported by observed provider configuration, but still needs its first controlled test.

## :material-book-open-page-variant-outline: Confirmed Gaps

- OVA import instructions and appliance default credentials, networking, DNS, and TLS.
- Appliance host sizing.
- Exact endpoint, permission, and quota requirements.
- Registry authentication and image availability.
- Source dependency closure and digests.
- Public-equivalent Kolla images.
- The first controlled VMware-to-OpenStack test.

No public/community product deployment artifact was found; the internal OVA publication endpoint is available.

## :material-book-open-page-variant-outline: Next Gates

1. Verify the RC2 download and SHA-256 checksum.
2. Determine VMware import requirements and appliance sizing.
3. Determine initial appliance access, networking, DNS, and TLS.
4. Configure VMware and OpenStack endpoints.
5. Migrate one minimal Linux VM.
6. Validate the result and capture cleanup steps.
7. Separately resolve private Git/registry source-build closure.
