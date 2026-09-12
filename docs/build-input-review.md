# Native build inputs

Reviewed on 2026-09-12. No package installation is needed to build the initial app.
It uses Apple frameworks and a checked-in Xcode project. Python tooling uses only
the standard library.

| Input | Selected revision | Evidence |
|---|---|---|
| Xcode | 26.6, build 17F113 | [GitHub runner inventory](https://raw.githubusercontent.com/actions/runner-images/main/images/macos/macos-26-arm64-Readme.md) lists this toolchain; [Apple compatibility](https://developer.apple.com/xcode/system-requirements) lists its SDK and deployment support. |
| iOS SDK | 26.5; deployment target 17.0 | Asserted during each native run; compiling for iOS 17 is separate from running on iOS 17. |
| actions/checkout | v7.0.1, `3d3c42e5aac5ba805825da76410c181273ba90b1` | [Official release](https://github.com/actions/checkout/releases/tag/v7.0.1), tag resolved through GitHub API; GitHub reports valid commit verification. |
| actions/upload-artifact | v7.0.1, `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | [Official release](https://github.com/actions/upload-artifact/releases/tag/v7.0.1), tag resolved through GitHub API; GitHub reports valid commit verification. |

Both actions are maintained under GitHub's `actions` organization. Their pinned
`action.yml` files run committed JavaScript bundles with Node 24. The workflow
does not run their development, install, or build scripts. Checkout uses a
read-only token and disables persisted credentials. Upload uses its ordinary
archive mode, retains files for the configured duration, and separates failed
runs from successful IPA artifacts. There are no signing secrets.

The pinned package metadata and complete lockfiles were inspected. Checkout has
587 lockfile entries, including 25 entries not marked development-only; upload
has 704, including 157 not marked development-only. All resolved entries use
the npm registry and carry integrity values. The immutable action revision
pins the bundled runtime dependencies; the workflow does not resolve the
version ranges in the upstream development manifests. Checkout's release notes
include branch/argument handling fixes. Upload's notes include an updated HTTP
runtime dependency. This is an origin, metadata and lockfile review, not a
line-by-line audit of every bundled dependency or a reproducible bundle build.

The hosted runner image is mutable. The inspected arm64 inventory reports image
`20260907.0351.1`; each real run records the actual image, macOS, Swift, SDK,
Xcode, simulator UUID/runtime and source SHA. A missing or changed pinned Xcode
fails the command. There is no automatic fallback to another Xcode installation.

Native results are read with Apple's `xcresulttool get test-results tests`,
documented in the [Xcode release notes](https://developer.apple.com/documentation/xcode-release-notes/xcode-16_3-release-notes).
The parser requires passed case nodes for every requested class and rejects
missing, skipped, failed or zero-test results. Windows unit tests exercise the
checker using mock data; those results do not establish simulator execution or
physical playback.

The successful artifact includes `artifact/` with the IPA, checksum, manifest
and native evidence, and `results/` with the actual result bundles and command
logs. `--check-evidence` accepts the downloaded JSON directly on Windows and
resolves `HEAD` through Git. A later source commit requires a new native run.

No native run or physical installation has passed at the time this initial
build setup was authored. Use `docs/device-validation.md` to record actual
device observations once a matching-source build exists.
