---
name: cixpress-pipeline-monitor
description: Use ONLY when identifying, monitoring, checking status or logs, or troubleshooting CIXpress pipelines in the approved dev environment; it enforces polling-only, read-only observation.
---

# CIXpress Pipeline Monitor

Use this skill only for approved CIXpress pipeline observation in `virt-infra-dev-buc-hq`. The human-facing companion is `coriolis-operator/docs/cixpress-monitoring.md`; all critical safety requirements are repeated here.

## Safety Rules

- Always use `kubectl --context virt-infra-dev-buc-hq -n cixpress` explicitly.
- Use authorized Kubernetes exec to query the internal conductor URL `http://localhost:5000`: ingress may require deployment-specific authentication. This relies on Kubernetes authorization; never bypass Kubernetes authorization or inspect credentials.
- Allow only GET requests to `/healthz/ready`, `/pipelines`, `/pipelines/{pipeline_id}`, and `/pipelines/{pipeline_id}/logs`.
- Never use SSE or `/stream`. Polling is the only monitoring mechanism.
- Never trigger a pipeline, use `/clear`, write configuration, issue POST/PUT/PATCH/DELETE, mutate Kubernetes, inspect Secrets or credentials, port-forward, deploy into `cixpress`, or output raw sensitive logs.
- Do not report HTTP 202 as success.

## Preflight

Require local `/usr/bin/jq` 1.6 and in-container `/usr/bin/curl`. Stop if either is unavailable; do not install tools.

```sh
/usr/bin/jq --version
kubectl --context virt-infra-dev-buc-hq -n cixpress exec deployment/conductor -c conductor -- /usr/bin/curl --version
```

For each new list/discovery session, use a fresh unique agent because filters persist by derived session:

```sh
kubectl --context virt-infra-dev-buc-hq -n cixpress exec deployment/conductor -c conductor -- /usr/bin/curl -fsS -H "User-Agent: cixpress-pipeline-monitor-$(date +%s%N)" http://localhost:5000/healthz/ready
```

## Discovery And Identification

Use this exact list normalization; `/pipelines` is documented as a pipeline-ID map but runtime may return a list with `id`:

```sh
kubectl --context virt-infra-dev-buc-hq -n cixpress exec deployment/conductor -c conductor -- /usr/bin/curl -fsS -H "User-Agent: cixpress-pipeline-monitor-$(date +%s%N)" "http://localhost:5000/pipelines?itemsPerPage=200&startIdx=0" |
  /usr/bin/jq '[if type == "object" then to_entries[] | {id: (.value.id // .key), templateName: .value.templateName, head_id: (.value.head.id // null), state: .value.state, start_time: .value.start_time, completion_time: .value.completion_time} else .[] | {id, templateName, head_id: (.head.id // null), state, start_time, completion_time} end] |
    sort_by(.start_time // "") | reverse'
```

Select in this precedence: explicit ID, exact commit SHA, then a unique commit prefix plus template and time. Sort by `start_time` explicitly because observed descending order is not guaranteed. Repository/branch filters are not guaranteed. Never guess if ambiguous.

Replace `<pipeline-id>` with a candidate only, then validate it before interpolation. Stop on failure:

```sh
pipeline_id='<pipeline-id>'
if ! [[ "$pipeline_id" =~ ^[A-Za-z0-9]{6}$ ]]; then
  printf '%s\n' 'invalid pipeline ID; stopping' >&2
  exit 1
fi
```

## Detail And Polling

`/pipelines/{id}` returns an ID-keyed object or `{}`. Normalize object/array steps:

```sh
kubectl --context virt-infra-dev-buc-hq -n cixpress exec deployment/conductor -c conductor -- /usr/bin/curl -fsS -H "User-Agent: cixpress-pipeline-monitor-$(date +%s%N)" "http://localhost:5000/pipelines/<pipeline-id>" |
  /usr/bin/jq --arg id '<pipeline-id>' 'if has($id) then .[$id] | {id: (.id // $id), templateName, head_id: (.head.id // null), state, start_time, completion_time, steps: [(.steps // []) | if type == "object" then to_entries[] | {name: (.value.name // .key), identifier: .value.identifier, state: .value.state, start_time: .value.start_time, completion_time: .value.completion_time} else .[] | {name: (.name // .identifier), identifier, state, start_time, completion_time} end]} else {id: $id, error: "pipeline not found"} end'
```

