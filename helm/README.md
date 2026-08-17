# Canonical Kubernetes Explorer Helm Chart

## Installation

```shell
helm install kubernetes-explorer-docs ./helm --namespace mkdocs
```

## Secret Management

### Keycloak/OIDC Client Secret

By default, the chart reads the client secret from `oauth2-proxy-mkdocs` using the `client-secret` key:

```yaml
proxy:
  keycloak:
    secret_name: oauth2-proxy-mkdocs
    client_secret_key: client-secret
```

### Cookie Secret

By default, the chart reads the cookie secret from `oauth2-proxy-mkdocs` using the `cookie-secret` key:

```yaml
proxy:
  cookie:
    secret_name: oauth2-proxy-mkdocs
    secret_key: cookie-secret
```

### Upgrade Safety

When `secret_name` is configured for a credential, the chart renders an explicit empty `value` alongside `valueFrom`. This ensures upgrades from legacy inline credentials are safe under Kubernetes strategic merge — the old inline value is cleared rather than lingering.

### Redis Session Store

The chart uses an existing Valkey instance for oauth2-proxy sessions. By default, it connects to `redis://valkey:6379` and reads the password from the `redis` Secret using the `password` key:

```yaml
proxy:
  redis:
    enabled: true
    connection_url: redis://valkey:6379
    secret_name: redis
    secret_key: password
```

Never commit real secrets to version control. Use Kubernetes Secrets or external secret management solutions.
