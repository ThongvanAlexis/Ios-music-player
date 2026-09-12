"""Exercise build evidence rejection and packaging without pretending to run iOS."""

import copy
import importlib.util
import json
import os
from pathlib import Path
import plistlib
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave
import zipfile


PROJECT_DIR = Path(__file__).resolve().parent.parent
SPECIFICATION = importlib.util.spec_from_file_location("native_check", PROJECT_DIR / "scripts/native_check.py")
native_check = importlib.util.module_from_spec(SPECIFICATION)
SPECIFICATION.loader.exec_module(native_check)
CONFIG = native_check.read_json(PROJECT_DIR / "build_config.json")
EXPECTED_SHA = "a" * 40


def expected_evidence():
    """Supply test data whose claimed success can be challenged one field at a time."""
    return {
        "schemaVersion": native_check.EVIDENCE_SCHEMA_VERSION,
        "status": "passed",
        "sourceSHA": EXPECTED_SHA,
        "toolchain": {"xcodeVersion": CONFIG["xcodeVersion"], "xcodeBuild": CONFIG["xcodeBuild"],
                      "sdkVersion": CONFIG["sdkVersion"], "macOS": "test macOS", "swiftVersion": "test Swift"},
        "simulator": {"udid": "11111111-1111-1111-1111-111111111111", "runtimeVersion": CONFIG["sdkVersion"]},
        "resultBundle": "build/results/test/NativeTests.xcresult",
        "tests": {"executed": 2, "failed": 0, "skipped": 0,
                  "passedBySuite": {suite: 1 for suite in CONFIG["requiredTestSuites"]}},
        "release": {"status": "passed", "bundleIdentifier": CONFIG["bundleIdentifier"],
                    "minimumOSVersion": CONFIG["deploymentTarget"], "architectures": ["arm64"],
                    "ipaSHA256": "b" * 64, "resources": CONFIG["requiredResourcePaths"]},
    }


def test_result(result="Passed", class_name="NativeTracerTests"):
    """Represent xcresult's nested bundle, suite and executed case nodes."""
    return {"testNodes": [{"nodeType": "Test Plan", "name": "MusicPlayer", "children": [
        {"nodeType": "Unit test bundle", "name": "MusicPlayerTests", "children": [
            {"nodeType": "Test Suite", "name": class_name, "children": [
                {"nodeType": "Test Case", "nodeIdentifier": f"{class_name}/testPlayback()", "result": result}
            ]}
        ]}
    ]}]}


class EvidenceTests(unittest.TestCase):
    """Ensure missing native proof never passes as completed work."""

    def test_accepts_matching_complete_evidence(self):
        native_check.validate_evidence(expected_evidence(), EXPECTED_SHA, CONFIG)

    def test_portable_cli_resolves_head_without_xcode(self):
        runner = native_check.CommandRunner(PROJECT_DIR, CONFIG)
        evidence = expected_evidence()
        evidence["sourceSHA"] = native_check.resolve_sha(runner, "HEAD")
        with tempfile.TemporaryDirectory() as temporary_dir:
            filename = Path(temporary_dir) / "copied-evidence.json"
            native_check.write_json(filename, evidence)
            result = subprocess.run([sys.executable, str(PROJECT_DIR / "scripts/native_check.py"),
                                     "--check-evidence", str(filename), "--expected-sha", "HEAD"],
                                    cwd=temporary_dir, capture_output=True, text=True,
                                    timeout=CONFIG["timeoutByCommand"]["query"])
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(evidence["sourceSHA"], result.stdout)
            evidence["sourceSHA"] = "c" * 40
            native_check.write_json(filename, evidence)
            result = subprocess.run([sys.executable, str(PROJECT_DIR / "scripts/native_check.py"),
                                     "--check-evidence", str(filename)], cwd=temporary_dir,
                                    capture_output=True, text=True, timeout=CONFIG["timeoutByCommand"]["query"])
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("different source SHA", result.stderr)

    def test_rejects_stale_source_sha(self):
        with self.assertRaisesRegex(native_check.NativeCheckError, "different source SHA"):
            native_check.validate_evidence(expected_evidence(), "c" * 40, CONFIG)

    def test_rejects_incomplete_or_failed_report(self):
        for status in ("running", "failed", None):
            with self.subTest(status=status):
                evidence = expected_evidence()
                evidence["status"] = status
                with self.assertRaises(native_check.NativeCheckError):
                    native_check.validate_evidence(evidence, EXPECTED_SHA, CONFIG)

    def test_rejects_wrong_toolchain(self):
        for key in ("xcodeVersion", "xcodeBuild", "sdkVersion"):
            with self.subTest(key=key):
                evidence = expected_evidence()
                evidence["toolchain"][key] = "wrong"
                with self.assertRaises(native_check.NativeCheckError):
                    native_check.validate_evidence(evidence, EXPECTED_SHA, CONFIG)

    def test_rejects_zero_invalid_or_missing_counts(self):
        for count in (0, -1, None, True, "2"):
            with self.subTest(count=count):
                evidence = expected_evidence()
                evidence["tests"]["executed"] = count
                with self.assertRaises(native_check.NativeCheckError):
                    native_check.validate_evidence(evidence, EXPECTED_SHA, CONFIG)

    def test_rejects_missing_requested_class_even_with_other_tests(self):
        evidence = expected_evidence()
        evidence["tests"]["passedBySuite"] = {}
        with self.assertRaisesRegex(native_check.NativeCheckError, "Missing executed tests"):
            native_check.validate_evidence(evidence, EXPECTED_SHA, CONFIG)

    def test_rejects_skipped_failed_or_missing_result_bundle(self):
        for key in ("failed", "skipped"):
            evidence = expected_evidence()
            evidence["tests"][key] = 1
            with self.assertRaises(native_check.NativeCheckError):
                native_check.validate_evidence(evidence, EXPECTED_SHA, CONFIG)
        evidence = expected_evidence()
        del evidence["resultBundle"]
        with self.assertRaises(native_check.NativeCheckError):
            native_check.validate_evidence(evidence, EXPECTED_SHA, CONFIG)

    def test_rejects_missing_release_architecture_checksum_or_resource(self):
        for key in ("status", "architectures", "ipaSHA256", "resources", "minimumOSVersion", "bundleIdentifier"):
            with self.subTest(key=key):
                evidence = expected_evidence()
                del evidence["release"][key]
                with self.assertRaises(native_check.NativeCheckError):
                    native_check.validate_evidence(evidence, EXPECTED_SHA, CONFIG)


