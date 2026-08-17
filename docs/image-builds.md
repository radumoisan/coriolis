# Coriolis Image Builds

!!! abstract
    This page records the observed Coriolis and Kolla image build paths, their source boundaries, publishing behavior, and verified risks.

## :material-book-open-page-variant-outline: Build Hierarchy And Families

```text
coriolis-ci
  -> coriolis-cd
       -> SSH to appliance VM
            -> coriolis-ansible bootstrap
            -> coriolis-ansible build
                 -> coriolis-docker (Docker builds)
  -> coriolis-ansible push-docker-images (may run later)
```

`coriolis-cd` prepares remote configuration, handles registry login, uploads a temporary Bitbucket SSH key, and delegates the build to `coriolis-docker`. It does not itself run Docker builds.

### :material-application-edit-outline: Coriolis Application Images

The product images are built by `coriolis-docker`. `coriolis-common`, based on `ubuntu:22.04`, is the shared base for API, conductor, transfer cron, scheduler, minion manager, deployer manager, and worker. Independent images are compressor, logger, web, web proxy, console editor, Metal Hub, licensing server, and licensing UI.

Image names and tags are registry- and namespace-configurable. Observed defaults were `registry.cloudbase.it/appliance/<image>:latest`.

| Image | Base image or relationship | Source/build input | Purpose |
| --- | --- | --- | --- |
| `coriolis-common` | `ubuntu:22.04` | Public Coriolis core plus private replicator and writer binaries | Shared Coriolis service base |
| `coriolis-api` | Depends on `coriolis-common` | Coriolis service source and rendered Dockerfile | API service image |
| `coriolis-conductor` | Depends on `coriolis-common` | Coriolis service source and rendered Dockerfile | Conductor service image |
| `coriolis-transfer-cron` | Depends on `coriolis-common` | Coriolis service source and rendered Dockerfile | Transfer cron service image |
| `coriolis-scheduler` | Depends on `coriolis-common` | Coriolis service source and rendered Dockerfile | Scheduler service image |
| `coriolis-minion-manager` | Depends on `coriolis-common` | Coriolis service source and rendered Dockerfile | Minion-manager service image |
| `coriolis-deployer-manager` | Depends on `coriolis-common` | Coriolis service source and rendered Dockerfile | Deployer-manager service image |
| `coriolis-worker` | Depends on `coriolis-common` | Selected union of export/import provider repositories; selected Metal Hub client; `libqemu` | Worker service image |
| `coriolis-compressor` | Independent | Compressor source and rendered Dockerfile | Compressor image |
| `coriolis-logger` | Independent | Logger source and Dockerfile | Logger image |
| `coriolis-web` | Independent | Web source and rendered Dockerfile | Web image |
| `coriolis-web-proxy` | Independent | Rendered proxy startup script and Dockerfile | Web-proxy image |
| `coriolis-console-editor` | Independent | Generated tools and Python client dependency | Console-editor image |
| `coriolis-metal-hub` | Independent | Metal Hub source and rendered Dockerfile | Metal Hub image |
| `coriolis-licensing-server` | Independent | Licensing-server source and rendered Dockerfile | Licensing-server image |
| `coriolis-licensing-ui` | Independent | Licensing-UI source and rendered Dockerfile | Licensing UI image |

!!! note
    Build inputs may be cloned from public GitHub or private Bitbucket sources. A published image can include private components, but local source inspection cannot establish the contents of a particular registry image.

### :material-application-edit-outline: Upstream OpenStack Kolla Images

Kolla images are a separate build family. `kolla/build.sh` installs upstream Kolla from Git and runs `kolla-build` for Keystone, Barbican, RabbitMQ, MariaDB, Kolla Toolbox, cron, and Memcached. Their deployment is separate from the build and consumes images through Kolla-Ansible.

## :material-book-open-page-variant-outline: Observed Build And Publishing Behavior

### :material-application-edit-outline: Build Mechanics

1. Configuration is generated or loaded.
2. Build sources are cloned or updated.
3. Dockerfiles are rendered from Jinja templates.
4. The local tag is checked for existence.
5. A handler removes and rebuilds the image when needed.
6. Image publication is a separate push action.

The tag-local existence check means a local image can be reused before the rebuild handler runs. The existing remote `coriolis-docker` checkout is not updated as part of the observed path.

### :material-application-edit-outline: Credentials And Publishing

Registry authentication is used for Docker operations, and Bitbucket SSH access is used for private build inputs. The observed automation passes the registry password on the command line, accepts SSH host keys automatically, and attempts to remove the temporary Bitbucket key; removal is not guaranteed if the workflow fails.

`coriolis-ansible push-docker-images` is separate from image construction. Its observed push list does not cover every built image: Metal Hub and licensing UI are absent, and licensing server is commented out. Default tags are mutable `latest`. The Kolla build script has no equivalent explicit local push list.

## :material-book-open-page-variant-outline: Verified Risks

!!! warning
    The following are observed conditions, not a proposed implementation plan.

- Mutable `master` and `latest` references can change without a build-definition change.
- Base images, packages, and Git dependencies are unpinned.
- The build does not record provenance.
- Tag-local existence checks can reuse a stale image.
- The existing remote `coriolis-docker` checkout is not updated.
- The registry password is passed on the command line.
- SSH host-key acceptance is automatic.
- Temporary Bitbucket-key removal is not guaranteed on failure.
- The Kolla build configuration uses `2023.1`, while deployment takes its release setting from a tag; these can diverge.
- The licensing UI uses outdated Node 11.
- The logger Dockerfile copies source and defaults to a shell, with no visible compile or start step.
- Generated configuration files are ignored.

## :material-book-open-page-variant-outline: Questions Before Changing The Pipeline

- Which images are authoritative for each deployment path?
- What do the published registry images actually contain?
- What immutable version and tag source should identify an image?
- Which Kolla and OpenStack versions must be pinned together?
- Which inputs and artifacts belong in the public versus private build and distribution boundary?
- Are the incomplete images and the incomplete push list intentional?
