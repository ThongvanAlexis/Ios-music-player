"""Retrieve a verified native build through the installed GitHub CLI."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import plistlib
import re
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import time
import unicodedata
from urllib.parse import urlencode
import zipfile

from scripts import native_check


PROJECT_DIR = Path(__file__).resolve().parent
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
WINDOWS_RESERVED_NAME_SET = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"} | {
    prefix + suffix for prefix in ("COM", "LPT") for suffix in "123456789¹²³"}
MACH_HEADER_BYTES = 32
MACH_MAGIC_64 = 0xFEEDFACF
MACH_CPU_ARM64 = 0x0100000C
MACH_EXECUTE = 2
ZIP_MODE_SHIFT = 16
WINDOWS_REPARSE_ATTRIBUTE = 0x400
BUILD_IDENTIFIER_PREFIX_LENGTH = 12


class DownloadError(RuntimeError):
    """Describe a failed download without exposing GitHub's credential-bearing output."""


def require(condition: bool, message: str) -> None:
    """Reject an unmet validation check before a build can be published."""
    if not condition:
        raise DownloadError(message)


def read_json(filename: Path, config: dict) -> dict:
    """Bound structured input and reject invalid or non-object JSON."""
    require(filename.stat().st_size <= config["downloadLimit"]["maximumJsonBytes"],
            "JSON exceeds the configured size limit.")
    try:
        result = json.loads(filename.read_text(encoding="utf-8"))
        require(isinstance(result, dict), "Expected a JSON object.")
        return result
    except (ValueError, UnicodeError) as error:
        raise DownloadError("Invalid JSON in GitHub metadata or downloaded reports.") from error


def select_run(run_records, requested_run_id=None, requested_sha=None, config=None):
    """Choose only the requested successful source from the configured workflow."""
    config = config if config is not None else native_check.read_json(PROJECT_DIR / "build_config.json")
    if requested_sha is not None:
        require(isinstance(requested_sha, str) and native_check.SHA_PATTERN.fullmatch(requested_sha),
                "--sha requires a full lowercase 40-character commit SHA.")
    if requested_run_id is not None:
        require(re.fullmatch(r"[1-9][0-9]*", str(requested_run_id)), "--run-id requires a positive run number.")
    candidates = []
    for record in run_records:
        if not isinstance(record, dict):
            continue
        if record.get("status") != "completed" or record.get("conclusion") != "success":
            continue
        if record.get("repository", {}).get("full_name") != config["repository"]:
            continue
        if record.get("head_repository", {}).get("full_name") != config["repository"]:
            continue
        if record.get("head_branch") != config["branch"] or record.get("path") != ".github/workflows/" + config["workflow"]:
            continue
        if "workflowId" in config and record.get("workflow_id") != config["workflowId"]:
            continue
        if type(record.get("id")) is not int or record["id"] <= 0:
            continue
        if not native_check.SHA_PATTERN.fullmatch(str(record.get("head_sha", ""))):
            continue
        if requested_run_id is not None and str(record["id"]) != str(requested_run_id):
            continue
        if requested_sha is not None and record["head_sha"] != requested_sha:
            continue
        try:
            created_at = datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
            require(created_at.tzinfo is not None, "GitHub run creation time lacks a timezone.")
        except (KeyError, ValueError, TypeError) as error:
            raise DownloadError("GitHub run creation time is invalid.") from error
        candidates.append((created_at, record["id"], record))
    require(bool(candidates), "No matching completed successful run. Check --run-id/--sha and retry after CI succeeds; no other source was selected.")
    candidates.sort(key=lambda candidate: candidate[:2], reverse=True)
    return next(iter(candidates))[-1]


def safe_relative_path(value: str) -> PurePosixPath:
    """Reject Windows aliases and archive paths that can escape or collide on disk."""
    require(isinstance(value, str) and bool(value) and "\\" not in value,
            "Unsafe archive or report path.")
    path_text = value.removesuffix("/")
    parts = path_text.split("/")
    for part in parts:
        require(part not in ("", ".", "..") and not part.endswith((".", " ")),
                "Unsafe archive or report path.")
        require(not any(ord(character) < 32 or character in '<>:"|?*' for character in part),
                "Unsafe archive or report path.")
        require(part.split(".")[0].upper() not in WINDOWS_RESERVED_NAME_SET,
                "Archive path uses a Windows reserved filename.")
    return PurePosixPath(*parts)