Run individual bounded GET polls every 15 seconds, maximum 20 polls (five minutes) unless the user requests another bound. Compare consecutive states, report transitions, and stop at terminal state. Never use an infinite loop.

Expected operator steps: `git-clone`, `kaniko-build`, `helm-update`, `cleanup`. Pipeline success requires each expected step to be `SUCCEEDED`. If the top-level state exists but steps are empty, report that state and unavailable per-step confirmation. `INPROGRESS` with `completion_time`, or other contradictions, means stale/inconsistent data. Missing Jobs or steps can result from cleanup, not success. Observed pipeline states: `SUCCEEDED`, `FAILED`, `INPROGRESS`; OpenAPI step states: `NOT_STARTED`, `STARTED`, `FAILED`, `SUCCEEDED`.

## Logs

Only inspect the active, failed, or user-requested step. Request metadata/line counts first, with zero-based offset and URL-encoded parameters:

```sh
kubectl --context virt-infra-dev-buc-hq -n cixpress exec deployment/conductor -c conductor -- /usr/bin/curl -fsS -G -H "User-Agent: cixpress-pipeline-monitor-$(date +%s%N)" --data-urlencode 'step=<step>' --data-urlencode 'offset=0' "http://localhost:5000/pipelines/<pipeline-id>/logs" |
  /usr/bin/jq --arg pipeline_id '<pipeline-id>' --arg step '<step>' '{pipeline_id: $pipeline_id, step: $step, streams: [(.logs // {}) | to_entries[] | {stream: .key, lines: (.value | length)}]}'
```

The response contains a `.logs` stream-to-lines map. Replace placeholders only after ID validation and selection. If an excerpt is necessary, use this optional best-effort transformation only after metadata inspection; it emits at most the last 40 lines per stream and redacts likely bearer, authorization, token, password, secret, API-key, JWT, and URL-userinfo values:

```sh
kubectl --context virt-infra-dev-buc-hq -n cixpress exec deployment/conductor -c conductor -- /usr/bin/curl -fsS -G -H "User-Agent: cixpress-pipeline-monitor-$(date +%s%N)" --data-urlencode 'step=<step>' --data-urlencode 'offset=0' "http://localhost:5000/pipelines/<pipeline-id>/logs" |
  /usr/bin/jq --arg pipeline_id '<pipeline-id>' --arg step '<step>' '
    def redact:
      gsub("(?i)(?<prefix>bearer[[:space:]]+)[^[:space:],;]+"; "\(.prefix)[REDACTED]") |
      gsub("(?i)(?<prefix>(?:authorization|auth|token|password|secret|api[-_ ]?key)[[:space:]]*[:=][[:space:]]*)[^[:space:],;]+"; "\(.prefix)[REDACTED]") |
      gsub("(?i)(?<prefix>https?://)[^/@[:space:]]+@"; "\(.prefix)[REDACTED]@") |
      gsub("(?i)\\b[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+\\b"; "[REDACTED_JWT]");
    {pipeline_id: $pipeline_id, step: $step, streams: [(.logs // {}) | to_entries[] |
      {stream: .key, lines: [(.value | if type == "array" then .[-40:] else [] end)[] |
        if type == "string" then redact else "[NON_STRING_LINE]" end]}]}'
```

This redaction is best-effort. If safe redaction is uncertain, return metadata only; never execute the excerpt command against live logs without that determination. Summarize rather than reproduce output. Offsets are partially guaranteed only: a 12-line single stream returned zero lines at offset 12. Do not claim cross-stream completeness; track and report offsets conservatively.

## Kubernetes Job Fallback

Jobs are secondary read-only evidence. Match names ending in `-job-<pipeline-id>`; no Job can mean cleanup:

```sh
kubectl --context virt-infra-dev-buc-hq -n cixpress get jobs -o name | /usr/bin/jq -R -r --arg id '<pipeline-id>' 'select(endswith("-job-" + $id))'
```

## Report Format

Report selection evidence, pipeline ID, template, commit, start/completion times, top-level state, expected-step states, transitions, poll count, and step-confirmation availability. For logs report the requested step, HTTP outcome, stream count, line counts, offsets, and only a safely redacted bounded summary. State uncertainty rather than infer success or root cause.
