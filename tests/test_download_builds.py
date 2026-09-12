"""Prove artifact selection and failure preservation without GitHub credentials."""

import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import plistlib
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
import zipfile


PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
import download_builds
from scripts import native_check

CONFIG = native_check.read_json(PROJECT_DIR / "build_config.json")
SOURCE_SHA = "a" * 40
RUN_ID = 123
WORKFLOW_ID = 456
ARTIFACT_ID = 789


def run_record(identifier=RUN_ID, **changes):
    """Represent API identity fields so tests can vary trust boundaries separately."""
    record = {"id": identifier, "head_sha": SOURCE_SHA, "head_branch": CONFIG["branch"],
              "status": "completed", "conclusion": "success", "workflow_id": WORKFLOW_ID,
              "path": ".github/workflows/" + CONFIG["workflow"],
              "repository": {"full_name": CONFIG["repository"]},
              "head_repository": {"full_name": CONFIG["repository"]},
              "created_at": "2026-09-12T12:00:00Z"}
    return {**record, **changes}


def zip_bytes(members):
    """Build real archives, including intentionally unsafe entries under test."""
    destination = io.BytesIO()
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, value in members:
            if isinstance(name, str):
                member = zipfile.ZipInfo(name)
                # ZipInfo rewrites Windows separators during construction; preserve hostile raw names.
                member.filename = name
                member.orig_filename = name
            else:
                member = name
            archive.writestr(member, value)
    return destination.getvalue()


def artifact_bytes(change_manifest=None, change_evidence=None, extra_members=(), ipa_members=None,
                   omit_path=None):
    """Create a tiny complete app and original reports with matching checksums."""
    app_path = "Payload/" + CONFIG["appName"] + ".app/"
    info = {"CFBundleIdentifier": CONFIG["bundleIdentifier"],
            "MinimumOSVersion": CONFIG["deploymentTarget"],
            "CFBundleExecutable": CONFIG["appName"], "CFBundlePackageType": "APPL",
            "CFBundleSupportedPlatforms": ["iPhoneOS"], "BuildSourceSHA": SOURCE_SHA}
    # A minimal 64-bit arm64 Mach-O header identifies an arm64 executable in this test.
    executable = struct.pack("<8I", 0xFEEDFACF, 0x0100000C, 0, 2, 0, 0, 0, 0)
    members = [(app_path + "Info.plist", plistlib.dumps(info)),
               (app_path + CONFIG["appName"], executable)]
    members.extend((app_path + path, b"resource") for path in CONFIG["requiredResourcePaths"])
    ipa = zip_bytes(members if ipa_members is None else ipa_members)
    checksum = hashlib.sha256(ipa).hexdigest()
    toolchain = {key: CONFIG[key] for key in ("xcodeVersion", "xcodeBuild", "sdkVersion")}
    toolchain.update(macOS="test macOS", swiftVersion="test Swift")
    report_dir = "results/test"
    evidence = {"schemaVersion": 1, "status": "passed", "sourceSHA": SOURCE_SHA,
                "runID": str(RUN_ID), "toolchain": toolchain,
                "simulator": {"udid": "test-device", "runtimeVersion": CONFIG["sdkVersion"]},
                "resultBundle": "build/" + report_dir + "/NativeTests.xcresult",
                "commands": [{"exitCode": 0, "log": "build/" + report_dir + "/command-001.log"}],
                "tests": {"executed": len(CONFIG["requiredTestSuites"]), "failed": 0, "skipped": 0,
                          "passedBySuite": {suite: 1 for suite in CONFIG["requiredTestSuites"]}},
                "release": {"status": "passed", "bundleIdentifier": CONFIG["bundleIdentifier"],
                            "minimumOSVersion": CONFIG["deploymentTarget"], "architectures": ["arm64"],
                            "ipaSHA256": checksum, "resources": CONFIG["requiredResourcePaths"]}}
    manifest = {key: CONFIG[key] for key in ("repository", "workflow", "branch", "artifactName",
                "ipaBasename", "bundleIdentifier", "deploymentTarget", "evidenceBasename")}
    manifest.update(schemaVersion=1, sourceSHA=SOURCE_SHA, runID=str(RUN_ID), ipaSHA256=checksum,
                    toolchain=toolchain, resultBundle=report_dir + "/NativeTests.xcresult")
    if change_manifest:
        change_manifest(manifest)
    if change_evidence:
        change_evidence(evidence)
    test_nodes = [{"nodeType": "Test Suite", "name": suite, "children": [
        {"nodeType": "Test Case", "name": "testPlayback", "result": "Passed"}]
        } for suite in CONFIG["requiredTestSuites"]]
    outer_members = [("artifact/" + CONFIG["ipaBasename"], ipa),
                     ("artifact/" + CONFIG["manifestBasename"], json.dumps(manifest)),
                     ("artifact/" + CONFIG["evidenceBasename"], json.dumps(evidence)),
                     ("artifact/" + CONFIG["checksumBasename"], checksum + "  " + CONFIG["ipaBasename"] + "\n"),
                     (report_dir + "/NativeTests.xcresult/Info.plist", plistlib.dumps({"version": 1})),
                     (report_dir + "/test-results.json", json.dumps({"testNodes": test_nodes})),
                     (report_dir + "/command-001.log", "native command succeeded")]
    return zip_bytes([(name, value) for name, value in outer_members if name != omit_path] + list(extra_members))


