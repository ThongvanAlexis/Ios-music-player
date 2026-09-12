# Phase 1: Installable Native Player - Pattern Map

**Mapped:** 2026-09-12
**Files classified:** 30 proposed file/responsibility entries
**Analogs found:** 2 / 30 entries (one source workflow and one delivery-record template)

The repository is greenfield: tracked files contain planning documents, instructions and `.gitignore`, with no Swift source, Xcode project or tests. Names below are proposed planner assignments, not existing APIs. Directory entries represent files the planner must split by responsibility. No local `.codex/skills/` or `.agents/skills/` directory exists.

## File Classification

All paths are relative to this repository unless prefixed with the sibling checkout. “New” means no tracked source analog exists.

| New/Modified File or Responsibility | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `MusicPlayer.xcodeproj/project.pbxproj` | config | batch | None | New |
| `MusicPlayer.xcodeproj/xcshareddata/xcschemes/MusicPlayer.xcscheme` | config | batch | None | New |
| `MusicPlayer/Info.plist` | config | transform | None | New |
| `MusicPlayer/App/MusicPlayerApp.swift` | provider | event-driven | None | New |
| `MusicPlayer/App/AppConfiguration.swift` | config | transform | None | New |
| `MusicPlayer/Feature/AppShell.swift` | component | event-driven | None | New |
| `MusicPlayer/Feature/FilesView.swift` | component | event-driven | None | New |
| `MusicPlayer/Feature/NowPlayingView.swift` | component | event-driven | None | New |
| `MusicPlayer/Feature/CompactPlayer.swift` | component | event-driven | None | New |
| `MusicPlayer/Feature/SettingsView.swift` | component | event-driven | None | New |
| `MusicPlayer/Feature/DiagnosticView.swift` | component | event-driven | None | New |
| `MusicPlayer/Domain/` track IDs, queue, command, snapshot and resume policy | model | transform | None | New |
| `MusicPlayer/Audio/PlaybackCoordinator.swift` | service | event-driven | None | New |
| `MusicPlayer/Audio/PCMDecoder.swift` and concrete Apple reader | service | streaming | None | New |
| `MusicPlayer/Audio/PCMProducer.swift` and graph ownership | service | streaming | None | New |
| `MusicPlayer/Audio/AudioSessionController.swift` | service | event-driven | None | New |
| `MusicPlayer/Audio/SystemMediaController.swift` | service | event-driven | None | New |
| `MusicPlayer/Persistence/` Core Data model, store and resume persistence | store | CRUD | None | New |
| `MusicPlayer/Library/` locator resolution, readiness and reconciliation | service | file-I/O | None | New |
| `MusicPlayer/Theme/` Codable skin definition, loader and semantic roles | model/service | file-I/O, transform | None | New |
| `MusicPlayer/Resources/Skins/Dark/` JSON and at least one image asset | config | file-I/O | None | New |
| `MusicPlayer/Diagnostic/` structured record, bounded history and optional writer | model/store | file-I/O | None | New |
| `MusicPlayerTests/`, `MusicPlayerUITests/`, `Tests/Fixtures/` | test | batch, event-driven | None | New |
| `.github/workflows/ci.yml` | config | batch, file-I/O | `../GOSL-MirkFall/.github/workflows/ci.yml` | Role + delivery-flow match |
| `download_builds.py` | utility | request-response, file-I/O | None | New |
| `download_builds.bat` | utility | batch | None | New |
| `build_config.json`, `tests/test_download_builds.py` | config/test | transform, batch | None | New |
| `docs/device-validation.md` | test record | batch | `../GOSL-MirkFall/docs/phase-07-smoke.md` | Role match |
| Conditional `NativeCodec/` bridge, module map, licenses and pinned build inputs | service/config | streaming, batch | None | New, only after measured Apple gap |
| `.gitignore` | config | file-I/O | Existing target only | New entries; no analog needed |

## Pattern Assignments

### `.github/workflows/ci.yml` (config, batch/file-I/O)