class NativeResultTests(unittest.TestCase):
    """Count real case nodes instead of matching a success phrase in console output."""

    def test_counts_nested_passed_case(self):
        suite = "MusicPlayerTests/NativeTracerTests"
        result = native_check.read_test_counts(test_result(), [suite])
        self.assertEqual(result["executed"], 1)
        self.assertEqual(result["passedBySuite"][suite], 1)

    def test_rejects_empty_result_and_summary_only(self):
        for result in ({}, {"testNodes": []}, {"testNodes": [{"nodeType": "Test Suite", "name": "NativeTracerTests", "result": "Passed"}]}):
            with self.assertRaises(native_check.NativeCheckError):
                native_check.read_test_counts(result, ["MusicPlayerTests/NativeTracerTests"])

    def test_rejects_failed_skipped_expected_failure_and_unknown_cases(self):
        for status in ("Failed", "Skipped", "Expected Failure", "Unknown"):
            with self.subTest(status=status), self.assertRaises(native_check.NativeCheckError):
                native_check.read_test_counts(test_result(status), ["MusicPlayerTests/NativeTracerTests"])

    def test_does_not_confuse_class_prefix_or_wrong_test_target(self):
        for suite in ("MusicPlayerTests/NativeTracer", "MusicPlayerUITests/NativeTracerTests"):
            with self.assertRaisesRegex(native_check.NativeCheckError, "No passed test cases"):
                native_check.read_test_counts(test_result(), [suite])