class FakeRunner:
    """Supply API pages and raw binary downloads while recording argument boundaries."""

    def __init__(self, archive=None):
        self.archive = artifact_bytes() if archive is None else archive
        self.run_records = [run_record()]
        self.calls = []
        self.failure = None
        self.change_artifact = None

    def __call__(self, arguments, **options):
        self.calls.append((arguments, options))
        if self.failure:
            raise self.failure
        endpoint = arguments[2]
        if endpoint.endswith("/zip"):
            output = self.archive
        elif "/artifacts?" in endpoint:
            artifact = {"id": ARTIFACT_ID, "name": CONFIG["artifactName"], "expired": False,
                        "size_in_bytes": len(self.archive),
                        "digest": "sha256:" + hashlib.sha256(self.archive).hexdigest(),
                        "workflow_run": {"id": RUN_ID, "head_sha": SOURCE_SHA, "head_branch": CONFIG["branch"]}}
            if self.change_artifact:
                self.change_artifact(artifact)
            output = json.dumps({"total_count": 1, "artifacts": [artifact]}).encode()
        elif "/runs?" in endpoint:
            query_by_name = parse_qs(urlsplit(endpoint).query)
            page = int(next(iter(query_by_name["page"])))
            page_size = int(next(iter(query_by_name["per_page"])))
            start_index = (page - 1) * page_size
            output = json.dumps({"total_count": len(self.run_records),
                                 "workflow_runs": self.run_records[start_index:start_index + page_size]}).encode()
        elif endpoint.endswith("/runs/" + str(RUN_ID)):
            output = json.dumps(next(iter(self.run_records))).encode()
        else:
            output = json.dumps({"id": WORKFLOW_ID, "path": ".github/workflows/" + CONFIG["workflow"]}).encode()
        options["stdout"].write(output)
        return subprocess.CompletedProcess(arguments, 0)


