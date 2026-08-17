# Coriolis

!!! abstract
    Coriolis supports migration of workloads between clouds and virtualization platforms. Its repository family separates the core product, container packaging, deployment delivery, and continuous-integration responsibilities.

## :material-book-open-page-variant-outline: How The Repositories Work Together

These repositories have different relationships; they are not a simple dependency graph. `coriolis-oss` supplies core Coriolis source that `coriolis-docker` can use while building service images. Other product repositories also contribute where needed.

```text
Runtime call hierarchy:
coriolis-ci
  -> coriolis-cd
       -> coriolis-docker
            -> Coriolis services and dependencies

Artifact progression:
Coriolis source -> container images and services -> appliance -> CI migration validation
```

`coriolis-ci` is Jenkins orchestration that invokes the `coriolis-cd` appliance delivery and deployment CLI. In turn, that CLI invokes `coriolis-docker` to build or deploy Coriolis service containers and their dependencies. `coriolis-cd` can also be used independently of CI.

## :material-book-open-page-variant-outline: Repository Roles

### :material-application-edit-outline: `coriolis-oss`

The open-source Coriolis product source repository. It contains the API, migration workflows, workers, schedulers, provider integrations, and control-plane services that perform and manage migrations.

### :material-application-edit-outline: `coriolis-docker`

Deployment automation for Coriolis. It builds container images, deploys Coriolis services, and deploys their dependencies. See [image build behavior and risks](image-builds.md). It uses upstream OpenStack Kolla and Kolla-Ansible for selected supporting services: Keystone, Barbican, RabbitMQ, and MariaDB. This is not a general-purpose OpenStack cloud deployment.

### :material-application-edit-outline: `coriolis-cd`

Appliance lifecycle and delivery tooling. Its CLI builds Coriolis components into appliance machines, deploys appliances, and supports appliance export, import, and test-machine operations.

### :material-application-edit-outline: `coriolis-ci`

Jenkins-based continuous integration. It provisions and configures appliances, deploys product components, runs migration tests, and collects results from complete workflows.

## :material-book-open-page-variant-outline: Kubernetes And Helm

No Kubernetes or Helm deployment support was found for the Coriolis product. The Helm chart at this repository's root deploys only this MkDocs documentation site.

## :material-book-open-page-variant-outline: Auxiliary Client

`python-coriolismetalhubclient` is an auxiliary Python client for bare-metal and Metal Hub integrations.
