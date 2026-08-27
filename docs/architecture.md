# Coriolis Architecture

!!! abstract
    Coriolis combines a migration control plane, Worker services, provider plugins, and supporting services. The Kubernetes operator can deploy this runtime, but is not part of the migration control plane.

## :material-book-open-page-variant-outline: Conceptual View

This diagram shows product roles rather than detailed RPC or network paths.

```text
User
  |
Web UI
  |
Coriolis API
  |
Migration control services ---- Worker services ---- Provider plugins
  |                                               |
  +-- Conductor, Scheduler, Transfer Cron,         +-- Source OpenStack
      Minion Manager, Deployer Manager             +-- Destination OpenStack

Supporting services: Keystone | RabbitMQ | MariaDB | Memcached

Kubernetes operator -> deploys and reconciles the Coriolis runtime
```

## :material-book-open-page-variant-outline: Migration Product

| Component | Role |
| --- | --- |
| Web UI | Browser interface for endpoints, transfers, deployments, and minion pools. |
| API | WSGI service that exposes the Coriolis API. |
| Conductor | Coordinates product operations and work across the control services. |
| Scheduler | Selects compatible Worker services using provider requirements and region information. |
| Transfer Cron | Registers schedules and triggers scheduled transfer task execution. |
| Minion Manager | Manages minion pools and their scheduled refresh work. |
| Deployer Manager | Starts automatic deployments and monitors pending deployment work. |
| Worker service | Registers available providers and capabilities, then runs migration tasks. |
| Provider plugins | Implement platform-specific endpoint operations, including source export and destination import. The initial focus is the OpenStack provider. |

## :material-book-open-page-variant-outline: Supporting Services

| Service | Role |
| --- | --- |
| Keystone | Provides identity services for the runtime. |
| RabbitMQ | Provides the messaging service used by the control-plane components. |
| MariaDB | Stores persistent runtime data. |
| Memcached | Provides caching support for the runtime. |

## :material-book-open-page-variant-outline: Kubernetes Operator

The [Coriolis Operator](operator.md) deploys and reconciles the Coriolis runtime in Kubernetes. Its page covers lifecycle behavior, validation status, and limits.