**Tracked analog:** `../GOSL-MirkFall/.github/workflows/ci.yml`, verified with `git -C ../GOSL-MirkFall ls-files -- .github/workflows/ci.yml`.

**Core packaging and failure handling, lines 429–438:**

```bash
set -euo pipefail
BUILD_DIR="build/ios/iphoneos"
if [ ! -d "$BUILD_DIR/Runner.app" ]; then
  echo "::error::Expected Runner.app under $BUILD_DIR after flutter build ios"
  exit 1
fi
WORK_DIR="$(mktemp -d)"
mkdir "$WORK_DIR/Payload"
cp -R "$BUILD_DIR/Runner.app" "$WORK_DIR/Payload/"
(cd "$WORK_DIR" && zip -qr "$GITHUB_WORKSPACE/mirkfall-unsigned.ipa" Payload)
```

Copy the app-presence check, temporary packaging directory and immediate `Payload/<app>.app` structure. Replace Flutter paths, app/artifact names and diagnostic text with the native target's actual products; add cleanup and inspect the app before packaging. Use native Release `xcodebuild`, signing disabled, iOS 17 deployment, and the research-selected Xcode version assertion. Do not copy Flutter, CocoaPods, the unpinned default Xcode choice or sibling job dependencies.

**Upload validation, lines 443–447:**

```yaml
with:
  name: mirkfall-ios-unsigned-ipa
  path: mirkfall-unsigned.ipa
  if-no-files-found: error
  retention-days: 14
```

Keep missing-output failure; choose this project's artifact name and retention. Upload checksum, manifest and test results as well. The sibling action uses a moving version tag: replace it and checkout with reviewed official full commit pins. Record run ID, source SHA, toolchain, runner image and dependency digests. Use least required workflow permissions; no push command or automatic publish step. Authentication is runner-managed; app account guards do not apply.

### `download_builds.py`, `download_builds.bat`, shared delivery config and Python tests

**No tracked analog.** The context-selected sibling downloader and launcher were read, but neither is returned by `git ls-files` in that checkout; therefore they are not assigned as source patterns. Their observed behavior informs adaptation, not code to copy.

Create a standard-library Python implementation using `subprocess.run` with an argument list and configured timeout, and let installed `gh` own authentication. Do not adopt the sibling HTTP/progress packages or retrieve a token. Use one shared delivery configuration for workflow/artifact/manifest names and call limits; load it from CI and Python rather than duplicating agreement-sensitive values.

Select successful completed runs by repository, workflow and branch; accept explicit run ID and expected SHA, display the chosen SHA and reject mismatches without older-build substitution. Download the expected artifact into a new temporary directory with explicit `gh run download` arguments. Validate manifest identity, IPA checksum and archive structure before publication. Preserve the previous IPA on timeout, missing/expired artifact, invalid archive, mismatch or replacement failure. Reject archive path escapes and unexpected app products. Return nonzero on failure and retain useful English diagnostics without credentials.

The batch launcher resolves its own directory, invokes the Python entry point, forwards user arguments and preserves its exit code even if it pauses. Infer neither success from an empty artifact list nor completion from the newest unfiltered run. Unit tests inject subprocess results and temporary storage to exercise wrong SHA, timeout, damaged download and preservation of a prior IPA.

### `docs/device-validation.md` (test record, batch)

**Tracked analog:** `../GOSL-MirkFall/docs/phase-07-smoke.md`, verified in the sibling checkout.

**Evidence fields, lines 99–104:**

```markdown
- **Device:** Iphone 17 pro
- **iOS version:** 26.3.1 (a)
- **MirkFall build:** fbcbde6a2569baad84b3104eceed51b437e38ed4
- **Sideload method:** Iloader (side store)
- **IPA source:** https://github.com/ThongvanAlexis/GOSL-MirkFall/actions/runs/24834805699/artifacts/6601494748
- **Date of walk (UTC):** 20260423 15h00
```

Copy field structure only, replacing values with this app's actual evidence. Add artifact checksum, installed source SHA, transfer/disconnect results, codec matrix, locked next-track opening and wired/Bluetooth loss interleavings. Mark unperformed checks pending. The sibling's successful launch does not validate this app; its allowance for skipped checks must not weaken required physical audio validation.

