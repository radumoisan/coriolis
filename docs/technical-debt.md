# Technical Debt And Limitations

!!! abstract
    This register tracks documented operator-wide compromises, incomplete behavior, and validation gaps that affect deployment or migration use. It is an initial, evidence-backed working list rather than a general issue tracker.

## :material-book-open-page-variant-outline: Register

### :material-application-edit-outline: Production Scope Is Not Validated

**Current state:** Accepted evidence is limited to bounded development lifecycle, logging, and OpenStack-to-OpenStack migration walkthroughs. Production readiness remains unvalidated.

**Impact:** The operator and migration path cannot be represented as production-ready.

**Workaround:** Use the documented development scope and validate a controlled workload in the target cloud.

**Resolution or validation criterion:** Repeatable, production-oriented validation covers the outstanding operator and provider scope described in [Validation History](#validation-history), [Migration Flow](migration-flow.md#status-cleanup-and-validation), and [OpenStack Context](openstack-provider.md#cleanup-and-validation), including broader browser-flow, OpenStack provider, and API migration qualification.

### :material-application-edit-outline: Single-Replica Core Profile

**Current state:** The core profile uses fixed single replicas; HA, cross-node behavior, production storage, backup and restore, and multi-CR routing are unsupported or unvalidated.

**Impact:** The documented appliance profile has no validated high-availability, resilience, or multi-instance deployment claim.

**Workaround:** Use the bounded single-node development profile only.

**Resolution or validation criterion:** Supported topology, storage, backup and restore, and routing behavior are implemented and validated beyond the current bounded profile.

### :material-application-edit-outline: Upgrades Are Unsupported

**Current state:** The operator reports `Upgradeable=False`; upgrade behavior has no acceptance evidence.

**Impact:** Runtime or operator version changes cannot be treated as supported lifecycle operations.

**Workaround:** None is documented.

**Resolution or validation criterion:** Upgrade behavior is supported and accepted for the relevant version-change paths.

### :material-application-edit-outline: Drift Repair Is Intentionally Narrow

**Current state:** Reconciliation retries absent or empty status, collisions, and in-flight work, but is not a broad periodic drift self-healing loop.

**Impact:** Deleted or altered managed resources are not expected to be repaired by re-applying the custom resource.

**Workaround:** Follow the documented controlled recovery path; make CR recreation or operator resume a deliberate lifecycle decision and do not hand-edit operator-owned resources.

**Resolution or validation criterion:** Drift detection and repair behavior is implemented and validated for the intended managed-resource scope.

### :material-application-edit-outline: Standalone Helm Installation Is Unvalidated

**Current state:** The [operator guide](operator.md#helm-installation) documents an optional standalone Helm command, but it has no separate acceptance evidence. The command intentionally omits `--version`, so it resolves the latest published chart and can change as releases are published.

**Impact:** Standalone Helm installation is unvalidated and can deploy a different chart over time.

**Workaround:** Use the Argo CD-managed deployment documented for the validated development path.

**Resolution or validation criterion:** A standalone Helm operator installation, including latest-chart resolution behavior, is validated independently of the Argo CD-managed path.

### :material-application-edit-outline: Operator Guide Embedded YAML Can Drift

**Current state:** The [operator guide](operator.md#helm-installation) embeds copies of `coriolis-operator/helm/values.yaml`, `coriolis-operator/helm/crds/coriolisappliances.yaml`, and `docs/assets/manifests/coriolis-appliance.yaml`; the current MkDocs configuration has no automatic source inclusion.

**Impact:** Chart defaults, CRD schema, or appliance example can become stale after canonical source changes, especially because the standalone Helm command resolves the latest published chart.

**Workaround:** Compare displayed examples with the canonical source and selected chart before use or customization.

**Resolution or validation criterion:** Render examples from canonical sources or enforce automated synchronization or equality checks appropriate to all three embedded copies.

### :material-application-edit-outline: Licensing Backend Is Not Deployed

**Current state:** The core profile does not deploy a licensing backend or configure `LICENSING_SERVER_BASE_URL`; the Dashboard licence card receives HTML instead of a licensing API response.

**Impact:** The Current Licence card reports an error, and this configuration must not be generalized to licensed production deployments.

**Workaround:** Treat the licence-card error as expected in this development profile; it does not affect the documented login, endpoint, or migration flow.

**Resolution or validation criterion:** A licensing backend and conductor configuration provide the expected licensing API response in the applicable deployment profile.

### :material-application-edit-outline: Worker Privileges Are a Security Constraint

**Current state:** The operator-deployed Worker runs as root and privileged, with host mounts for `/dev` and `/lib/modules`.

**Impact:** The deployment has a significant operational security constraint and no production-security endorsement.

**Workaround:** None is documented.

**Resolution or validation criterion:** The deployment's privilege and host-access requirements are reduced or explicitly validated for the intended production-security posture.

## :material-book-open-page-variant-outline: Validation History

Accepted evidence covers operator 0.5.40 managing runtime 2603.4 through a bounded single-node core lifecycle and same-name recreation; Barbican-backed UI credentials, browser login, and browser-driven OpenStack-to-OpenStack migration in a bounded development proof of concept accepted on released operator 0.5.54; Kubernetes-native logging hardening accepted on 0.5.57; and the prior end-to-end walkthrough, now split across the [deployment](deploy-appliance.md), [headless migration](headless-migration.md), and [Web UI migration](web-ui-migration.md) pages, followed on release 0.5.59 with runtime 2603.4. This preserves prior evidence; the documentation split does not establish fresh runtime validation. None of this is a production-readiness result; broader production readiness across HA, storage, backup, upgrades, drift, and multi-CR routing remains open.

| Status label | Meaning | Current scope |
| --- | --- | --- |
| Implemented | Present in the operator. | Core profile reconciliation and its resource definitions, including the managed logging stack. |
| Validated | Tested with accepted evidence. | Managed resource reconciliation and lifecycle behavior for dependencies, Coriolis services, and Ingress, including collision safety and normal cleanup. |
| Validated, bounded | Tested only within a stated limit. | Single-node `Ready=True` and retained-state recreation on 0.5.40; a development Web UI OpenStack-to-OpenStack migration proof of concept on 0.5.54; logging hardening on 0.5.57; the prior walkthrough now split across the [deployment](deploy-appliance.md), [headless migration](headless-migration.md), and [Web UI migration](web-ui-migration.md) pages, followed end to end on 0.5.59 with runtime 2603.4. |
| In progress | Work with partial evidence not yet accepted end to end on the current release. | Direct Helm operator installation is not separately validated: the [operator guide](operator.md#helm-installation) documents an optional standalone install that resolves the latest published chart, while only the Argo CD-managed live development path in the [operator lab environment](operator-lab-environment.md#operator-installation) is validated. |
| Pending | Planned work without acceptance evidence. | Broader, repeatable, production-oriented browser-flow, OpenStack provider, and API migration qualification beyond the bounded 0.5.54 development proof of concept and the bounded 0.5.59 prior walkthrough. |
| Unsupported/unvalidated | Not supported as a public readiness claim. | Production HA, storage, backup, upgrades, drift self-healing, and multi-CR routing. |

## :material-book-open-page-variant-outline: Maintenance Rule

Add an entry only when current documentation supports an operator-wide compromise, incomplete behavior, or validation gap. Keep essential operational warnings in their procedure pages, and keep stable component or API reference material in its reference page unless it creates one of those tracked gaps.
