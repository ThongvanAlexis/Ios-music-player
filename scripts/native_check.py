"""Build, test and package current-source iOS artifacts with inspectable evidence."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import plistlib
import re
import shutil
import struct
import subprocess
import sys
import time
import uuid
import wave
import zipfile


PROJECT_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILENAME = PROJECT_DIR / "build_config.json"
EVIDENCE_SCHEMA_VERSION = 1
SHA_PATTERN = re.compile(r"[0-9a-f]{40}")
CLASS_PATTERN = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")
PCM_SAMPLE_WIDTH = 2
MONO_CHANNEL_COUNT = 1
ERROR_TAIL_CHARACTER_COUNT = 6000


class NativeCheckError(RuntimeError):
    """Explain an unmet build or evidence requirement without claiming success."""


def read_json(filename: Path) -> dict:
    """Read structured configuration or evidence without platform-specific tools."""
    with filename.open(encoding="utf-8") as source:
        return json.load(source)


def write_json(filename: Path, value: dict) -> None:
    """Publish a complete report atomically so partial writes cannot look successful."""
    filename.parent.mkdir(parents=True, exist_ok=True)
    temporary_filename = filename.with_name(filename.name + ".tmp")
    temporary_filename.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary_filename.replace(filename)


def require(condition: bool, message: str) -> None:
    """Turn a failed acceptance condition into an actionable command failure."""
    if not condition:
        raise NativeCheckError(message)


def contained_path(root_dir: Path, relative_path: str) -> Path:
    """Reject configuration paths that would write outside the checkout."""
    filename = (root_dir / relative_path).resolve()
    require(filename.is_relative_to(root_dir.resolve()) and filename != root_dir.resolve(),
            f"Path must stay inside the project: {relative_path}")
    return filename


class CommandRunner:
    """Run bounded argument-array commands and retain output for failed native runs."""

    def __init__(self, project_dir: Path, config: dict, log_dir: Path | None = None):
        self.project_dir = project_dir
        self.config = config
        self.log_dir = log_dir
        self.environment_by_name = dict(os.environ)
        self.environment_by_name["DEVELOPER_DIR"] = config["developerDirectory"]
        self.commands = []

    def run(self, arguments: list[str], category: str = "query", capture: bool = True) -> str:
        """Execute a command with a timeout and include its identity in the evidence."""
        started_at = time.monotonic()
        command = {"arguments": arguments, "category": category}
        self.commands.append(command)
        log_filename = None
        try:
            if capture:
                result = subprocess.run(arguments, cwd=self.project_dir,
                                        env=self.environment_by_name, text=True,
                                        encoding="utf-8", errors="replace", capture_output=True,
                                        timeout=self.config["timeoutByCommand"][category], check=False)
                output = result.stdout
                error_output = result.stderr
            else:
                require(self.log_dir is not None, "Native command log directory is missing.")
                self.log_dir.mkdir(parents=True, exist_ok=True)
                log_filename = self.log_dir / f"command-{len(self.commands):03d}.log"
                print("Running: " + " ".join(arguments), flush=True)
                with log_filename.open("w", encoding="utf-8") as destination:
                    result = subprocess.run(arguments, cwd=self.project_dir,
                                            env=self.environment_by_name, stdout=destination,
                                            stderr=subprocess.STDOUT,
                                            timeout=self.config["timeoutByCommand"][category], check=False)
                output = ""
                error_output = ""
                command["log"] = log_filename.relative_to(self.project_dir).as_posix()
            command["exitCode"] = result.returncode
            if result.returncode:
                if log_filename:
                    with log_filename.open("rb") as source:
                        source.seek(max(0, log_filename.stat().st_size - ERROR_TAIL_CHARACTER_COUNT))
                        error_output = source.read().decode("utf-8", errors="replace")
                raise NativeCheckError(f"Command failed ({result.returncode}): {' '.join(arguments)}\n"
                                       + (output + error_output)[-ERROR_TAIL_CHARACTER_COUNT:])
            return output.strip()
        except subprocess.TimeoutExpired as error:
            command["timedOut"] = True
            raise NativeCheckError(f"Command timed out: {' '.join(arguments)}") from error
        finally:
            command["elapsedSeconds"] = round(time.monotonic() - started_at, 3)


def resolve_sha(runner: CommandRunner, reference: str) -> str:
    """Resolve a commit without accepting an option or arbitrary revision expression."""
    require(reference == "HEAD" or SHA_PATTERN.fullmatch(reference) is not None,
            "Expected SHA must be HEAD or a full lowercase commit SHA.")
    source_sha = runner.run(["git", "rev-parse", "--verify", f"{reference}^{{commit}}"])
    require(SHA_PATTERN.fullmatch(source_sha) is not None, "Git did not return a full commit SHA.")
    return source_sha


def select_simulator(device_by_runtime: dict, runtime_records: list[dict]) -> dict:
    """Choose a usable iPhone explicitly, independent of simctl's output ordering."""
    runtime_by_identifier = {record["identifier"]: record for record in runtime_records
                             if record.get("isAvailable") and ".iOS-" in record["identifier"]}
    candidates = []
    for runtime_identifier, devices in device_by_runtime.items():
        if runtime_identifier not in runtime_by_identifier:
            continue
        runtime = runtime_by_identifier[runtime_identifier]
        for device in devices:
            if device.get("isAvailable") and device.get("name", "").startswith("iPhone"):
                uuid.UUID(device["udid"])
                candidates.append({**device, "runtimeIdentifier": runtime_identifier,
                                   "runtimeVersion": runtime["version"]})
    require(bool(candidates), "No available iOS iPhone simulator. Install a compatible runtime.")
    candidates.sort(key=lambda device: (tuple(int(part) for part in device["runtimeVersion"].split(".")),
                                        device["name"], device["udid"]), reverse=True)
    return next(iter(candidates))


