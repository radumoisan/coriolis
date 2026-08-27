# Coriolis

!!! abstract
    Coriolis is a workload migration product. This documentation initially focuses on OpenStack-to-OpenStack migrations.

## :material-book-open-page-variant-outline: What Coriolis Does

Coriolis provides a Web UI and API for defining endpoints, transfers, and deployments. Its control services coordinate work, Worker services run migration tasks, and provider plugins implement platform-specific operations.

The Kubernetes operator is separate from the migration product. It reconciles a `CoriolisAppliance` resource into a Kubernetes-hosted Coriolis runtime and its dependencies; it does not replace the product's migration services.

## :material-book-open-page-variant-outline: Current Scope

OpenStack is the initial documentation focus. OpenStack provider plugins implement source export and destination import operations.

!!! warning
    End-to-end OpenStack-to-OpenStack migration validation remains pending. This documentation describes the implemented architecture, not a production-readiness claim.

## :material-book-open-page-variant-outline: Architecture

Learn how the product services, provider plugins, supporting services, and Kubernetes operator fit together in the [Coriolis Architecture](architecture.md).

Follow the [Migration Flow](migration-flow.md) from endpoint definition through separate transfer and deployment executions.

See the [Coriolis Operator](operator.md) for its Kubernetes lifecycle scope, validated boundaries, and current limitations.

Prepare the two-cloud prerequisites described in the [OpenStack Context](openstack-provider.md), and use the focused [Terminology](terminology.md) when terms need clarification.