def local_path(root_dir: Path, relative_path: str) -> Path:
    """Keep local output inside the intended root, including through existing links."""
    path = root_dir.joinpath(*safe_relative_path(relative_path).parts)
    for candidate in (root_dir, path, *path.parents):
        if candidate.exists() or candidate.is_symlink():
            require(not candidate.is_symlink() and
                    not getattr(candidate.lstat(), "st_file_attributes", 0) & WINDOWS_REPARSE_ATTRIBUTE,
                    "Output path must not contain a symbolic link or Windows reparse point.")
    root_dir = root_dir.resolve()
    require(path.resolve().is_relative_to(root_dir) and path.resolve() != root_dir,
            "Output path must remain inside its project directory.")
    return path


def bounded_process(arguments, *, cwd, stdout, stderr, timeout, maximum_output_bytes, poll_seconds):
    """Stream CLI output to disk with a deadline and a running byte limit."""
    process = subprocess.Popen(arguments, cwd=cwd, stdout=stdout, stderr=stderr)
    deadline = time.monotonic() + timeout
    try:
        while process.poll() is None:
            if time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired(arguments, timeout)
            require(os.fstat(stdout.fileno()).st_size <= maximum_output_bytes,
                    "GitHub output exceeds the configured download limit.")
            time.sleep(poll_seconds)
        require(os.fstat(stdout.fileno()).st_size <= maximum_output_bytes,
                "GitHub output exceeds the configured download limit.")
        return subprocess.CompletedProcess(arguments, process.returncode)
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()


class GitHubArtifactClient:
    """Apply bounded GitHub API queries and safe error reporting using gh authentication."""

    def __init__(self, project_dir: Path, staging_dir: Path, config: dict, runner):
        self.project_dir = project_dir
        self.staging_dir = staging_dir
        self.config = config
        self.runner = runner

    def fetch(self, endpoint: str, filename: Path, *, archive=False) -> None:
        """Keep binary bytes untouched and suppress unknown CLI output that may contain secrets."""
        limit = self.config["downloadLimit"]
        category = "download" if archive else "query"
        maximum_bytes = limit["maximumArchiveBytes" if archive else "maximumJsonBytes"]
        try:
            with filename.open("wb") as destination:
                result = self.runner(["gh", "api", endpoint], cwd=self.project_dir,
                                     stdout=destination, stderr=subprocess.DEVNULL,
                                     timeout=self.config["timeoutByCommand"][category],
                                     maximum_output_bytes=maximum_bytes,
                                     poll_seconds=limit["processPollSeconds"])
            require(result.returncode == 0,
                    "GitHub request failed. Run gh auth status; if needed run gh auth login, verify repository access, then retry the same selection.")
            require(filename.stat().st_size <= maximum_bytes, "GitHub output exceeds the configured size limit.")
        except subprocess.TimeoutExpired as error:
            raise DownloadError("GitHub request timed out. Check the connection and retry the same --run-id or --sha.") from error
        except (subprocess.CalledProcessError, FileNotFoundError) as error:
            raise DownloadError("GitHub CLI could not complete the request. Install gh if missing, run gh auth login, then retry the same selection.") from error

    def query(self, endpoint: str) -> dict:
        """Decode a bounded response only after the CLI completed successfully."""
        filename = self.staging_dir / "api-response.json"
        self.fetch(endpoint, filename)
        return read_json(filename, self.config)

    def list_records(self, endpoint: str, collection_key: str, query_by_name=None) -> list[dict]:
        """Fetch every bounded page so response order or truncation cannot select another run."""
        limit = self.config["downloadLimit"]
        records = []
        identifier_set = set()
        for page in range(1, limit["maximumApiPages"] + 1):
            query_by_name = dict(query_by_name or {})
            query_by_name.update(per_page=limit["apiPageSize"], page=page)
            response = self.query(endpoint + "?" + urlencode(query_by_name))
            total = response.get("total_count")
            items = response.get(collection_key)
            require(type(total) is int and total >= 0 and isinstance(items, list), "GitHub pagination metadata is invalid.")
            require(total <= limit["apiPageSize"] * limit["maximumApiPages"],
                    "Too many GitHub results. Select an exact --run-id or narrow the --sha selection.")
            require(len(items) <= limit["apiPageSize"], "GitHub returned an oversized API page.")
            for item in items:
                require(isinstance(item, dict) and type(item.get("id")) is int and item["id"] not in identifier_set,
                        "GitHub pagination returned invalid or duplicate identities; retry the same selection.")
                identifier_set.add(item["id"])
                records.append(item)
            if len(records) == total:
                return records
            require(bool(items) and len(records) < total, "GitHub result count changed; retry the same selection.")
        raise DownloadError("GitHub pagination limit reached. Select an exact --run-id.")