def read_test_counts(result: dict, required_suites: list[str]) -> dict:
    """Count executed test cases from xcresult and reject failures, skips and absent suites."""
    count_by_suite = {suite: 0 for suite in required_suites}
    executed_test_count = 0

    def visit(node: dict, ancestors: tuple[str, ...]) -> None:
        nonlocal executed_test_count
        labels = ancestors + (node.get("name", ""), node.get("nodeIdentifier", ""))
        if node.get("nodeType") == "Test Case":
            require(node.get("result") == "Passed",
                    f"Native test did not pass: {node.get('nodeIdentifier', node.get('name'))}: {node.get('result')}")
            executed_test_count += 1
            token_set = set(re.findall(r"[A-Za-z_][A-Za-z_0-9]*", "/".join(labels)))
            for suite in required_suites:
                if set(suite.split("/")).issubset(token_set):
                    count_by_suite[suite] += 1
            return
        for child in node.get("children", []):
            visit(child, labels)

    for node in result.get("testNodes", []):
        visit(node, ())
    require(executed_test_count > 0, "xcresult contains zero executed tests.")
    for suite, count in count_by_suite.items():
        require(count > 0, f"No passed test cases found for requested suite {suite}.")
    return {"executed": executed_test_count, "passedBySuite": count_by_suite, "failed": 0, "skipped": 0}


