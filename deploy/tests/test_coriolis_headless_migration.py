#!/usr/bin/env python3
"""Focused standard-library tests for coriolis-headless-migration.py."""

import contextlib
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
import unittest
import urllib.error
import urllib.parse
import urllib.request
from unittest import mock

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HELPER_PATH = os.path.join(
    REPO_ROOT, "deploy", "coriolis-headless-migration.py")
EXAMPLE_PATH = os.path.join(
    REPO_ROOT, "docs", "assets", "manifests",
    "headless-migration.example.json")


def _load_helper():
    spec = importlib.util.spec_from_file_location(
        "coriolis_headless_migration", HELPER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HELPER = _load_helper()

API_BASE = "https://coriolis.example.invalid/coriolis"
KEYSTONE_BASE = "https://keystone.example.invalid/identity"
AUTH_PATH = "/identity/auth/tokens"
PROJECT_PATH = "/coriolis/proj-1"
NOTES = "tutorial-notes-alpha"
ORIGIN_ENDPOINT = "endpoint-origin"
DESTINATION_ENDPOINT = "endpoint-destination"
TRANSFER_PATH = PROJECT_PATH + "/transfers/transfer-1"
EXECUTIONS_PATH = TRANSFER_PATH + "/executions"
EXECUTION_PATH = EXECUTIONS_PATH + "/execution-1"
DEPLOYMENT_DETAIL_PATH = PROJECT_PATH + "/deployments/deployment-1"


def valid_config():
    return {
        "transfer": {
            "notes": NOTES,
            "scenario": "live_migration",
            "origin_endpoint_id": ORIGIN_ENDPOINT,
            "destination_endpoint_id": DESTINATION_ENDPOINT,
            "instances": ["instance-1"],
            "source_environment": {
                "replica_export_mechanism": "swift_backups"},
            "destination_environment": {
                "migr_flavor_name": "c1.small",
                "migr_network": "network-1"},
            "network_map": {"source-network": "destination-network-1"},
            "storage_mappings": {"default": "__DEFAULT__"},
            "clone_disks": True,
            "skip_os_morphing": True,
        },
        "execution": {"shutdown_instances": True, "auto_deploy": True},
    }


def fill_placeholders(value):
    """Replace every <...> placeholder string with a unique literal."""
    if isinstance(value, str):
        match = HELPER.PLACEHOLDER_PATTERN.fullmatch(value)
        if match:
            return "filled-" + value[1:-1].lower()
        return value
    if isinstance(value, dict):
        return {fill_placeholders(key): fill_placeholders(item)
                for key, item in value.items()}
    if isinstance(value, list):
        return [fill_placeholders(item) for item in value]
    return value


class FakeResponse:
    def __init__(self, status=200, body=None, headers=None):
        self.status = status
        self.headers = headers or {}
        self._body = b"" if body is None else json.dumps(body).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class RecordingUrlopen:
    """Scripted stand-in for urllib.request.urlopen."""

    def __init__(self, routes):
        self._routes = routes
        self._counts = {}
        self.calls = []
        self.bodies = {}

    def __call__(self, request, timeout=None):
        method = request.get_method()
        path = urllib.parse.urlsplit(request.full_url).path
        self.calls.append((method, path))
        if request.data is not None:
            self.bodies.setdefault((method, path), []).append(
                json.loads(request.data.decode("utf-8")))
        key = (method, path)
        if key not in self._routes:
            raise AssertionError("unexpected request: %s %s" % key)
        sequence = self._routes[key]
        index = self._counts.get(key, 0)
        self._counts[key] = index + 1
        response = sequence[min(index, len(sequence) - 1)]
        if isinstance(response, Exception):
            raise response
        return response


def http_error(url_path, code, body):
    return urllib.error.HTTPError(
        url_path, code, "error", {}, io.BytesIO(body))


def success_routes(transfer_id="transfer-1", execution_statuses=None,
                   deployment_pages=None, deployment_statuses=None):
    executions_path = "%s/transfers/%s/executions" % (
        PROJECT_PATH, transfer_id)
    execution_path = "%s/execution-1" % executions_path
    if execution_statuses is None:
        execution_statuses = ["RUNNING", "COMPLETED"]
    if deployment_pages is None:
        deployment_pages = [[{"id": "deployment-1",
                              "transfer_id": transfer_id}]]
    if deployment_statuses is None:
        deployment_statuses = ["RUNNING", "COMPLETED"]
    return {
        ("POST", AUTH_PATH): [FakeResponse(
            201,
            {"token": {"project": {"id": "proj-1"}}},
            {"X-Subject-Token": "TOKEN-VALUE-DO-NOT-PRINT"})],
        ("GET", PROJECT_PATH + "/endpoints"): [FakeResponse(200, {
            "endpoints": [
                {"id": ORIGIN_ENDPOINT,
                 "connection_info": {"password": "SECRET-CONN-INFO"}},
                {"id": DESTINATION_ENDPOINT},
                {"id": "some-other-endpoint"}]})],
        ("GET", PROJECT_PATH + "/transfers"): [
            FakeResponse(200, {"transfers": []})],
        ("POST", PROJECT_PATH + "/transfers"): [FakeResponse(200, {
            "transfer": {"id": transfer_id, "notes": NOTES}})],
        ("GET", executions_path): [FakeResponse(200, {"executions": []})],
        ("POST", executions_path): [FakeResponse(200, {
            "execution": {"id": "execution-1", "status": "PENDING"}})],
        ("GET", execution_path): [
            FakeResponse(200, {"execution": {
                "id": "execution-1",
                "status": status,
                "message": "SECRET-EXECUTION-DETAIL"}})
            for status in execution_statuses],
        ("GET", PROJECT_PATH + "/deployments"): [
            FakeResponse(200, {"deployments": page})
            for page in deployment_pages],
        ("GET", PROJECT_PATH + "/deployments/deployment-1"): [
            FakeResponse(200, {"deployment": {
                "id": "deployment-1",
                "last_execution_status": status,
                "info": "SECRET-DEPLOYMENT-DETAIL"}})
            for status in deployment_statuses],
    }


class HelperTestCase(unittest.TestCase):
    def run_cli(self, config, routes, argv=None, sleep=None,
                monotonic=None):
        with tempfile.NamedTemporaryFile(
                "w", suffix=".json", delete=False) as handle:
            json.dump(config, handle)
            config_path = handle.name
        self.addCleanup(os.unlink, config_path)
        recorder = RecordingUrlopen(routes)
        if argv is None:
            argv = [
                "--api-base", API_BASE,
                "--keystone-base", KEYSTONE_BASE,
                "--config", config_path,
                "--timeout", "60",
                "--poll-interval", "1",
                "--run",
            ]
        stdin = mock.Mock(buffer=io.BytesIO(b"service-password\n"))
        stdout = io.StringIO()
        patches = [
            mock.patch.object(urllib.request, "urlopen", recorder),
            mock.patch("time.sleep", sleep or (lambda seconds: None)),
            mock.patch.object(sys, "stdin", stdin),
            contextlib.redirect_stdout(stdout),
        ]
        if monotonic is not None:
            patches.append(mock.patch("time.monotonic", monotonic))
        with contextlib.ExitStack() as stack:
            for patcher in patches:
                stack.enter_context(patcher)
            code = HELPER.main(argv)
        return code, stdout.getvalue(), recorder

    def test_successful_run_polls_execution_and_deployment(self):
        code, out, recorder = self.run_cli(valid_config(), success_routes())
        self.assertEqual(code, 0)
        self.assertIn("PASS preflight", out)
        self.assertIn("PASS transfer id=transfer-1", out)
        self.assertIn("PASS execution id=execution-1 status=COMPLETED", out)
        self.assertIn(
            "PASS deployment id=deployment-1 status=COMPLETED", out)
        self.assertIn("SUMMARY headless-migration passed", out)
        # Polled through the intermediate non-terminal states first.
        self.assertEqual(
            recorder.calls.count(
                ("GET", PROJECT_PATH + "/transfers/transfer-1"
                 "/executions/execution-1")), 2)
        self.assertEqual(
            recorder.calls.count(
                ("GET", PROJECT_PATH + "/deployments")), 2)

    def test_cli_username_and_project_override_keystone_auth(self):
        with tempfile.NamedTemporaryFile(
                "w", suffix=".json", delete=False) as handle:
            json.dump(valid_config(), handle)
            config_path = handle.name
        self.addCleanup(os.unlink, config_path)
        recorder = RecordingUrlopen(success_routes())
        argv = [
            "--api-base", API_BASE,
            "--keystone-base", KEYSTONE_BASE,
            "--config", config_path,
            "--timeout", "60",
            "--poll-interval", "1",
            "--username", "admin",
            "--project-name", "admin",
            "--run",
        ]
        stdin = mock.Mock(buffer=io.BytesIO(b"admin-password\n"))
        stdout = io.StringIO()
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(
                urllib.request, "urlopen", recorder))
            stack.enter_context(mock.patch(
                "time.sleep", lambda seconds: None))
            stack.enter_context(mock.patch.object(sys, "stdin", stdin))
            stack.enter_context(contextlib.redirect_stdout(stdout))
            code = HELPER.main(argv)
        self.assertEqual(code, 0)
        auth = recorder.bodies[("POST", AUTH_PATH)][0]["auth"]
        user = auth["identity"]["password"]["user"]
        self.assertEqual(user["name"], "admin")
        self.assertEqual(user["domain"]["name"], "Default")
        self.assertEqual(auth["scope"]["project"]["name"], "admin")
        self.assertEqual(
            auth["scope"]["project"]["domain"]["name"], "Default")
        out = stdout.getvalue()
        self.assertNotIn("admin-password", out)
        self.assertNotIn("TOKEN-VALUE-DO-NOT-PRINT", out)

    def test_client_auth_defaults_remain_coriolis_service(self):
        recorder = RecordingUrlopen({
            ("POST", AUTH_PATH): [FakeResponse(
                201,
                {"token": {"project": {"id": "proj-1"}}},
                {"X-Subject-Token": "TOKEN-VALUE-DO-NOT-PRINT"})],
        })
        with mock.patch.object(urllib.request, "urlopen", recorder):
            client = HELPER.CoriolisClient(API_BASE, KEYSTONE_BASE)
            client.authenticate("service-password")
        auth = recorder.bodies[("POST", AUTH_PATH)][0]["auth"]
        self.assertEqual(
            auth["identity"]["password"]["user"]["name"], "coriolis")
        self.assertEqual(auth["scope"]["project"]["name"], "service")

    def test_post_bodies_use_transfer_and_execution_wrapping(self):
        config = valid_config()
        code, out, recorder = self.run_cli(config, success_routes())
        self.assertEqual(code, 0)
        transfer_posts = recorder.bodies[(
            "POST", PROJECT_PATH + "/transfers")]
        execution_posts = recorder.bodies[(
            "POST", PROJECT_PATH + "/transfers/transfer-1/executions")]
        self.assertEqual(transfer_posts, [{"transfer": config["transfer"]}])
        self.assertEqual(
            execution_posts, [{"execution": config["execution"]}])

    def test_unresolved_placeholder_rejected_before_network(self):
        with open(EXAMPLE_PATH, "r", encoding="utf-8") as handle:
            config = json.load(handle)
        code, out, recorder = self.run_cli(config, success_routes())
        self.assertNotEqual(code, 0)
        self.assertEqual(recorder.calls, [])
        self.assertIn("ERROR category=config_unresolved_placeholder", out)

    def test_transient_execution_read_error_then_success(self):
        routes = success_routes(execution_statuses=["COMPLETED"])
        routes[("GET", EXECUTION_PATH)] = [
            urllib.error.URLError("transient reset"),
            FakeResponse(200, {"execution": {
                "id": "execution-1", "status": "COMPLETED"}})]
        code, out, recorder = self.run_cli(valid_config(), routes)
        self.assertEqual(code, 0)
        self.assertIn(
            "PASS execution id=execution-1 status=COMPLETED", out)
        self.assertIn("SUMMARY headless-migration passed", out)
        # The transient error plus the successful read: two execution GETs.
        self.assertEqual(
            recorder.calls.count(("GET", EXECUTION_PATH)), 2)

    def test_three_consecutive_network_errors_stop_without_downstream(self):
        routes = success_routes()
        routes[("GET", EXECUTION_PATH)] = [
            urllib.error.URLError("reset one"),
            urllib.error.URLError("reset two"),
            urllib.error.URLError("reset three"),
            FakeResponse(200, {"execution": {
                "id": "execution-1", "status": "COMPLETED"}})]
        code, out, recorder = self.run_cli(valid_config(), routes)
        self.assertEqual(code, 1)
        self.assertIn("ERROR category=network_error", out)
        self.assertNotIn("PASS execution", out)
        self.assertNotIn("SUMMARY", out)
        # Retries stop at three; the fourth scripted response is unused.
        self.assertEqual(
            recorder.calls.count(("GET", EXECUTION_PATH)), 3)
        self.assertNotIn(("GET", DEPLOYMENT_DETAIL_PATH), recorder.calls)

    def test_deployment_terminal_failure(self):
        routes = success_routes(deployment_statuses=["RUNNING", "ERROR"])
        code, out, recorder = self.run_cli(valid_config(), routes)
        self.assertEqual(code, 1)
        self.assertIn("ERROR category=deployment_failed http_status=none",
                      out)
        self.assertNotIn("SECRET-DEPLOYMENT-DETAIL", out)
        self.assertIn("PASS execution id=execution-1", out)
        self.assertNotIn("SUMMARY", out)

    def test_deployment_ambiguity_with_two_correlated_deployments(self):
        correlated = [
            {"id": "deployment-1", "transfer_id": "transfer-1"},
            {"id": "deployment-2", "transfer_id": "transfer-1"}]
        routes = success_routes(deployment_pages=[[], correlated])
        code, out, recorder = self.run_cli(valid_config(), routes)
        self.assertEqual(code, 1)
        self.assertIn("ERROR category=deployment_ambiguous http_status=none",
                      out)
        self.assertNotIn(("GET", DEPLOYMENT_DETAIL_PATH), recorder.calls)

    def test_execution_timeout_with_mocked_monotonic(self):
        routes = success_routes(execution_statuses=["RUNNING"])
        clock = iter([0.0, 100.0])
        code, out, recorder = self.run_cli(
            valid_config(), routes, monotonic=lambda: next(clock))
        self.assertEqual(code, 1)
        self.assertIn("ERROR category=execution_timeout http_status=none",
                      out)
        self.assertNotIn(("GET", DEPLOYMENT_DETAIL_PATH), recorder.calls)

    def test_auto_deploy_false_skips_deployment_discovery(self):
        config = valid_config()
        config["execution"]["auto_deploy"] = False
        code, out, recorder = self.run_cli(config, success_routes())
        self.assertEqual(code, 0)
        self.assertIn("SUMMARY headless-migration passed", out)
        self.assertNotIn("PASS deployment", out)
        self.assertNotIn(("GET", DEPLOYMENT_DETAIL_PATH), recorder.calls)

    def test_authentication_failure_safe_output(self):
        routes = success_routes()
        routes[("POST", AUTH_PATH)] = [
            http_error(AUTH_PATH, 401, b"SECRET-AUTH-DETAIL")]
        code, out, recorder = self.run_cli(valid_config(), routes)
        self.assertEqual(code, 1)
        self.assertIn(
            "ERROR category=authentication_failed http_status=401", out)
        self.assertNotIn("SECRET-AUTH-DETAIL", out)
        self.assertNotIn("service-password", out)

    def test_transfer_post_4xx_is_not_retried_or_resolved(self):
        routes = success_routes()
        routes[("POST", PROJECT_PATH + "/transfers")] = [
            http_error(PROJECT_PATH + "/transfers", 400, b"SECRET-REJECT")]
        code, out, recorder = self.run_cli(valid_config(), routes)
        self.assertEqual(code, 1)
        self.assertIn("ERROR category=api_rejected http_status=400", out)
        self.assertNotIn("SECRET-REJECT", out)
        # No blind retry and no ambiguous-resolution lookup on 4xx.
        self.assertEqual(
            recorder.calls.count(("POST", PROJECT_PATH + "/transfers")), 1)
        self.assertEqual(recorder.calls.count(("GET",
                                               PROJECT_PATH + "/transfers")),
                         1)
        self.assertNotIn(("POST", EXECUTIONS_PATH), recorder.calls)

    def test_public_ingress_paths_never_duplicate_version_segments(self):
        code, out, recorder = self.run_cli(valid_config(), success_routes())
        self.assertEqual(code, 0)
        self.assertIn(("POST", "/identity/auth/tokens"), recorder.calls)
        self.assertIn(("GET", "/coriolis/proj-1/endpoints"), recorder.calls)
        self.assertIn(
            ("POST", "/coriolis/proj-1/transfers"), recorder.calls)
        for method, path in recorder.calls:
            self.assertNotIn("/v3/", path)
            self.assertNotIn("/v1/", path)

    def test_terminal_failure_stops_without_leaking_detail(self):
        routes = success_routes(execution_statuses=["RUNNING", "ERROR"])
        code, out, recorder = self.run_cli(valid_config(), routes)
        self.assertEqual(code, 1)
        self.assertIn("ERROR category=execution_failed http_status=none",
                      out)
        self.assertNotIn("SECRET-EXECUTION-DETAIL", out)
        self.assertNotIn("PASS execution", out)
        self.assertNotIn("SUMMARY", out)
        self.assertNotIn(("GET", PROJECT_PATH + "/deployments/deployment-1"),
                         recorder.calls)

    def test_http_error_reports_category_and_status_only(self):
        routes = success_routes()
        routes[("GET", PROJECT_PATH + "/endpoints")] = [
            urllib.error.HTTPError(
                PROJECT_PATH + "/endpoints", 503,
                "Service Unavailable", {},
                io.BytesIO(b"SECRET-UPSTREAM-BODY"))]
        code, out, recorder = self.run_cli(valid_config(), routes)
        self.assertEqual(code, 1)
        self.assertIn(
            "ERROR category=api_server_error http_status=503", out)
        self.assertNotIn("SECRET-UPSTREAM-BODY", out)
        self.assertNotIn("service-password", out)

    def test_output_never_contains_token_or_connection_info(self):
        code, out, recorder = self.run_cli(valid_config(), success_routes())
        self.assertEqual(code, 0)
        for secret in ("TOKEN-VALUE-DO-NOT-PRINT", "SECRET-CONN-INFO",
                       "service-password", "SECRET-DEPLOYMENT-DETAIL"):
            self.assertNotIn(secret, out)

    def test_duplicate_notes_preflight_blocks_before_post(self):
        routes = success_routes()
        routes[("GET", PROJECT_PATH + "/transfers")] = [FakeResponse(200, {
            "transfers": [{
                "id": "transfer-old", "notes": NOTES,
                "origin_endpoint_id": ORIGIN_ENDPOINT,
                "destination_endpoint_id": DESTINATION_ENDPOINT}]})]
        code, out, recorder = self.run_cli(valid_config(), routes)
        self.assertEqual(code, 1)
        self.assertIn("ERROR category=preflight_failed http_status=none",
                      out)
        self.assertNotIn(
            ("POST", PROJECT_PATH + "/transfers"), recorder.calls)

    def test_missing_endpoint_preflight_blocks(self):
        routes = success_routes()
        routes[("GET", PROJECT_PATH + "/endpoints")] = [FakeResponse(
            200, {"endpoints": [{"id": ORIGIN_ENDPOINT}]})]
        code, out, recorder = self.run_cli(valid_config(), routes)
        self.assertEqual(code, 1)
        self.assertIn("ERROR category=preflight_failed", out)
        self.assertNotIn(
            ("POST", PROJECT_PATH + "/transfers"), recorder.calls)

    def test_ambiguous_transfer_post_resolves_via_single_match(self):
        routes = success_routes(transfer_id="transfer-recovered")
        routes[("POST", PROJECT_PATH + "/transfers")] = [
            urllib.error.URLError("connection reset")]
        routes[("GET", PROJECT_PATH + "/transfers")] = [
            FakeResponse(200, {"transfers": []}),
            FakeResponse(200, {"transfers": [{
                "id": "transfer-recovered", "notes": NOTES,
                "origin_endpoint_id": ORIGIN_ENDPOINT,
                "destination_endpoint_id": DESTINATION_ENDPOINT}]})]
        code, out, recorder = self.run_cli(valid_config(), routes)
        self.assertEqual(code, 0)
        self.assertIn("PASS transfer id=transfer-recovered", out)
        # The ambiguous POST was never retried blindly.
        self.assertEqual(
            recorder.calls.count(("POST", PROJECT_PATH + "/transfers")), 1)

    def test_ambiguous_transfer_post_stops_when_unmatched(self):
        routes = success_routes()
        routes[("POST", PROJECT_PATH + "/transfers")] = [
            urllib.error.URLError("connection reset")]
        code, out, recorder = self.run_cli(valid_config(), routes)
        self.assertEqual(code, 1)
        self.assertIn("ERROR category=post_ambiguous http_status=none", out)
        self.assertEqual(
            recorder.calls.count(("POST", PROJECT_PATH + "/transfers")), 1)
        self.assertNotIn(
            ("POST", PROJECT_PATH + "/transfers/transfer-1/executions"),
            recorder.calls)

    def test_http_requires_explicit_allow_http(self):
        config = valid_config()
        with tempfile.NamedTemporaryFile(
                "w", suffix=".json", delete=False) as handle:
            json.dump(config, handle)
            config_path = handle.name
        self.addCleanup(os.unlink, config_path)
        routes = success_routes()
        recorder = RecordingUrlopen(routes)
        stdout = io.StringIO()
        with mock.patch.object(urllib.request, "urlopen", recorder), \
                contextlib.redirect_stdout(stdout):
            code = HELPER.main([
                "--api-base", "http://coriolis.example.invalid",
                "--keystone-base", KEYSTONE_BASE,
                "--config", config_path,
                "--run",
            ])
        self.assertNotEqual(code, 0)
        self.assertIn(
            "ERROR category=config_insecure_url", stdout.getvalue())
        self.assertEqual(recorder.calls, [])