## Shared Patterns

These are required new patterns from context/research, not existing Swift excerpts.

- **Composition and imports:** Native SwiftUI directly; use Foundation, CoreData, AVFAudio/AVFoundation and MediaPlayer where owned. Inject external services at initialization. Avoid UI abstraction and forwarding-only wrappers. AppShell supplies all eight fixed destinations; later features need honest placeholder content, not implemented business workflows.
- **One playback authority:** App buttons, compact player and system commands dispatch the same intents. Serialize decisions; use immutable snapshots and generations across workers. Only explicit app/system Play clears headphone-loss inhibition. Reconnection, seek, selection, Next, restore and delayed completions cannot bypass it.
- **Bounded audio:** Decode into reusable buffers off UI/render threads; enforce backpressure and source-time accounting. Reject stale callbacks after stop/seek and distinguish buffer reuse from heard completion. Conditional MP4 reader or Xiph adapters implement the decoder boundary only when tests establish a gap.
- **Storage:** Stable UUID identity plus relative app-owned locator; resolve the current Documents root on access. Validate containment and changing revisions. Readiness quiescence alone cannot prove an interrupted copy completed. Store metadata/resume/diagnostics outside shared music, keep DB work in a background context, and restore paused. Apply protection that supports opening subsequent tracks while locked after first unlock.
- **Errors:** Preserve operation, affected file, original domain/code/message, bounded cause chain and recovery result. A bounded persistent history remains inspectable and copyable with verbose logging off; optional writing runs serially off main/audio threads.
- **Appearance:** One versioned JSON/image schema and loader feeds bundled dark controls now and imported/bundled variants later. SwiftUI owns geometry, accessibility and commands. Consult the phase UI specification for concrete layout; use semantic assets from the first screen.
- **Documentation/naming:** Add `///` to every non-private Swift declaration requiring documentation, including internal types and initializers. Explain behavior without planning identifiers. Centralize constants; descriptive singular names, plural arrays, set suffixes and explicit path kinds follow AGENTS.md.
- **Delivery:** Build/runtime facts stay separate. No push. Windows unit checks cannot validate Xcode or phone behavior. Installed build evidence must identify the exact source SHA.

The tracked sibling `docs/flutter-discoveries.md` was also inspected, notably lines 22–32 on resolving relative sandbox paths and IPA packaging. It is contextual documentation, not a Swift analog. Its Flutter JIT/debug claims, plugin SDK constraints and synchronous Dart logging advice must not be transferred to native Swift; this project requires background file writes and normal diagnostics in the delivered app.

## No Analog Found

The 28 entries marked New above have no eligible source analog. Use the architecture, API examples, test matrix and dependency review in `01-RESEARCH.md`, and the locked decisions in `01-CONTEXT.md`, to establish them. Research snippets are proposed designs, not compiled code. Do not manufacture existing imports, auth middleware, test helpers or native decoder implementations.

Project resources must include app icons, declared skin images and model membership. Info.plist must expose USB file sharing and audio background mode. Ignore generated build/download outputs while retaining the existing `/ref_pics/` rule. Native codec files remain conditional; do not add dependencies or build tooling simply to fill a proposed directory. Folder trees, full skin importing, waveform, EQ processing and saved collections remain deferred.

## Metadata

**Search scope:** Current repository tracked inventory and both possible project skill directories; six context-named sibling delivery references.
**Files inspected:** AGENTS.md, context, research; sibling workflow, downloader, launcher, delivery commands, smoke record and discovery notes. Relevant workflow/document ranges were extracted; scripts were inspected as text only.
**Tracked checks:** Sibling workflow, smoke record and discovery notes returned tracked paths. Downloader, launcher and delivery commands did not; none is assigned as a reusable tracked analog.
**Extraction date:** 2026-09-12.
**Validation:** Source inspection only; no app build, installation, downloader execution, source edits, commit or push performed.