def validate_evidence(evidence: dict, expected_sha: str, config: dict,
                      required_suites: list[str] | None = None) -> None:
    """Validate copied native evidence on Windows without invoking Xcode."""
    require(evidence.get("schemaVersion") == EVIDENCE_SCHEMA_VERSION, "Unknown native evidence schema.")
    require(evidence.get("status") == "passed", "Native run is missing or did not pass.")
    require(evidence.get("sourceSHA") == expected_sha, "Native evidence belongs to a different source SHA.")
    toolchain = evidence.get("toolchain", {})
    for key in ("xcodeVersion", "xcodeBuild", "sdkVersion"):
        require(toolchain.get(key) == config[key], f"Native evidence has the wrong {key}.")
    require(bool(toolchain.get("macOS")) and bool(toolchain.get("swiftVersion")), "Toolchain identity is incomplete.")
    require(bool(evidence.get("simulator", {}).get("udid")) and
            bool(evidence.get("simulator", {}).get("runtimeVersion")), "Simulator identity is missing.")
    test_result = evidence.get("tests", {})
    executed_count = test_result.get("executed")
    require(type(executed_count) is int and executed_count > 0, "Native evidence has zero or invalid test counts.")
    require(test_result.get("failed") == 0 and test_result.get("skipped") == 0,
            "Native evidence contains failed or skipped tests.")
    for suite in required_suites or config["requiredTestSuites"]:
        count = test_result.get("passedBySuite", {}).get(suite)
        require(type(count) is int and 0 < count <= executed_count, f"Missing executed tests for {suite}.")
    require(bool(evidence.get("resultBundle")), "Native result bundle identity is missing.")
    release = evidence.get("release", {})
    require(release.get("status") == "passed", "Successful unsigned Release build evidence is missing.")
    require(release.get("bundleIdentifier") == config["bundleIdentifier"], "Release bundle identity mismatch.")
    require(release.get("minimumOSVersion") == config["deploymentTarget"], "Release minimum OS mismatch.")
    require("arm64" in release.get("architectures", []), "Release is missing arm64.")
    require(re.fullmatch(r"[0-9a-f]{64}", release.get("ipaSHA256", "")) is not None, "IPA checksum is missing.")
    require(set(config["requiredResourcePaths"]).issubset(release.get("resources", [])), "Release skin resources are missing.")


def generate_fixture(filename: Path, config: dict) -> None:
    """Generate known nonzero PCM externally to the app, exercising genuine file discovery."""
    fixture = config["fixture"]
    frame_count = fixture["sampleRate"] * fixture["durationSeconds"]
    with wave.open(str(filename), "wb") as destination:
        destination.setnchannels(MONO_CHANNEL_COUNT)
        destination.setsampwidth(PCM_SAMPLE_WIDTH)
        destination.setframerate(fixture["sampleRate"])
        for frame_index in range(frame_count):
            sample = round(fixture["amplitude"] * math.sin(math.tau * fixture["frequencyHertz"] * frame_index / fixture["sampleRate"]))
            destination.writeframesraw(struct.pack("<h", sample))


def inspect_app(app_dir: Path, config: dict) -> dict:
    """Check the actual built app's platform, minimum OS and packaged skin files."""
    with (app_dir / "Info.plist").open("rb") as source:
        info = plistlib.load(source)
    require(info.get("CFBundleIdentifier") == config["bundleIdentifier"], "Built app bundle identifier is incorrect.")
    require(info.get("MinimumOSVersion") == config["deploymentTarget"], "Built app minimum OS differs from configuration.")
    require(info.get("CFBundleExecutable") == config["appName"], "Built app executable name is incorrect.")
    require(info.get("CFBundlePackageType") == "APPL", "Built product is not an iOS application.")
    require("iPhoneOS" in info.get("CFBundleSupportedPlatforms", []), "Release app is not built for a device.")
    for relative_path in config["requiredResourcePaths"]:
        resource_filename = contained_path(app_dir, relative_path)
        require(resource_filename.is_file() and resource_filename.stat().st_size > 0,
                f"Built app resource is missing: {relative_path}")
    return info