class RunSelectionTests(unittest.TestCase):
    def test_selects_newest_success_independent_of_api_order(self):
        earlier = run_record(identifier=RUN_ID - 1)
        newest = run_record(identifier=RUN_ID + 1)
        selected = download_builds.select_run([earlier, newest, run_record(conclusion="failure")],
                                               config=CONFIG)
        self.assertEqual(selected, newest)

    def test_explicit_run_and_sha_never_fall_back(self):
        for identifier, source_sha in ((999, None), (None, "b" * 40), (RUN_ID, "b" * 40)):
            with self.subTest(identifier=identifier, source_sha=source_sha):
                with self.assertRaises(download_builds.DownloadError):
                    download_builds.select_run([run_record()], identifier, source_sha, CONFIG)

    def test_rejects_wrong_run_identity_or_status(self):
        for key, value in (("head_branch", "wrong"), ("path", "wrong.yml"),
                           ("repository", {"full_name": "other/repo"}),
                           ("head_repository", {"full_name": "other/repo"}),
                           ("status", "in_progress"), ("conclusion", "failure")):
            with self.subTest(key=key):
                with self.assertRaises(download_builds.DownloadError):
                    download_builds.select_run([run_record(**{key: value})], RUN_ID, SOURCE_SHA, CONFIG)


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.output_patch = patch("builtins.print")
        self.print_mock = self.output_patch.start()
        self.addCleanup(self.output_patch.stop)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project_dir = Path(self.temporary.name)
        self.old_dir = self.project_dir / "GH_builds" / "previous"
        self.old_dir.mkdir(parents=True)
        self.old_filename = self.old_dir / CONFIG["ipaBasename"]
        self.old_filename.write_bytes(b"previous usable IPA")
        self.evidence_filename = self.project_dir / "build" / CONFIG["evidenceBasename"]
        self.evidence_filename.parent.mkdir()
        self.evidence_filename.write_bytes(b"previous evidence")

    def download(self, runner, **selection):
        return download_builds.download_build(project_dir=self.project_dir, config=CONFIG,
                                               runner=runner, **selection)

    def assert_preserved(self):
        self.assertEqual(self.old_filename.read_bytes(), b"previous usable IPA")
        self.assertEqual(self.evidence_filename.read_bytes(), b"previous evidence")
        self.assertEqual(list(self.old_dir.parent.iterdir()), [self.old_dir])

    def test_download_preserves_original_reports_and_reuses_verified_run(self):
        runner = FakeRunner()
        published_dir = self.download(runner, requested_run_id=RUN_ID, requested_sha=SOURCE_SHA)
        self.assertTrue((published_dir / "artifact" / CONFIG["ipaBasename"]).is_file())
        self.assertTrue((published_dir / "results/test/test-results.json").is_file())
        self.assertEqual(self.evidence_filename.read_bytes(),
                         (published_dir / "artifact" / CONFIG["evidenceBasename"]).read_bytes())
        self.assertEqual(self.download(runner, requested_run_id=RUN_ID), published_dir)
        self.assertEqual(self.old_filename.read_bytes(), b"previous usable IPA")
        self.assertTrue(all(call[0][:2] == ["gh", "api"] for call in runner.calls))
        self.assertTrue(all(call[1]["timeout"] > 0 for call in runner.calls))

    def test_missing_selection_and_wrong_workflow_id_preserve_previous(self):
        for change in ({"head_sha": "b" * 40}, {"id": RUN_ID + 1}, {"workflow_id": WORKFLOW_ID + 1}):
            with self.subTest(change=change):
                runner = FakeRunner()
                runner.run_records = [run_record(**change)]
                with self.assertRaises(download_builds.DownloadError):
                    self.download(runner, requested_run_id=RUN_ID, requested_sha=SOURCE_SHA)
                self.assert_preserved()

    def test_timeout_and_gh_error_preserve_previous_without_exposing_secrets(self):
        for failure in (subprocess.TimeoutExpired(["gh"], 1, stderr="secret-token"),
                        subprocess.CalledProcessError(1, ["gh"], stderr="secret-token"),
                        FileNotFoundError("secret-token")):
            with self.subTest(failure=type(failure).__name__):
                runner = FakeRunner()
                runner.failure = failure
                with self.assertRaises(download_builds.DownloadError) as caught:
                    self.download(runner)
                self.assertNotIn("secret-token", str(caught.exception))
                self.assert_preserved()

    def test_manifest_checksum_and_evidence_mismatch_preserve_previous(self):
        modifications = [({"sourceSHA": "b" * 40}, None), ({"ipaSHA256": "0" * 64}, None),
                         ({"repository": "other/repo"}, None), ({"runID": "999"}, None),
                         ({"bundleIdentifier": "wrong"}, None), (None, {"runID": "999"}),
                         (None, {"sourceSHA": "b" * 40}), (None, {"status": "failed"})]
        for manifest_change, evidence_change in modifications:
            with self.subTest(manifest=manifest_change, evidence=evidence_change):
                archive = artifact_bytes(
                    change_manifest=(lambda value: value.update(manifest_change)) if manifest_change else None,
                    change_evidence=(lambda value: value.update(evidence_change)) if evidence_change else None)
                with self.assertRaises(download_builds.DownloadError):
                    self.download(FakeRunner(archive))
                self.assert_preserved()

    def test_api_digest_size_expiry_and_identity_are_required(self):
        for change in ({"digest": "sha256:" + "0" * 64}, {"digest": None},
                       {"size_in_bytes": 1}, {"expired": True},
                       {"workflow_run": {"id": 999, "head_sha": SOURCE_SHA, "head_branch": CONFIG["branch"]}}):
            with self.subTest(change=change):
                runner = FakeRunner()
                runner.change_artifact = lambda value: value.update(change)
                with self.assertRaises(download_builds.DownloadError):
                    self.download(runner)
                self.assert_preserved()

    def test_rejects_unsafe_outer_and_inner_archive_paths(self):
        unsafe_paths = ["../escape", "/escape", "C:/escape", "C:escape", "folder\\escape",
                        "folder/file:stream", "folder/../escape", "folder/./escape", "folder//escape",
                        "folder/CON", "folder/trailing.", "folder/trailing "]
        for path in unsafe_paths:
            for inner in (False, True):
                with self.subTest(path=path, inner=inner):
                    archive = artifact_bytes(ipa_members=[(path, b"bad")]) if inner else artifact_bytes(extra_members=[(path, b"bad")])
                    with self.assertRaises(download_builds.DownloadError):
                        self.download(FakeRunner(archive))
                    self.assert_preserved()

    def test_rejects_duplicate_case_and_symlink_members(self):
        symlink = zipfile.ZipInfo("link")
        symlink.create_system = 3
        symlink.external_attr = (stat.S_IFLNK | 0o777) << 16
        for extra_members in ([("artifact/MANIFEST.JSON", b"duplicate")], [(symlink, b"../outside")],
                              [("collision", b"file"), ("collision/child", b"nested")]):
            with self.subTest(extra_members=str(extra_members)):
                with self.assertRaises(download_builds.DownloadError):
                    self.download(FakeRunner(artifact_bytes(extra_members=extra_members)))
                self.assert_preserved()

    def test_rejects_malformed_ipa_wrong_app_and_missing_reports(self):
        for archive in (b"not a ZIP", artifact_bytes(ipa_members=[("Payload/Other.app/file", b"bad")]),
                        artifact_bytes(omit_path="results/test/test-results.json"),
                        artifact_bytes(omit_path="results/test/command-001.log")):
            with self.subTest(size=len(archive)):
                with self.assertRaises(download_builds.DownloadError):
                    self.download(FakeRunner(archive))
                self.assert_preserved()

    def test_publication_failure_preserves_previous(self):
        with patch.object(Path, "rename", side_effect=OSError("simulated publication failure")):
            with self.assertRaises(download_builds.DownloadError):
                self.download(FakeRunner())
        self.assert_preserved()

    def test_archive_count_and_expanded_size_limits_preserve_previous(self):
        for key in ("maximumMembers", "maximumExpandedBytes", "maximumMemberBytes"):
            with self.subTest(key=key):
                config = copy.deepcopy(CONFIG)
                config["downloadLimit"][key] = 1
                with self.assertRaises(download_builds.DownloadError):
                    download_builds.download_build(project_dir=self.project_dir, config=config, runner=FakeRunner())
                self.assert_preserved()

    def test_actual_ipa_source_sha_must_match_selected_run(self):
        with zipfile.ZipFile(io.BytesIO(artifact_bytes())) as archive:
            ipa = archive.read("artifact/" + CONFIG["ipaBasename"])
        with zipfile.ZipFile(io.BytesIO(ipa)) as archive:
            members = [(member.filename, archive.read(member)) for member in archive.infolist()]
        for source_sha in (None, "b" * 40):
            with self.subTest(source_sha=source_sha):
                modified_members = []
                for path, value in members:
                    if path.endswith("/Info.plist"):
                        info = plistlib.loads(value)
                        info["BuildSourceSHA"] = source_sha or ""
                        value = plistlib.dumps(info)
                    modified_members.append((path, value))
                with self.assertRaises(download_builds.DownloadError):
                    self.download(FakeRunner(artifact_bytes(ipa_members=modified_members)))
                self.assert_preserved()

    def test_pagination_checks_all_pages_and_refuses_unbounded_selection(self):
        runner = FakeRunner()
        runner.run_records = [run_record(identifier=RUN_ID - 1), run_record()]
        config = copy.deepcopy(CONFIG)
        config["downloadLimit"]["apiPageSize"] = 1
        config["downloadLimit"]["maximumApiPages"] = 1
        with self.assertRaises(download_builds.DownloadError):
            download_builds.download_build(project_dir=self.project_dir, config=config, runner=runner)
        self.assert_preserved()
        config["downloadLimit"]["maximumApiPages"] = 2
        published_dir = download_builds.download_build(project_dir=self.project_dir, config=config, runner=runner,
                                                       requested_sha=SOURCE_SHA)
        self.assertTrue((published_dir / "artifact" / CONFIG["ipaBasename"]).is_file())
        self.assertTrue(any("page=2" in call[0][2] for call in runner.calls))
        self.assertTrue(any("head_sha=" + SOURCE_SHA in call[0][2] for call in runner.calls))

    def test_changed_previously_published_content_is_never_overwritten(self):
        runner = FakeRunner()
        published_dir = self.download(runner)
        ipa_filename = published_dir / "artifact" / CONFIG["ipaBasename"]
        ipa_filename.write_bytes(b"locally changed IPA")
        with self.assertRaises(download_builds.DownloadError):
            self.download(runner)
        self.assertEqual(ipa_filename.read_bytes(), b"locally changed IPA")
        self.assertEqual(self.old_filename.read_bytes(), b"previous usable IPA")

    def test_missing_configuration_is_reported_without_traceback_or_raw_error(self):
        with patch.object(download_builds.native_check, "read_json", side_effect=FileNotFoundError("secret-token")):
            error_output = io.StringIO()
            with patch.object(sys, "argv", ["download_builds.py"]), patch.object(sys, "stderr", error_output):
                self.assertEqual(download_builds.main(), 1)
            message = self.print_mock.call_args.args[0]
            self.assertIn("Download failed:", message)
            self.assertNotIn("Traceback", message)
            self.assertNotIn("secret-token", message)
            self.assert_preserved()

    @unittest.skipUnless(os.name == "nt", "Windows junction creation requires cmd.exe")
    def test_windows_junction_output_is_rejected_without_writing_through_it(self):
        with tempfile.TemporaryDirectory() as external_dir:
            junction_dir = self.project_dir / "linked-download"
            result = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(junction_dir), external_dir],
                                    capture_output=True, timeout=CONFIG["timeoutByCommand"]["query"])
            self.assertEqual(result.returncode, 0, result.stderr)
            try:
                config = copy.deepcopy(CONFIG)
                config["downloadRelativeDir"] = junction_dir.name
                with self.assertRaises(download_builds.DownloadError):
                    download_builds.download_build(project_dir=self.project_dir, config=config, runner=FakeRunner())
                self.assertEqual(list(Path(external_dir).iterdir()), [])
                self.assert_preserved()
            finally:
                junction_dir.rmdir()