class ExampleManifestTestCase(unittest.TestCase):
    def test_example_validates_once_placeholders_are_filled(self):
        with open(EXAMPLE_PATH, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
        filled = fill_placeholders(raw)
        config = HELPER.validate_config(filled)
        transfer = config["transfer"]
        self.assertEqual(transfer["scenario"], "live_migration")
        self.assertTrue(transfer["clone_disks"])
        self.assertTrue(transfer["skip_os_morphing"])
        self.assertTrue(raw["execution"]["auto_deploy"])
        self.assertTrue(raw["execution"]["shutdown_instances"])
        self.assertEqual(
            raw["transfer"]["source_environment"][
                "replica_export_mechanism"], "swift_backups")
        self.assertEqual(
            raw["transfer"]["storage_mappings"]["default"], "__DEFAULT__")

    def test_example_contains_no_secrets_or_historical_ids(self):
        with open(EXAMPLE_PATH, "r", encoding="utf-8") as handle:
            text = handle.read()
        self.assertIsNone(
            UUID_PATTERN.search(text),
            "example must not embed historical UUID identifiers")
        for historical in ("c09be736", "0067286c", "2d4a485c",
                           "b480e10c", "8b1d447d", "c5815350",
                           "08e4c993", "coriolis-m7", "ext_net_gts",
                           "rbd1"):
            self.assertNotIn(historical, text)
        lowered = text.lower()
        for secret_word in ("password", "secret", "token"):
            self.assertNotIn(secret_word, lowered)


UUID_PATTERN = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


if __name__ == "__main__":
    unittest.main()