def package_app(app_dir: Path, artifact_dir: Path, config: dict) -> str:
    """Preserve executable permissions inside one immediate Payload app directory."""
    ipa_filename = artifact_dir / config["ipaBasename"]
    members = sorted(app_dir.rglob("*"), key=lambda filename: filename.relative_to(app_dir).as_posix())
    require(bool(members), "Built app is empty.")
    with zipfile.ZipFile(ipa_filename, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for filename in members:
            require(not filename.is_symlink(), f"Unexpected symlink in app product: {filename}")
            if filename.is_file():
                archive.write(filename, (Path("Payload") / app_dir.name / filename.relative_to(app_dir)).as_posix())
    with ipa_filename.open("rb") as source:
        checksum = hashlib.file_digest(source, "sha256").hexdigest()
    (artifact_dir / config["checksumBasename"]).write_text(f"{checksum}  {ipa_filename.name}\n", encoding="utf-8")
    return checksum


def run_native(arguments: argparse.Namespace, config: dict, project_dir: Path = PROJECT_DIR) -> dict:
    """Run a current-source simulator check and optional unsigned device build."""
    require(platform.system() == "Darwin", "Native tests require macOS/Xcode. Use --check-evidence for downloaded reports on Windows.")
    require(Path(config["developerDirectory"]).is_dir(), f"Pinned Xcode is missing: {config['developerDirectory']}")
    run_identifier = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex
    run_dir = contained_path(project_dir, config["resultRelativeDir"]) / run_identifier
    run_dir.mkdir(parents=True)
    runner = CommandRunner(project_dir, config, run_dir)
    evidence = {"schemaVersion": EVIDENCE_SCHEMA_VERSION, "status": "running", "startedAt": datetime.now(timezone.utc).isoformat(),
                "runID": os.environ.get("GITHUB_RUN_ID"), "runnerImage": os.environ.get("ImageVersion", "local-macOS"),
                "runnerArchitecture": platform.machine(), "commands": runner.commands}
    evidence_filename = contained_path(project_dir, config["buildRelativeDir"]) / config["evidenceBasename"]
    try:
        evidence["sourceSHA"] = resolve_sha(runner, "HEAD")
        require(not runner.run(["git", "status", "--porcelain", "--untracked-files=normal"]),
                "Commit source changes before native validation; evidence must identify an exact clean commit.")
        version_output = runner.run(["xcodebuild", "-version"])
        expected_version = f"Xcode {config['xcodeVersion']}\nBuild version {config['xcodeBuild']}"
        require(version_output == expected_version, f"Expected {expected_version}; got {version_output}.")
        sdk_version = runner.run(["xcrun", "--sdk", "iphoneos", "--show-sdk-version"])
        require(sdk_version == config["sdkVersion"], f"Expected iOS SDK {config['sdkVersion']}; got {sdk_version}.")
        evidence["toolchain"] = {"xcodeVersion": config["xcodeVersion"], "xcodeBuild": config["xcodeBuild"],
                                 "sdkVersion": sdk_version, "macOS": runner.run(["sw_vers"]),
                                 "swiftVersion": runner.run(["xcrun", "swift", "--version"])}
        devices = json.loads(runner.run(["xcrun", "simctl", "list", "devices", "available", "--json"]))
        runtimes = json.loads(runner.run(["xcrun", "simctl", "list", "runtimes", "--json"]))
        simulator = select_simulator(devices["devices"], runtimes["runtimes"])
        evidence["simulator"] = simulator
        destination = f"platform=iOS Simulator,id={simulator['udid']}"
        runner.environment_by_name["TEST_DESTINATION"] = destination
        if simulator["state"] != "Booted":
            runner.run(["xcrun", "simctl", "boot", simulator["udid"]], "simulator")
        runner.run(["xcrun", "simctl", "bootstatus", simulator["udid"], "-b"], "simulator")
        derived_dir = contained_path(project_dir, config["derivedDataRelativeDir"]) / run_identifier
        common_arguments = ["xcodebuild", "-project", config["project"], "-scheme", config["scheme"],
                            "-derivedDataPath", str(derived_dir), "-destination", destination,
                            "-parallel-testing-enabled", "NO", "CODE_SIGNING_ALLOWED=NO",
                            f"IPHONEOS_DEPLOYMENT_TARGET={config['deploymentTarget']}",
                            f"SOURCE_COMMIT_SHA={evidence['sourceSHA']}"]
        runner.run(common_arguments + ["build-for-testing"], "build", capture=False)
        build_stamp = {"sourceSHA": evidence["sourceSHA"], "destination": destination, "xcodeBuild": config["xcodeBuild"]}
        stamp_filename = derived_dir / "current-source-build.json"
        write_json(stamp_filename, build_stamp)
        app_dir = derived_dir / "Build/Products/Debug-iphonesimulator" / f"{config['appName']}.app"
        runner.run(["xcrun", "simctl", "install", simulator["udid"], str(app_dir)], "simulator")
        container_dir = Path(runner.run(["xcrun", "simctl", "get_app_container", simulator["udid"], config["bundleIdentifier"], "data"]))
        documents_dir = container_dir / "Documents"
        documents_dir.mkdir(parents=True, exist_ok=True)
        generate_fixture(documents_dir / config["fixture"]["basename"], config)
        selected_suites = [f"MusicPlayerTests/{name}" for name in arguments.suite] + [f"MusicPlayerUITests/{name}" for name in arguments.ui_suite]
        required_suites = config["requiredTestSuites"] if arguments.full or not selected_suites else selected_suites
        result_dir = run_dir / "NativeTests.xcresult"
        require(read_json(stamp_filename) == build_stamp and resolve_sha(runner, "HEAD") == evidence["sourceSHA"],
                "Build-for-testing does not match the current source/destination/toolchain.")
        # The app container must exist before an external WAV can be injected. The full
        # route still invokes xcodebuild test; selected checks reuse this invocation's build.
        test_action = "test" if arguments.full else "test-without-building"
        test_arguments = common_arguments + ["-resultBundlePath", str(result_dir)]
        if not arguments.full:
            test_arguments += [f"-only-testing:{suite}" for suite in required_suites]
        runner.run(test_arguments + [test_action], "test", capture=False)
        require(result_dir.is_dir(), "Native test result bundle is missing.")
        result = json.loads(runner.run(["xcrun", "xcresulttool", "get", "test-results", "tests", "--path", str(result_dir)]))
        write_json(run_dir / "test-results.json", result)
        evidence["tests"] = read_test_counts(result, required_suites)
        evidence["resultBundle"] = result_dir.relative_to(project_dir).as_posix()
        evidence["requestedSuites"] = required_suites
        if arguments.release:
            release_arguments = ["xcodebuild", "-project", config["project"], "-scheme", config["scheme"],
                                 "-configuration", "Release", "-sdk", "iphoneos", "-destination", "generic/platform=iOS",
                                 "-derivedDataPath", str(derived_dir), "CODE_SIGNING_ALLOWED=NO", "CODE_SIGNING_REQUIRED=NO",
                                 f"IPHONEOS_DEPLOYMENT_TARGET={config['deploymentTarget']}",
                                 f"SOURCE_COMMIT_SHA={evidence['sourceSHA']}", "build"]
            runner.run(release_arguments, "build", capture=False)
            app_dir = derived_dir / "Build/Products/Release-iphoneos" / f"{config['appName']}.app"
            info = inspect_app(app_dir, config)
            require(info.get("BuildSourceSHA") == evidence["sourceSHA"], "Built app source SHA is missing or incorrect.")
            executable_filename = app_dir / config["appName"]
            architectures = runner.run(["xcrun", "lipo", "-archs", str(executable_filename)]).split()
            require("arm64" in architectures, "Built executable does not contain arm64.")
            load_command = runner.run(["xcrun", "vtool", "-show-build", str(executable_filename)])
            require(re.search(r"\bplatform\s+IOS\b", load_command) is not None, "Mach-O is not an iOS device executable.")
            require(re.search(r"\bminos\s+" + re.escape(config["deploymentTarget"]) + r"(?:\.0)?\s", load_command + "\n") is not None,
                    "Mach-O minimum OS differs from the configured deployment target.")
            (run_dir / "release-load-commands.txt").write_text(load_command + "\n", encoding="utf-8")
            artifact_dir = contained_path(project_dir, config["artifactRelativeDir"])
            artifact_dir.mkdir(parents=True, exist_ok=True)
            checksum = package_app(app_dir, artifact_dir, config)
            evidence["release"] = {"status": "passed", "bundleIdentifier": info["CFBundleIdentifier"],
                                   "minimumOSVersion": info["MinimumOSVersion"], "architectures": architectures,
                                   "resources": config["requiredResourcePaths"], "ipaSHA256": checksum}
            manifest = {"schemaVersion": 1, "sourceSHA": evidence["sourceSHA"], "runID": evidence["runID"],
                        "repository": config["repository"], "workflow": config["workflow"], "branch": config["branch"],
                        "artifactName": config["artifactName"], "ipaBasename": config["ipaBasename"],
                        "ipaSHA256": checksum, "bundleIdentifier": config["bundleIdentifier"],
                        "deploymentTarget": config["deploymentTarget"], "toolchain": evidence["toolchain"],
                        "evidenceBasename": config["evidenceBasename"],
                        "resultBundle": result_dir.relative_to(contained_path(project_dir, config["buildRelativeDir"])).as_posix()}
            write_json(artifact_dir / config["manifestBasename"], manifest)
        require(resolve_sha(runner, "HEAD") == evidence["sourceSHA"], "Source commit changed during native validation.")
        require(not runner.run(["git", "status", "--porcelain", "--untracked-files=normal"]), "Source changed during native validation.")
        evidence["status"] = "passed"
        if arguments.release:
            validate_evidence(evidence, evidence["sourceSHA"], config, required_suites)
        return evidence
    except Exception as error:
        evidence["status"] = "failed"
        evidence["error"] = str(error)
        raise
    finally:
        evidence["finishedAt"] = datetime.now(timezone.utc).isoformat()
        write_json(evidence_filename, evidence)
        write_json(run_dir / config["evidenceBasename"], evidence)
        if evidence["status"] == "passed" and arguments.release:
            shutil.copy2(evidence_filename, contained_path(project_dir, config["artifactRelativeDir"]) / config["evidenceBasename"])


def main() -> int:
    """Expose native execution and portable evidence checking as separate command paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", action="append", default=[], metavar="CLASS")
    parser.add_argument("--ui-suite", action="append", default=[], metavar="CLASS")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--release", action="store_true")
    parser.add_argument("--check-evidence", type=Path)
    parser.add_argument("--expected-sha", default="HEAD")
    parser.add_argument("--ci-output", action="store_true", help="Write configured artifact paths to GITHUB_OUTPUT.")
    arguments = parser.parse_args()
    try:
        config = read_json(CONFIG_FILENAME)
        require(config.get("schemaVersion") == 1, "Unknown build configuration schema.")
        for name in arguments.suite + arguments.ui_suite:
            require(CLASS_PATTERN.fullmatch(name) is not None, f"Invalid test class name: {name}")
        if arguments.ci_output:
            with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
                for key in ("artifactName", "artifactRelativeDir", "resultRelativeDir", "retentionDays"):
                    output.write(f"{key}={config[key]}\n")
            return 0
        if arguments.check_evidence:
            runner = CommandRunner(PROJECT_DIR, config)
            expected_sha = resolve_sha(runner, arguments.expected_sha)
            validate_evidence(read_json(arguments.check_evidence), expected_sha, config)
            print(f"Native simulator and Release evidence passed for {expected_sha}. Physical device checks remain separate.")
            return 0
        result = run_native(arguments, config)
        print(f"Native checks passed for {result['sourceSHA']}: {result['tests']['executed']} tests.")
        return 0
    except (NativeCheckError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"Native check failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