def inspect_zip(archive: zipfile.ZipFile, config: dict) -> list[zipfile.ZipInfo]:
    """Validate the whole archive before any member can touch the filesystem."""
    limit = config["downloadLimit"]
    members = archive.infolist()
    require(0 < len(members) <= limit["maximumMembers"], "Archive member count is outside the configured limit.")
    total_size = 0
    member_by_path = {}
    for member in members:
        require(member.orig_filename == member.filename, "Archive filename contains a NUL character.")
        path = safe_relative_path(member.filename)
        key = unicodedata.normalize("NFC", path.as_posix()).casefold()
        require(key not in member_by_path, "Archive contains duplicate or case-colliding paths.")
        mode = member.external_attr >> ZIP_MODE_SHIFT
        require(stat.S_IFMT(mode) in (0, stat.S_IFREG, stat.S_IFDIR) and
                not member.external_attr & WINDOWS_REPARSE_ATTRIBUTE,
                "Archive contains a link or unsupported special file.")
        require(not (member.flag_bits & 1), "Encrypted archive members are unsupported.")
        require(not stat.S_ISDIR(mode) or member.is_dir(), "Archive directory metadata is inconsistent.")
        require(0 <= member.file_size <= limit["maximumMemberBytes"], "Archive member exceeds its size limit.")
        require(not member.is_dir() or member.file_size == 0, "Archive directory has unexpected content.")
        total_size += member.file_size
        require(total_size <= limit["maximumExpandedBytes"], "Expanded archive exceeds its size limit.")
        member_by_path[key] = member
    for key in member_by_path:
        for parent in PurePosixPath(key).parents:
            ancestor = member_by_path.get(parent.as_posix())
            require(ancestor is None or ancestor.is_dir(), "Archive file collides with a directory.")
    return members


def extract_archive(archive_filename: Path, destination_dir: Path, config: dict) -> None:
    """Extract checked regular files into fresh staging using exclusive file creation."""
    with zipfile.ZipFile(archive_filename) as archive:
        members = inspect_zip(archive, config)
        for member in members:
            filename = local_path(destination_dir, member.filename)
            if member.is_dir():
                filename.mkdir(parents=True, exist_ok=True)
                continue
            filename.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, filename.open("xb") as destination:
                shutil.copyfileobj(source, destination, config["downloadLimit"]["streamChunkBytes"])


