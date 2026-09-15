# Technical Debt And Limitations

!!! abstract
    This register tracks documented operator-wide compromises, incomplete behavior, and validation gaps that affect deployment or migration use. It is an initial, evidence-backed working list rather than a general issue tracker.

## :material-book-open-page-variant-outline: Register

### :material-application-edit-outline: Production Scope Is Not Validated

**Current state:** Accepted evidence is limited to bounded development lifecycle, logging, and OpenStack-to-OpenStack migration walkthroughs. Production readiness remains unvalidated.

**Impact:** The operator and migration path cannot be represented as production-ready.

**Workaround:** Use the documented development scope and validate a controlled workload in the target cloud.

**Resolution or validation criterion:** Repeatable, production-oriented validation covers the outstanding operator and provider scope described in [Coriolis Operator](operator.md#limits-and-next-work), [Migration Flow](migration-flow.md#status-cleanup-and-validation), and [OpenStack Context](openstack-provider.md#cleanup-and-validation).

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

**Current state:** The [advanced tutorial](operator-advanced-tutorial.md#optional-standalone-helm-installation) documents an optional standalone Helm command, but it has no separate acceptance evidence. The command intentionally omits `--version`, so it resolves the latest published chart and can change as releases are published.

**Impact:** Standalone Helm installation is unvalidated and can deploy a different chart over time.

**Workaround:** Use the Argo CD-managed deployment documented for the validated development path.

**Resolution or validation criterion:** A standalone Helm operator installation, including latest-chart resolution behavior, is validated independently of the Argo CD-managed path.

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

## :material-book-open-page-variant-outline: Maintenance Rule

Add an entry only when current documentation supports an operator-wide compromise, incomplete behavior, or validation gap. Keep essential operational warnings in their procedure pages, and keep stable component or API reference material in its reference page unless it creates one of those tracked gaps.
