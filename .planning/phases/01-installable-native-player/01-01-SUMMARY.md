---
phase: 01-installable-native-player
plan: "01"
subsystem: native-player
tags: [swiftui, swift6, core-data, avaudioengine, xctest, github-actions]
requires: []
provides:
  - Native Files-to-WAV playback with persisted identity and bounded audio output
  - Bundled dark JSON/image skin and inspectable transfer observations
  - Pinned macOS simulator tests and unsigned arm64 IPA with source evidence
affects: [01-02, library-discovery, playback, skins, diagnostics]
tech-stack:
  added: [SwiftUI, Core Data, AVAudioEngine, XCTest, GitHub Actions]
  patterns: [Background persistence with immutable snapshots, Single audio start authority, Source-matched build evidence]
key-files:
  created:
    - MusicPlayer.xcodeproj/project.pbxproj
    - MusicPlayer/App/MusicPlayerApp.swift
    - MusicPlayer/Persistence/LibraryStore.swift
    - MusicPlayer/Audio/PlaybackCoordinator.swift
    - MusicPlayer/Feature/FilesView.swift
    - MusicPlayer/Theme/Skin.swift
    - MusicPlayerTests/NativeTracerTests.swift
    - MusicPlayerUITests/NativeTracerUITests.swift
    - scripts/native_check.py
    - build_config.json
    - .github/workflows/ci.yml
  modified: [.gitignore, AGENTS.md]
key-decisions:
  - The user's updated repository instructions authorize agent pushes and supersede older user-only-push wording.
  - A successful newer simulator run and iOS 17 deployment build do not establish iOS 17 runtime or physical-device support.
  - The first WAV slice contributes to broad phase requirements without completing them.
requirements-completed: []
requirements-contributed: [APP-01, APP-02, BUILD-01, LIB-01, PLAY-01, PLAY-06, SKIN-01]
coverage:
  - id: D1
    description: Persist a real Documents WAV, render nonzero audio, recover after read failure, and inhibit starts after injected route loss.
    verification:
      - kind: integration
        ref: MusicPlayerTests/NativeTracerTests.swift; run 34710813866; 9 passed
        status: pass
    human_judgment: false
  - id: D2
    description: Select a transferred WAV in the real Files UI and relaunch silently.
    verification:
      - kind: automated_ui
        ref: MusicPlayerUITests/NativeTracerUITests.swift#testTransferredWavePlaysAndRelaunchesSilently; run 34710813866
        status: pass
    human_judgment: false
  - id: D3
    description: Build an unsigned arm64 IPA from the tested source with the dark skin resources and iOS 17 minimum deployment.
    verification:
      - kind: other
        ref: build/ci-runs/34710813866-success/artifact/native-evidence.json; source 9115f759514b93a94f4f9856d986c0626ac4b3bd
        status: pass
    human_judgment: false
  - id: D4
    description: Install and hear playback on the actual iPhone, observe USB transfers, and verify real headphone-loss behavior.
    verification: []
    human_judgment: true
    rationale: Physical installation and USB observations belong to Plan 02; full physical playback acceptance belongs to later plans and remains pending.
actuals:
  tokens: 41413
  tasks: 2
  commits: 10
plan_head_before: 8c1058c4dd2e86f9007db4e1f0f0ef694ed063fb
tested_source_sha: 9115f759514b93a94f4f9856d986c0626ac4b3bd
native_run_id: "34710813866"
duration: 79min
completed: 2026-09-12
status: complete
---

# Phase 1 Plan 01: Native WAV Player and First macOS Build Summary

**A native Files screen now plays a persisted app-owned WAV through bounded audio buffers, and the same source passes simulator tests and produces an unsigned iPhone IPA.**

## Performance

- Recorded implementation window: first task commit at 2026-09-12T17:09:02Z through evidence review at approximately 18:28Z; 79 minutes. Earlier uncommitted authoring time is not reconstructed.
- Tasks: 2 of 2. Realized committed diff: 28 files, 165652 characters / 4 rounded up = 41413 estimate-scale tokens.
- Commit count: `git rev-list --count 8c1058c4dd2e86f9007db4e1f0f0ef694ed063fb..9115f759514b93a94f4f9856d986c0626ac4b3bd` returned 10, including intervening planning/authorization commits. This measurement precedes closeout metadata.

## Accomplishments

- Native SwiftUI app and real Files selection, background Core Data UUID/relative-locator persistence, closed PCM WAV validation, bounded AVAudioEngine playback, and explicit-Play recovery after route loss or audio read failure.
- Read-only copyable file observations retain pending/unsupported files for the upcoming USB investigation; a readable MP3 prefix is not treated as proof of completed transfer.
- Versioned dark skin JSON and a bundled image render through the shared loader. Initial errors retain original technical causes.
- Official pinned CI actions, native test/result inspection, current-source checks, unsigned Release packaging, checksum and manifest are implemented without third-party app packages.

## Native Evidence