def sha256(filename: Path) -> str:
    """Hash bytes from disk without loading a complete IPA into memory."""
    with filename.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def validate_ipa(filename: Path, config: dict, expected_sha: str) -> None:
    """Check actual device app structure, plist, arm64 executable and required resources."""
    expected_app_path = PurePosixPath("Payload") / (config["appName"] + ".app")
    with zipfile.ZipFile(filename) as archive:
        members = inspect_zip(archive, config)
        member_by_path = {PurePosixPath(member.filename): member for member in members}
        for path in member_by_path:
            require(path == PurePosixPath("Payload") or path == expected_app_path or expected_app_path in path.parents,
                    "IPA must contain exactly one immediate expected app inside Payload.")
        plist_path = expected_app_path / "Info.plist"
        executable_path = expected_app_path / config["appName"]
        require(plist_path in member_by_path and executable_path in member_by_path, "IPA plist or executable is missing.")
        require(member_by_path[plist_path].file_size <= config["downloadLimit"]["maximumJsonBytes"],
                "IPA plist exceeds its size limit.")
        info = plistlib.loads(archive.read(member_by_path[plist_path]))
        expected_by_key = {"CFBundleIdentifier": config["bundleIdentifier"], "MinimumOSVersion": config["deploymentTarget"],
                           "CFBundleExecutable": config["appName"], "CFBundlePackageType": "APPL",
                           "BuildSourceSHA": expected_sha}
        require(all(info.get(key) == value for key, value in expected_by_key.items()) and
                "iPhoneOS" in info.get("CFBundleSupportedPlatforms", []), "IPA app identity or device platform is incorrect.")
        with archive.open(member_by_path[executable_path]) as source:
            header = source.read(MACH_HEADER_BYTES)
        require(len(header) == MACH_HEADER_BYTES, "IPA executable header is missing.")
        magic, cpu_type, cpu_subtype, file_type, command_count, command_size, flags, reserved = struct.unpack("<8I", header)
        require((magic, cpu_type, file_type) == (MACH_MAGIC_64, MACH_CPU_ARM64, MACH_EXECUTE),
                "IPA executable is not a 64-bit arm64 Mach-O application.")
        for relative_path in config["requiredResourcePaths"]:
            member = member_by_path.get(expected_app_path / safe_relative_path(relative_path))
            require(member is not None and not member.is_dir() and member.file_size > 0, "IPA required resource is missing.")
        # Reading every stream also checks CRCs for resources beyond the small identity files.
        require(archive.testzip() is None, "IPA contains corrupted member data.")


def validate_artifact(staging_dir: Path, expected_identity: dict, config=None) -> dict:
    """Tie app bytes and original native reports to the selected successful GitHub run."""
    config = config if config is not None else native_check.read_json(PROJECT_DIR / "build_config.json")
    artifact_relative_dir = PurePosixPath(config["artifactRelativeDir"]).relative_to(config["buildRelativeDir"])
    artifact_dir = local_path(staging_dir, artifact_relative_dir.as_posix())
    manifest = read_json(local_path(artifact_dir, config["manifestBasename"]), config)
    require(manifest.get("schemaVersion") == config["schemaVersion"], "Artifact manifest schema is unsupported.")
    for key in ("repository", "workflow", "branch", "artifactName", "ipaBasename", "bundleIdentifier", "deploymentTarget", "evidenceBasename"):
        require(manifest.get(key) == config[key], "Artifact manifest build identity mismatch: " + key)
    require(str(manifest.get("runID")) == str(expected_identity["id"]) and
            manifest.get("sourceSHA") == expected_identity["head_sha"], "Artifact manifest run or source SHA mismatch.")
    ipa_filename = local_path(artifact_dir, config["ipaBasename"])
    checksum = sha256(ipa_filename)
    require(manifest.get("ipaSHA256") == checksum, "IPA checksum does not match the manifest.")
    checksum_filename = local_path(artifact_dir, config["checksumBasename"])
    require(checksum_filename.stat().st_size <= config["downloadLimit"]["maximumJsonBytes"], "Checksum file exceeds its size limit.")
    require(checksum_filename.read_text(encoding="utf-8").strip() == checksum + "  " + config["ipaBasename"],
            "IPA checksum file does not match the downloaded IPA.")
    validate_ipa(ipa_filename, config, expected_identity["head_sha"])
    evidence_filename = local_path(artifact_dir, config["evidenceBasename"])
    evidence = read_json(evidence_filename, config)
    native_check.validate_evidence(evidence, expected_identity["head_sha"], config)
    require(str(evidence.get("runID")) == str(expected_identity["id"]), "Native evidence belongs to another GitHub run.")
    require(evidence["release"]["ipaSHA256"] == checksum, "Native evidence refers to different IPA bytes.")
    require(manifest.get("toolchain") == evidence["toolchain"], "Manifest and native toolchain evidence differ.")
    result_path = safe_relative_path(manifest["resultBundle"])
    result_root = PurePosixPath(config["resultRelativeDir"]).relative_to(config["buildRelativeDir"])
    require(result_root in result_path.parents and result_path.suffix == ".xcresult", "Native result bundle location is invalid.")
    require(evidence["resultBundle"] == (PurePosixPath(config["buildRelativeDir"]) / result_path).as_posix(),
            "Manifest and native result bundle paths differ.")
    result_dir = local_path(staging_dir, result_path.as_posix())
    require(result_dir.is_dir() and any(filename.is_file() for filename in result_dir.rglob("*")), "Original native result bundle is missing.")
    test_result = read_json(result_dir.parent / "test-results.json", config)
    require(native_check.read_test_counts(test_result, config["requiredTestSuites"]) == evidence["tests"],
            "Native test matrix and evidence counts differ.")
    commands = evidence.get("commands")
    require(isinstance(commands, list) and bool(commands), "Native command evidence is missing.")
    for command in commands:
        require(command.get("exitCode") == 0 and not command.get("timedOut"), "Native command did not complete successfully.")
        if "log" in command:
            log_path = safe_relative_path(command["log"]).relative_to(config["buildRelativeDir"])
            require(result_root in log_path.parents and local_path(staging_dir, log_path.as_posix()).is_file(),
                    "Original native command log is missing.")
    return {"manifest": manifest, "evidenceFilename": evidence_filename, "ipaFilename": ipa_filename}


