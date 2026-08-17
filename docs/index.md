# Coriolis

!!! abstract
    Coriolis supports migration of workloads between clouds and virtualization platforms. Its repository family separates the core product, container packaging, deployment delivery, and continuous-integration responsibilities.

## :material-book-open-page-variant-outline: Repository Flow

The high-level flow moves from product source to packaged runtime, deployment delivery, and validation:

`coriolis-oss` -> `coriolis-docker` -> `coriolis-cd` -> `coriolis-ci`

The CI repository also exercises the deployment and appliance tooling as part of end-to-end validation.

## :material-book-open-page-variant-outline: Repository Roles

### :material-application-edit-outline: `coriolis-oss`

The open-source Coriolis product source repository. It contains the API, migration workflows, workers, schedulers, provider integrations, and control-plane services that perform and manage migrations.

### :material-application-edit-outline: `coriolis-docker`

Deployment automation for Coriolis. It builds container images, deploys the Coriolis services, and configures supporting infrastructure such as the OpenStack services used by the control plane.

### :material-application-edit-outline: `coriolis-cd`

Appliance lifecycle and delivery tooling. Its CLI builds Coriolis components into appliance machines, deploys appliances, and supports appliance export, import, and test-machine operations.

### :material-application-edit-outline: `coriolis-ci`

Jenkins-based continuous integration. It provisions and configures appliances, deploys product components, runs migration tests, and collects results from complete workflows.

## :material-book-open-page-variant-outline: Auxiliary Client

`python-coriolismetalhubclient` is an auxiliary Python client for bare-metal and Metal Hub integrations.