- Successful run: [34710813866](https://github.com/ThongvanAlexis/Ios-music-player/actions/runs/34710813866), clean source `9115f759514b93a94f4f9856d986c0626ac4b3bd`.
- Native wrapper ran from 18:19:09.964Z to 18:25:32.488Z on macOS 26.6.2 / 25G83, arm64 runner image `20260907.0351.1`.
- Xcode 26.6 / 17F113, SDK 26.5, Apple Swift 6.3.3; project language mode Swift 6 and deployment target iOS 17.0.
- iPhone Air simulator, iOS 26.5 / 23F77: 9 `NativeTracerTests` and 1 `NativeTracerUITests`, 0 failures, 0 skipped.
- Tests cover empty-library silence, persisted identity after reopening, nonzero rendered PCM and advancing time, injected route-loss inhibition, sustained explicit-Play recovery after read failure, growing-WAV observations, MP3-prefix uncertainty, file containment, dark image loading, actual Files UI selection and silent relaunch.
- The recorded `xcodebuild test` command took 155.745 seconds; app-test execution itself took 4.610 seconds. No standalone warm selected-test latency claim is made.
- Release passed: `com.oliver.musicplayer`, arm64, minimum OS 17.0, both dark skin resources present.
- IPA: `MusicPlayer-unsigned.ipa`, 193925 bytes. Locally recomputed SHA-256 agrees with manifest and evidence: `d379a6dee0861a2bbf68119dc873d021dc315db6b6088214fc7f28d905a515bb`.
- Original downloads retained under `build/ci-runs/34710813866-success/{artifact,results}`; GitHub log retained at `build/ci-runs/34710813866-full.log`. Selected evidence copied to `build/native-evidence.json`.
- `python scripts/native_check.py --check-evidence build/native-evidence.json --expected-sha HEAD` passed before any closeout metadata commit, when HEAD was the tested source above. Later documentation commits are not claimed as natively tested source.
- Uploaded build/test logs contain neither `database integrity compromised` nor `vnode unlinked`. Xcode emitted its AppIntents metadata-extraction warning because this app has no AppIntents dependency; builds and tests succeeded.
- 23 Python build-tooling tests passed locally and in CI. They verify tooling behavior, not physical audio.

## Task Commits

1. Task 1, native slice and build tooling: `a6fbc53`, `cee7c66`, `49924d4`.
2. Task 2, actual CI verification and necessary native corrections: `2b46fa9`, `ba715a9`, `3d19f20`, `12922ce`, `9115f75`.

Intervening history: `5031791` saved the build handoff; `57db8ab` recorded repository push authorization. The final metadata commit is separate from the source verified by CI.

## Deviations from Plan

- **Repository authorization:** the user updated AGENTS.md and explicitly allowed agent pushes. The orchestrator pushed and inspected builds; the older user-only action was no longer necessary.
- **[Rule 1 - Bug] Native Swift 6 isolation:** actual compilation exposed the shared Core Data merge-policy singleton and audio start-lock closure isolation. Store-local merge policy and explicit actor-isolated closure fixed compilation (`2b46fa9`, `ba715a9`).
- **[Rule 1 - Bug] Playback retry and selection:** rebuild failed playback resources on explicit Play and clear the previous selected filename immediately; regression coverage verifies sustained recovery (`3d19f20`, `12922ce`).
- **[Rule 1 - Bug] SQLite teardown:** close persistent stores before removing test directories and await shutdown during teardown. The matching run confirms the earlier SQLite integrity/unlinked-file diagnostics disappeared (`9115f75`).
- **TDD process deviation:** native behavior tests were not executed as an intentional RED before implementation. Windows toolchain rejection and initial Swift compiler failures are not behavior RED evidence. Final native GREEN is real; a RED/GREEN history is not claimed. Recorded in the cross-phase defect register for review.

## Requirement Scope and Remaining Verification

APP-01, APP-02, BUILD-01, LIB-01, PLAY-01, PLAY-06 and SKIN-01 receive partial evidence from this slice; none is fully complete solely because one WAV and the initial UI/build route work. Installation, broader navigation, required formats, full playback controls, durable diagnostics, complete skins and physical behavior remain assigned to later plans.

All physical-device checks remain pending, including first sideload, USB publication observations, audible speaker/headphone behavior, Bluetooth/wired-loss safety and locked playback. iOS 17 runtime testing is also pending; an iOS 17 deployment build on SDK 26.5 does not establish runtime support.

## Known Stubs

No stub prevents this WAV slice from working. `MusicPlayer/App/AppCopy.swift:19` through line 23 contains unused planned empty-state strings for later tags, playlists, favorites and EQ screens. These are not wired into the current Files route; later product phases own those capabilities.

## Next Plan Readiness

Plan 02 can implement safe Windows artifact retrieval and prepare the actual iPhone installation/USB observations using the verified artifact above. Phase 1 remains in progress with 1 of 20 plans complete.

## Self-Check: PASSED

All listed source/evidence files and all ten recorded commits exist. The downloaded IPA digest agrees with the manifest and native evidence, and the selected report passed the source check. STATE and ROADMAP report Plan 02 next with 1 of 20 plans complete; later native/device checks and broad requirements remain pending. The runtime advanced the plan counter but declined progress recalculation because phase scope was unscoped, so the visible progress was set directly from the one completed summary and twenty plan files.