class ToolingTests(unittest.TestCase):
    """Check selection, timeouts, fixture bytes and published app structure."""

    def test_simulator_selection_ignores_input_order_and_unavailable_devices(self):
        runtime_identifier = "com.apple.CoreSimulator.SimRuntime.iOS-26-5"
        runtimes = [{"identifier": runtime_identifier, "version": "26.5", "isAvailable": True}]
        older_device = {"name": "iPhone 16", "udid": "11111111-1111-1111-1111-111111111111", "isAvailable": True}
        newer_device = {"name": "iPhone 17", "udid": "22222222-2222-2222-2222-222222222222", "isAvailable": True}
        unavailable_device = {"name": "iPhone 99", "udid": "33333333-3333-3333-3333-333333333333", "isAvailable": False}
        for devices in ([older_device, newer_device, unavailable_device], [unavailable_device, newer_device, older_device]):
            self.assertEqual(native_check.select_simulator({runtime_identifier: devices}, runtimes)["udid"], newer_device["udid"])

    def test_missing_simulator_fails(self):
        with self.assertRaisesRegex(native_check.NativeCheckError, "No available"):
            native_check.select_simulator({}, [])

    def test_command_timeout_is_failure_and_recorded(self):
        runner = native_check.CommandRunner(PROJECT_DIR, CONFIG)
        with patch.object(native_check.subprocess, "run", side_effect=subprocess.TimeoutExpired(["tool"], 1)) as run:
            with self.assertRaisesRegex(native_check.NativeCheckError, "timed out"):
                runner.run(["tool"])
            self.assertEqual(run.call_args.kwargs["timeout"], CONFIG["timeoutByCommand"]["query"])
            self.assertFalse(run.call_args.kwargs.get("shell", False))
        self.assertTrue(next(iter(runner.commands))["timedOut"])

    def test_nonzero_command_is_failure(self):
        runner = native_check.CommandRunner(PROJECT_DIR, CONFIG)
        with patch.object(native_check.subprocess, "run", return_value=subprocess.CompletedProcess(["tool"], 7, "", "specific error")):
            with self.assertRaisesRegex(native_check.NativeCheckError, "specific error"):
                runner.run(["tool"])

    def test_head_resolution_uses_git_and_rejects_revision_options(self):
        runner = native_check.CommandRunner(PROJECT_DIR, CONFIG)
        with patch.object(runner, "run", return_value=EXPECTED_SHA) as run:
            self.assertEqual(native_check.resolve_sha(runner, "HEAD"), EXPECTED_SHA)
            run.assert_called_once_with(["git", "rev-parse", "--verify", "HEAD^{commit}"])
        with self.assertRaises(native_check.NativeCheckError):
            native_check.resolve_sha(runner, "--help")

    def test_paths_cannot_escape_project(self):
        for relative_path in ("../outside", "."):
            with self.assertRaises(native_check.NativeCheckError):
                native_check.contained_path(PROJECT_DIR, relative_path)

    def test_fixture_is_nonzero_closed_pcm_with_configured_duration(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            filename = Path(temporary_dir) / CONFIG["fixture"]["basename"]
            fixture_config = copy.deepcopy(CONFIG)
            fixture_config["fixture"]["durationSeconds"] = 1
            native_check.generate_fixture(filename, fixture_config)
            with wave.open(str(filename), "rb") as source:
                self.assertEqual(source.getnframes(), CONFIG["fixture"]["sampleRate"])
                self.assertEqual(source.getsampwidth(), native_check.PCM_SAMPLE_WIDTH)
                self.assertGreater(sum(source.readframes(100)), 0)

    def test_packaging_places_one_app_directly_in_payload(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            staging_dir = Path(temporary_dir)
            app_dir = staging_dir / f"{CONFIG['appName']}.app"
            app_dir.mkdir()
            executable_filename = app_dir / CONFIG["appName"]
            executable_filename.write_bytes(b"test Mach-O stand-in")
            executable_filename.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            plist = {"CFBundleIdentifier": CONFIG["bundleIdentifier"], "CFBundleExecutable": CONFIG["appName"],
                     "MinimumOSVersion": CONFIG["deploymentTarget"], "CFBundlePackageType": "APPL", "CFBundleSupportedPlatforms": ["iPhoneOS"]}
            (app_dir / "Info.plist").write_bytes(plistlib.dumps(plist))
            for relative_path in CONFIG["requiredResourcePaths"]:
                filename = app_dir / relative_path
                filename.parent.mkdir(parents=True, exist_ok=True)
                filename.write_bytes(b"resource")
            native_check.inspect_app(app_dir, CONFIG)
            checksum = native_check.package_app(app_dir, staging_dir, CONFIG)
            self.assertRegex(checksum, r"^[0-9a-f]{64}$")
            with zipfile.ZipFile(staging_dir / CONFIG["ipaBasename"]) as archive:
                self.assertTrue(all(name.startswith(f"Payload/{app_dir.name}/") for name in archive.namelist()))
                self.assertIn(f"Payload/{app_dir.name}/{CONFIG['appName']}", archive.namelist())
            plist["CFBundleSupportedPlatforms"] = ["iPhoneSimulator"]
            (app_dir / "Info.plist").write_bytes(plistlib.dumps(plist))
            with self.assertRaises(native_check.NativeCheckError):
                native_check.inspect_app(app_dir, CONFIG)

    def test_workflow_scheduler_values_and_pins_agree(self):
        workflow = (PROJECT_DIR / ".github/workflows" / CONFIG["workflow"]).read_text(encoding="utf-8")
        self.assertIn(f"runs-on: {CONFIG['runner']}", workflow)
        self.assertIn(f"timeout-minutes: {CONFIG['jobTimeoutMinutes']}", workflow)
        self.assertIn(f"branches: [{CONFIG['branch']}]", workflow)
        self.assertIn(f"{CONFIG['resultRelativeDir']}/", workflow)
        self.assertIn(f"{CONFIG['buildRelativeDir']}/{CONFIG['evidenceBasename']}", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("persist-credentials: false", workflow)
        pins_by_action = {}
        for action, pin in re.findall(r"uses: (actions/[a-z-]+)@([^\s]+)", workflow):
            self.assertRegex(pin, r"^[0-9a-f]{40}$")
            pins_by_action.setdefault(action, set()).add(pin)
        self.assertEqual(set(pins_by_action), {"actions/checkout", "actions/upload-artifact"})
        self.assertTrue(all(len(pin_set) == 1 for pin_set in pins_by_action.values()))


if __name__ == "__main__":
    unittest.main()
