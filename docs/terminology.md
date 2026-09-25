# Terminology

!!! abstract
    Definitions for the current OpenStack-to-OpenStack Coriolis documentation path.

For component roles, see [Architecture](architecture.md). For the execution sequence, see [Migration Flow](migration-flow.md). For Kubernetes deployment and lifecycle, see [Coriolis Operator](architecture.md#coriolis-operator). For platform-specific behavior, see [Provider Preparation](openstack-provider.md).

## :material-book-open-page-variant-outline: Glossary

| Term | Definition |
| --- | --- |
| **Coriolis runtime** | The Coriolis migration services, supporting services, and configuration that run the product. The runtime performs migration work. |
| **`CoriolisAppliance`** | A namespaced Kubernetes custom resource watched by the Coriolis Operator. It declares a desired Kubernetes-hosted Coriolis runtime; the operator manages that runtime. |
| **Endpoint** | A provider connection and its environment-specific configuration. Endpoints identify where Coriolis reads source workloads or writes destination resources. |
| **Source environment** | The environment that contains the workload and disk data Coriolis reads. |
| **Destination environment** | The environment where Coriolis prepares transferred disk state and creates the destination VM. |
| **Provider plugin** | A platform-specific component that implements endpoint, export, and import operations. |
| **Migration** | A move workflow. A migration transfer prepares workload data for a move to the destination environment. |
| **Replica** | Destination disk state maintained by a replica transfer. A replica transfer can run again later to synchronize newer source data. |
| **Transfer** | An execution that copies or synchronizes workload disks between endpoints. Completing a transfer makes disk state available but does not create a destination VM. |
| **Deployment** | A separate execution that uses transferred disk state to prepare destination resources and create the destination VM. |
| **Worker service** | A Coriolis service that registers provider capabilities and runs migration tasks. |
| **Minion** | A pool-managed Worker service instance that Minion Manager allocates for a task. |
| **Minion pool** | A configured set of Minions from which Minion Manager allocates task capacity. |
| **Temporary worker VM** | An operation-scoped VM created directly by an OpenStack provider plugin for export, disk copy, or OS morphing. It is not necessarily a Minion. |
| **OS morphing** | Optional offline guest operating-system changes that adapt a disk for the destination environment during deployment. |