class StreamingProcessTests(unittest.TestCase):
    def test_actual_process_timeout_kills_child(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            with (Path(temporary_dir) / "stdout.bin").open("wb") as destination:
                with patch.object(download_builds.subprocess, "Popen", wraps=subprocess.Popen) as spawn:
                    with self.assertRaises(subprocess.TimeoutExpired):
                        download_builds.bounded_process(
                            [sys.executable, "-c", "import time; time.sleep(30)"], cwd=temporary_dir,
                            stdout=destination, stderr=subprocess.DEVNULL, timeout=0.1,
                            maximum_output_bytes=CONFIG["downloadLimit"]["maximumJsonBytes"], poll_seconds=0.01)
                    self.assertTrue(spawn.called)
            # A closed output handle also confirms the killed process released its redirected file.
            (Path(temporary_dir) / "stdout.bin").unlink()

    def test_actual_process_output_limit_stops_stream(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            with (Path(temporary_dir) / "stdout.bin").open("wb") as destination:
                with self.assertRaises(download_builds.DownloadError):
                    download_builds.bounded_process(
                        [sys.executable, "-c", "import sys,time; sys.stdout.buffer.write(b'x'*4096); sys.stdout.flush(); time.sleep(30)"],
                        cwd=temporary_dir, stdout=destination, stderr=subprocess.DEVNULL,
                        timeout=CONFIG["timeoutByCommand"]["query"], maximum_output_bytes=1024, poll_seconds=0.01)


class LauncherTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "Windows launcher execution requires cmd.exe")
    def test_batch_uses_own_directory_and_forwards_arguments_and_exit_status(self):
        with tempfile.TemporaryDirectory(prefix="launcher with space ") as temporary_dir:
            launcher_dir = Path(temporary_dir)
            (launcher_dir / "download_builds.bat").write_bytes((PROJECT_DIR / "download_builds.bat").read_bytes())
            (launcher_dir / "download_builds.py").write_text(
                "import json, os, sys\nprint(json.dumps([os.getcwd(), sys.argv[1:]]))\nsys.exit(7)\n",
                encoding="utf-8")
            result = subprocess.run(["cmd.exe", "/d", "/c", str(launcher_dir / "download_builds.bat"),
                                     "--run-id", str(RUN_ID), "--sha", SOURCE_SHA],
                                    cwd=PROJECT_DIR, capture_output=True, text=True,
                                    timeout=CONFIG["timeoutByCommand"]["query"])
            self.assertEqual(result.returncode, 7, result.stderr)
            directory, arguments = json.loads(result.stdout.strip())
            self.assertEqual(Path(directory), launcher_dir)
            self.assertEqual(arguments, ["--run-id", str(RUN_ID), "--sha", SOURCE_SHA])


if __name__ == "__main__":
    unittest.main()