def validate_artifact_metadata(artifact: dict, run: dict, config: dict) -> None:
    """Require GitHub's original ZIP digest and association with the selected run."""
    require(artifact.get("name") == config["artifactName"] and artifact.get("expired") is False,
            "Expected artifact is missing or expired. Rebuild the selected source and retry its new run ID.")
    require(type(artifact.get("id")) is int and artifact["id"] > 0, "GitHub artifact identity is invalid.")
    require(type(artifact.get("size_in_bytes")) is int and
            0 < artifact["size_in_bytes"] <= config["downloadLimit"]["maximumArchiveBytes"], "Artifact size is outside the configured limit.")
    digest = artifact.get("digest")
    require(isinstance(digest, str) and digest.startswith("sha256:") and SHA256_PATTERN.fullmatch(digest.removeprefix("sha256:")),
            "GitHub artifact SHA-256 digest is missing or invalid; rebuild the selected source.")
    workflow_run = artifact.get("workflow_run", {})
    require(all(workflow_run.get(key) == run[key] for key in ("id", "head_sha", "head_branch")),
            "GitHub artifact belongs to a different run, source or branch.")


def download_build(requested_run_id=None, requested_sha=None, *, project_dir=PROJECT_DIR, config=None, runner=bounded_process) -> Path:
    """Publish an immutable verified build while keeping every previous usable IPA on failure."""
    try:
        project_dir = Path(project_dir).resolve()
        config = config if config is not None else native_check.read_json(project_dir / "build_config.json")
        # Validate selection before it becomes an API URL segment or query parameter.
        if requested_run_id is not None:
            require(re.fullmatch(r"[1-9][0-9]*", str(requested_run_id)), "--run-id requires a positive run number.")
        if requested_sha is not None:
            require(native_check.SHA_PATTERN.fullmatch(requested_sha), "--sha requires a full lowercase 40-character commit SHA.")
        build_dir = local_path(project_dir, config["buildRelativeDir"])
        download_dir = local_path(project_dir, config["downloadRelativeDir"])
        build_dir.mkdir(parents=True, exist_ok=True)
        download_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="download-", dir=build_dir) as temporary_dir:
            staging_dir = Path(temporary_dir)
            client = GitHubArtifactClient(project_dir, staging_dir, config, runner)
            repository_endpoint = "repos/" + config["repository"] + "/actions"
            workflow_endpoint = repository_endpoint + "/workflows/" + config["workflow"]
            workflow = client.query(workflow_endpoint)
            require(type(workflow.get("id")) is int and workflow.get("path") == ".github/workflows/" + config["workflow"],
                    "GitHub returned an unexpected workflow.")
            selection_config = {**config, "workflowId": workflow["id"]}
            if requested_run_id is not None:
                run_records = [client.query(repository_endpoint + "/runs/" + str(requested_run_id))]
            else:
                query_by_name = {"branch": config["branch"], "status": "success"}
                if requested_sha is not None:
                    query_by_name["head_sha"] = requested_sha
                run_records = client.list_records(workflow_endpoint + "/runs", "workflow_runs", query_by_name)
            run = select_run(run_records, requested_run_id, requested_sha, selection_config)
            print(f"Selected run {run['id']}, source SHA {run['head_sha']}.")
            artifacts = client.list_records(repository_endpoint + "/runs/" + str(run["id"]) + "/artifacts", "artifacts")
            matches = [artifact for artifact in artifacts if artifact.get("name") == config["artifactName"]]
            require(len(matches) == 1, "Expected exactly one named artifact; it may be missing or expired. Rebuild this source and select the new run.")
            artifact = next(iter(matches))
            validate_artifact_metadata(artifact, run, config)
            archive_filename = staging_dir / "artifact.zip"
            client.fetch(repository_endpoint + "/artifacts/" + str(artifact["id"]) + "/zip", archive_filename, archive=True)
            require(archive_filename.stat().st_size == artifact["size_in_bytes"], "Downloaded artifact size differs from GitHub metadata.")
            digest = sha256(archive_filename)
            require("sha256:" + digest == artifact["digest"], "Downloaded artifact digest differs from GitHub metadata.")
            content_dir = staging_dir / "content"
            content_dir.mkdir()
            extract_archive(archive_filename, content_dir, config)
            validated = validate_artifact(content_dir, run, config)
            published_basename = (f"run-{run['id']}-{run['head_sha'][:BUILD_IDENTIFIER_PREFIX_LENGTH]}-"
                                  f"{digest[:BUILD_IDENTIFIER_PREFIX_LENGTH]}")
            published_dir = local_path(download_dir, published_basename)
            # Keep the raw ZIP for audit and verify existing bytes against it before reuse.
            archive_filename.rename(content_dir / "github-artifact.zip")
            if published_dir.exists():
                require(not published_dir.is_symlink(), "Existing build directory must not be a link.")
                for filename in content_dir.rglob("*"):
                    if filename.is_file():
                        existing_filename = local_path(published_dir, filename.relative_to(content_dir).as_posix())
                        require(existing_filename.is_file() and not existing_filename.is_symlink() and sha256(existing_filename) == sha256(filename),
                                "Existing downloaded build has changed. Preserve it and choose a fresh output directory before retrying.")
            else:
                content_dir.rename(published_dir)
            evidence_relative_path = validated["evidenceFilename"].relative_to(content_dir)
            evidence_filename = local_path(build_dir, config["evidenceBasename"])
            temporary_evidence_filename = staging_dir / "selected-native-evidence.json"
            shutil.copyfile(published_dir / evidence_relative_path, temporary_evidence_filename)
            temporary_evidence_filename.replace(evidence_filename)
            print("Verified IPA: " + str(published_dir / validated["ipaFilename"].relative_to(content_dir)))
            print("Native evidence: " + str(evidence_filename))
            return published_dir
    except DownloadError:
        raise
    except (OSError, ValueError, KeyError, TypeError, AttributeError, zipfile.BadZipFile, RuntimeError) as error:
        # Unknown subprocess or artifact text can include credentials; report the failed category only.
        raise DownloadError("Build download or validation failed (" + type(error).__name__ + "). Previous IPA files were preserved. Check free disk space, repository access and the selected run, then retry.") from error


def main() -> int:
    """Expose exact run/source selection and a useful failure status to the Windows launcher."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", help="Exact successful GitHub Actions run number")
    parser.add_argument("--sha", help="Exact full lowercase commit SHA; may also constrain --run-id")
    arguments = parser.parse_args()
    try:
        download_build(arguments.run_id, arguments.sha)
        return 0
    except DownloadError as error:
        print("Download failed: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
