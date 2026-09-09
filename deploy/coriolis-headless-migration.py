#!/usr/bin/env python3
"""Tutorial helper that runs one parameterized Coriolis live migration.

The source and destination endpoints are expected to already exist (they
are created and validated through the Coriolis Web UI). The '--api-base'
and '--keystone-base' arguments must be the externally reachable Coriolis
v1 and Keystone v3 bases (for example the public ingress paths
'https://host/coriolis' and 'https://host/identity', or direct service
URLs ending in '/v1' and '/v3'); the helper appends only the remaining
resource paths and never duplicates version segments. This helper only:

1. Authenticates to the appliance Keystone with the 'coriolis' service
   user in the 'service' project. The password is read from stdin and is
   never printed or stored beyond the single authentication request.
2. Preflights the configured endpoint IDs and transfer uniqueness.
3. Creates one Transfer and starts one execution.
4. Polls the exact execution to a terminal state and, when
   'auto_deploy' is set, discovers and polls the single correlated
   deployment.

Nothing is cleaned up: the created objects remain visible in the Web UI
for observation and the documented manual cleanup flow. Only fixed,
safe messages are printed (never tokens, payloads, or error bodies).
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Iterator, List, Optional, Sequence, Set, Tuple

HTTP_REQUEST_TIMEOUT: int = 30
DEFAULT_TIMEOUT: int = 1800
DEFAULT_POLL_INTERVAL: int = 10
# GET-only polling reads may tolerate a small number of consecutive
# transient network failures before giving up. POST/write requests and
# non-network API errors are never retried.
MAX_CONSECUTIVE_NETWORK_ERRORS: int = 3

PLACEHOLDER_PATTERN = re.compile(r"<[^<>]*>")

TERMINAL_SUCCESS_STATUS: str = "COMPLETED"
TERMINAL_FAILURE_STATUSES = frozenset({
    "ERROR",
    "CANCELED",
    "CANCELLED",
    "DEADLOCKED",
    "ERROR_ALLOCATING_MINIONS",
    "CANCELED_FOR_DEBUGGING",
})

ALLOWED_TOP_LEVEL_KEYS: Set[str] = {"transfer", "execution"}
TRANSFER_KEYS: Set[str] = {
    "notes", "scenario", "origin_endpoint_id", "destination_endpoint_id",
    "instances", "source_environment", "destination_environment",
    "network_map", "storage_mappings", "clone_disks", "skip_os_morphing",
}
EXECUTION_KEYS: Set[str] = {"shutdown_instances", "auto_deploy"}

EXIT_OK: int = 0
EXIT_FAILURE: int = 1
EXIT_CONFIG_ERROR: int = 2


class MigrationError(Exception):
    """A failure described by a fixed safe category and HTTP status."""

    def __init__(self, category: str, http_status: object = "none") -> None:
        super().__init__(category)
        self.category: str = category
        self.http_status: object = http_status


def emit(line: str) -> None:
    print(line, flush=True)


def normalize_status(raw: object) -> str:
    return str(raw if raw is not None else "").strip().upper().replace(
        "-", "_").replace(" ", "_")


def http_error_category(status: int) -> str:
    if 400 <= status < 500:
        return "api_rejected"
    if status >= 500:
        return "api_server_error"
    return "api_error"


def iter_strings(value: object) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str):
                yield key
            for text in iter_strings(item):
                yield text
    elif isinstance(value, list):
        for item in value:
            for text in iter_strings(item):
                yield text


def has_unresolved_placeholder(value: object) -> bool:
    return any(PLACEHOLDER_PATTERN.search(text)
               for text in iter_strings(value))


def check_url_base(base: str, allow_http: bool) -> None:
    try:
        parsed = urllib.parse.urlsplit(base)
    except ValueError:
        raise MigrationError("config_invalid")
    if not parsed.netloc:
        raise MigrationError("config_invalid")
    if parsed.scheme == "https":
        return
    if parsed.scheme == "http" and allow_http:
        return
    raise MigrationError("config_insecure_url")


def validate_config(raw: object) -> Dict[str, Dict[str, Any]]:
    if not isinstance(raw, dict) or set(raw) != ALLOWED_TOP_LEVEL_KEYS:
        raise MigrationError("config_invalid")
    transfer = raw["transfer"]
    execution = raw["execution"]
    if not isinstance(transfer, dict) or not isinstance(execution, dict):
        raise MigrationError("config_invalid")
    if set(execution) != EXECUTION_KEYS:
        raise MigrationError("config_invalid")
    for key in transfer:
        if key not in TRANSFER_KEYS:
            raise MigrationError("config_invalid")
    for field in ("notes", "scenario", "origin_endpoint_id",
                  "destination_endpoint_id"):
        value = transfer.get(field)
        if not isinstance(value, str) or not value.strip():
            raise MigrationError("config_invalid")
    if transfer["scenario"] != "live_migration":
        raise MigrationError("config_invalid")
    if (transfer["origin_endpoint_id"].strip()
            == transfer["destination_endpoint_id"].strip()):
        raise MigrationError("config_invalid")
    instances = transfer.get("instances")
    if (not isinstance(instances, list) or not instances
            or not all(isinstance(item, str) and item.strip()
                       for item in instances)
            or len(set(instances)) != len(instances)):
        raise MigrationError("config_invalid")
    for field in ("source_environment", "destination_environment",
                  "network_map", "storage_mappings"):
        if not isinstance(transfer.get(field), dict):
            raise MigrationError("config_invalid")
    for field in ("clone_disks", "skip_os_morphing"):
        if not isinstance(transfer.get(field), bool):
            raise MigrationError("config_invalid")
    if not all(isinstance(execution.get(field), bool)
               for field in EXECUTION_KEYS):
        raise MigrationError("config_invalid")
    if has_unresolved_placeholder(raw):
        raise MigrationError("config_unresolved_placeholder")
    return {"transfer": transfer, "execution": execution}


def load_config_file(path: str) -> object:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        raise MigrationError("config_invalid")


def read_password_from_stdin() -> str:
    try:
        raw = sys.stdin.buffer.read().decode("utf-8")
    except (OSError, UnicodeError):
        raise MigrationError("missing_password")
    password = raw.strip()
    if not password:
        raise MigrationError("missing_password")
    return password


class CoriolisClient:
    """Minimal TLS-verified Coriolis/Keystone REST client."""

    def __init__(self, api_base: str, keystone_base: str) -> None:
        self._api_base: str = api_base.rstrip("/")
        self._keystone_base: str = keystone_base.rstrip("/")
        self._token: Optional[str] = None
        self.base_url: Optional[str] = None

    @staticmethod
    def _encoded(segment: str) -> str:
        return urllib.parse.quote(segment, safe="")

    def _request(
            self, url: str, method: str = "GET",
            body: Optional[Dict[str, Any]] = None,
    ) -> Tuple[int, object]:
        headers = {"Accept": "application/json"}
        if self._token is not None:
            headers["X-Auth-Token"] = self._token
        data: Optional[bytes] = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(
                    request, timeout=HTTP_REQUEST_TIMEOUT) as response:
                raw = response.read()
                status = int(getattr(response, "status", 200))
        except urllib.error.HTTPError as error:
            raise MigrationError(http_error_category(error.code), error.code)
        except (urllib.error.URLError, OSError, ValueError):
            raise MigrationError("network_error")
        if not raw:
            return status, {}
        try:
            return status, json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeError):
            raise MigrationError("invalid_response")

    def authenticate(self, password: str) -> None:
        body = {
            "auth": {
                "identity": {
                    "methods": ["password"],
                    "password": {"user": {
                        "name": "coriolis",
                        "password": password,
                        "domain": {"name": "Default"},
                    }},
                },
                "scope": {"project": {
                    "name": "service",
                    "domain": {"name": "Default"},
                }},
            }
        }
        # The configured base is already the externally reachable
        # Keystone v3 base (e.g. public ingress '/identity' or direct
        # '/v3'), so append only the token action.
        url = self._keystone_base + "/auth/tokens"
        request = urllib.request.Request(
            url, data=json.dumps(body).encode("utf-8"),
            headers={"Accept": "application/json",
                     "Content-Type": "application/json"},
            method="POST")
        try:
            with urllib.request.urlopen(
                    request, timeout=HTTP_REQUEST_TIMEOUT) as response:
                token = response.headers.get("X-Subject-Token")
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            raise MigrationError("authentication_failed", error.code)
        except (urllib.error.URLError, OSError, ValueError, UnicodeError):
            raise MigrationError("network_error")
        project_id = None
        if isinstance(payload, dict):
            token_section = payload.get("token")
            if isinstance(token_section, dict):
                project = token_section.get("project")
                if isinstance(project, dict):
                    project_id = project.get("id")
        if (not token or not isinstance(project_id, str)
                or not project_id):
            raise MigrationError("authentication_failed")
        self._token = str(token)
        # The configured API base is already the externally reachable
        # Coriolis v1 base (e.g. public ingress '/coriolis' or direct
        # '/v1'), so append only the project-scoped path.
        self.base_url = "%s/%s" % (
            self._api_base, self._encoded(project_id))

    def _url(self, path: str) -> str:
        if self.base_url is None:
            raise MigrationError("invalid_response")
        return self.base_url + path

    def get(self, path: str) -> object:
        return self._request(self._url(path))[1]

    def post(self, path: str, body: Dict[str, Any]) -> object:
        return self._request(self._url(path), method="POST", body=body)[1]


def _single(body: object, key: str) -> Dict[str, Any]:
    if not isinstance(body, dict):
        raise MigrationError("invalid_response")
    item = body.get(key)
    if not isinstance(item, dict):
        raise MigrationError("invalid_response")
    return item


def _collection(body: object, key: str) -> List[Dict[str, Any]]:
    if not isinstance(body, dict):
        raise MigrationError("invalid_response")
    items = body.get(key)
    if not isinstance(items, list) or any(
            not isinstance(item, dict) for item in items):
        raise MigrationError("invalid_response")
    return items


def _matching_transfers(
        client: CoriolisClient, transfer: Dict[str, Any]) -> List[
            Dict[str, Any]]:
    matches = []
    for item in _collection(client.get("/transfers"), "transfers"):
        if (item.get("notes") == transfer["notes"]
                and item.get("origin_endpoint_id")
                == transfer["origin_endpoint_id"]
                and item.get("destination_endpoint_id")
                == transfer["destination_endpoint_id"]):
            matches.append(item)
    return matches


def preflight(client: CoriolisClient, transfer: Dict[str, Any]) -> None:
    endpoints = _collection(client.get("/endpoints"), "endpoints")
    endpoint_ids = set()
    for endpoint in endpoints:
        if isinstance(endpoint.get("id"), str):
            endpoint_ids.add(endpoint["id"])
    if (transfer["origin_endpoint_id"] not in endpoint_ids
            or transfer["destination_endpoint_id"] not in endpoint_ids):
        raise MigrationError("preflight_failed")
    matching = _matching_transfers(client, transfer)
    if matching:
        raise MigrationError("preflight_failed")
    # No ambiguous existing target: no deployment may already carry the
    # exact configured notes either.
    deployments = _collection(client.get("/deployments"), "deployments")
    if any(deployment.get("notes") == transfer["notes"]
           for deployment in deployments):
        raise MigrationError("preflight_failed")


def create_transfer(
        client: CoriolisClient, transfer: Dict[str, Any]) -> str:
    try:
        posted = _single(client.post("/transfers", {"transfer": transfer}),
                         "transfer")
        created_id = posted.get("id")
        if isinstance(created_id, str) and created_id:
            return created_id
        raise MigrationError("post_ambiguous")
    except MigrationError as error:
        if error.category == "api_rejected":
            raise
        matches = _matching_transfers(client, transfer)
        if (len(matches) == 1
                and isinstance(matches[0].get("id"), str)
                and matches[0]["id"]):
            return matches[0]["id"]
        raise MigrationError("post_ambiguous", error.http_status)


def _executions(client: CoriolisClient, transfer_id: str) -> List[
        Dict[str, Any]]:
    path = "/transfers/%s/executions" % client._encoded(transfer_id)
    return _collection(client.get(path), "executions")


def start_execution(
        client: CoriolisClient, transfer_id: str,
        execution: Dict[str, Any]) -> str:
    path = "/transfers/%s/executions" % client._encoded(transfer_id)
    baseline = len(_executions(client, transfer_id))
    try:
        posted = _single(client.post(path, {"execution": execution}),
                         "execution")
        execution_id = posted.get("id")
        if isinstance(execution_id, str) and execution_id:
            return execution_id
        raise MigrationError("post_ambiguous")
    except MigrationError as error:
        if error.category == "api_rejected":
            raise
        after = _executions(client, transfer_id)
        if (baseline == 0 and len(after) == 1
                and isinstance(after[0].get("id"), str)
                and after[0]["id"]):
            return after[0]["id"]
        raise MigrationError("post_ambiguous", error.http_status)


def _poll_get(
        client: CoriolisClient, path: str, deadline: float,
        poll_interval: int, timeout_category: str) -> object:
    """Perform a GET-only polling read with bounded transient retry.

    At most ``MAX_CONSECUTIVE_NETWORK_ERRORS`` consecutive
    ``network_error`` read failures are tolerated within the deadline
    (sleeping the poll interval between them, with the count resetting
    on a successful read). The third consecutive network failure, a
    non-network error, or an expired deadline stops the phase; the
    phase's fixed timeout category is used when the deadline expires.
    """
    consecutive_errors = 0
    while True:
        try:
            body = client.get(path)
        except MigrationError as error:
            if error.category != "network_error":
                raise
            consecutive_errors += 1
            if consecutive_errors >= MAX_CONSECUTIVE_NETWORK_ERRORS:
                raise
            if time.monotonic() >= deadline:
                raise MigrationError(timeout_category)
            time.sleep(poll_interval)
        else:
            return body


def poll_execution(
        client: CoriolisClient, transfer_id: str, execution_id: str,
        timeout: int, poll_interval: int) -> None:
    path = "/transfers/%s/executions/%s" % (
        client._encoded(transfer_id), client._encoded(execution_id))
    deadline = time.monotonic() + timeout
    while True:
        status = normalize_status(_single(
            _poll_get(client, path, deadline, poll_interval,
                      "execution_timeout"),
            "execution").get("status"))
        if status == TERMINAL_SUCCESS_STATUS:
            return
        if status in TERMINAL_FAILURE_STATUSES:
            raise MigrationError("execution_failed")
        if time.monotonic() >= deadline:
            raise MigrationError("execution_timeout")
        time.sleep(poll_interval)


def discover_deployment(
        client: CoriolisClient, transfer_id: str,
        timeout: int, poll_interval: int) -> str:
    deadline = time.monotonic() + timeout
    while True:
        deployments = [
            deployment for deployment in _collection(
                _poll_get(client, "/deployments", deadline, poll_interval,
                          "deployment_timeout"),
                "deployments")
            if deployment.get("transfer_id") == transfer_id]
        if len(deployments) == 1:
            deployment_id = deployments[0].get("id")
            if not isinstance(deployment_id, str) or not deployment_id:
                raise MigrationError("deployment_ambiguous")
            return deployment_id
        if len(deployments) > 1:
            raise MigrationError("deployment_ambiguous")
        if time.monotonic() >= deadline:
            raise MigrationError("deployment_timeout")
        time.sleep(poll_interval)


def poll_deployment(
        client: CoriolisClient, deployment_id: str,
        timeout: int, poll_interval: int) -> None:
    path = "/deployments/%s" % client._encoded(deployment_id)
    deadline = time.monotonic() + timeout
    while True:
        status = normalize_status(_single(
            _poll_get(client, path, deadline, poll_interval,
                      "deployment_timeout"),
            "deployment").get("last_execution_status"))
        if status == TERMINAL_SUCCESS_STATUS:
            return
        if status in TERMINAL_FAILURE_STATUSES:
            raise MigrationError("deployment_failed")
        if time.monotonic() >= deadline:
            raise MigrationError("deployment_timeout")
        time.sleep(poll_interval)


def run_migration(args: argparse.Namespace) -> int:
    api_base = str(args.api_base).rstrip("/")
    keystone_base = str(args.keystone_base).rstrip("/")
    check_url_base(api_base, args.allow_http)
    check_url_base(keystone_base, args.allow_http)
    if args.timeout <= 0 or args.poll_interval <= 0:
        raise MigrationError("config_invalid")
    config = validate_config(load_config_file(args.config))
    transfer = config["transfer"]
    execution = config["execution"]
    password = read_password_from_stdin()
    client = CoriolisClient(api_base, keystone_base)
    client.authenticate(password)
    password = None
    preflight(client, transfer)
    emit("PASS preflight")
    transfer_id = create_transfer(client, transfer)
    emit("PASS transfer id=%s" % transfer_id)
    execution_id = start_execution(client, transfer_id, execution)
    poll_execution(
        client, transfer_id, execution_id, args.timeout,
        args.poll_interval)
    emit("PASS execution id=%s status=%s"
         % (execution_id, TERMINAL_SUCCESS_STATUS))
    if execution["auto_deploy"]:
        deployment_id = discover_deployment(
            client, transfer_id, args.timeout, args.poll_interval)
        poll_deployment(
            client, deployment_id, args.timeout, args.poll_interval)
        emit("PASS deployment id=%s status=%s"
             % (deployment_id, TERMINAL_SUCCESS_STATUS))
    emit("SUMMARY headless-migration passed")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run one parameterized Coriolis live migration against "
            "existing endpoints: create a Transfer, start one execution, "
            "poll it, and poll the correlated auto-deployment when "
            "enabled. Nothing is cleaned up afterwards."))
    parser.add_argument(
        "--api-base", required=True,
        help="Externally reachable Coriolis v1 API base URL, e.g. "
             "https://host/coriolis or http://api:7667/v1 (HTTPS; "
             "requires --allow-http for development HTTP).")
    parser.add_argument(
        "--keystone-base", required=True,
        help="Externally reachable Keystone v3 base URL, e.g. "
             "https://host/identity or http://keystone:5000/v3 "
             "(HTTPS; requires --allow-http for development HTTP).")
    parser.add_argument(
        "--config", required=True,
        help="Path to the JSON migration config (see "
             "docs/assets/manifests/headless-migration.example.json).")
    parser.add_argument(
        "--timeout", type=int, default=DEFAULT_TIMEOUT,
        help="Overall poll timeout in seconds per phase "
             "(default: %(default)s).")
    parser.add_argument(
        "--poll-interval", type=int, default=DEFAULT_POLL_INTERVAL,
        help="Poll interval in seconds (default: %(default)s).")
    parser.add_argument(
        "--allow-http", action="store_true",
        help="Allow plain HTTP base URLs for development only.")
    parser.add_argument(
        "--run", action="store_true", required=True,
        help="Mandatory acknowledgement that this creates a real "
             "migration.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run_migration(args)
    except MigrationError as error:
        emit("ERROR category=%s http_status=%s"
             % (error.category, error.http_status))
        if error.category.startswith("config_") or error.category in (
                "missing_password",):
            return EXIT_CONFIG_ERROR
        return EXIT_FAILURE
    except Exception:
        emit("ERROR category=unexpected_failure http_status=none")
        return EXIT_FAILURE


if __name__ == "__main__":
    sys.exit(main())
