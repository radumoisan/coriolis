# Coriolis

!!! abstract
    Coriolis is a workload migration product. This documentation initially focuses on OpenStack-to-OpenStack migrations.

## :material-book-open-page-variant-outline: What Coriolis Does

Coriolis provides a Web UI and API for defining endpoints, transfers, and deployments. Its control services coordinate work, Worker services run migration tasks, and provider plugins implement platform-specific operations.

The Kubernetes operator is separate from the migration product. It reconciles a `CoriolisAppliance` resource into a Kubernetes-hosted Coriolis runtime and its dependencies; it does not replace the product's migration services.

## :material-book-open-page-variant-outline: Current Scope

OpenStack is the initial documentation focus. OpenStack provider plugins implement source export and destination import operations.

!!! warning
    One bounded actual-browser Web UI OpenStack-to-OpenStack migration proof of concept has passed on released operator 0.5.54 in the development environment. The [Advanced Operator Tutorial](operator-advanced-tutorial.md) walkthrough has since been followed end to end on operator 0.5.59 with runtime 2603.4. This is bounded development evidence only; all production-readiness claims remain unvalidated.

## :material-book-open-page-variant-outline: Architecture

Learn how the product services, provider plugins, supporting services, and Kubernetes operator fit together in the [Coriolis Architecture](architecture.md).

Follow the [Migration Flow](migration-flow.md) from endpoint definition through separate transfer and deployment executions.

See the [Coriolis Operator](operator.md) for its Kubernetes lifecycle scope, validated boundaries, and current limitations.

For a hands-on walkthrough from appliance bring-up through a Web UI migration, follow the validated-on-0.5.59 [Advanced Operator Tutorial](operator-advanced-tutorial.md).

Prepare the two-cloud prerequisites described in the [OpenStack Context](openstack-provider.md), and use the focused [Terminology](terminology.md) when terms need clarification.
