# Walking Skeleton — iOS Music Player

**Phase:** 1
**Generated:** 2026-09-12
**Status:** Planned; no native or physical behavior has passed yet.

## Capability to prove end-to-end

The user taps a real app-owned WAV in native Files, its persisted track identity is read back, the shared player renders bounded audio, and the same source builds into the unsigned IPA. Plan 01 supplies this first path. Native UI calling the playback/storage services is the local-app counterpart of a web request; no server or authentication workflow is invented.

## Architectural decisions

| Decision | Choice | Rationale |
|---|---|---|
| Framework | Native SwiftUI; Swift 6 language mode | Locked native UI with concrete controls and no interchangeable UI layer |
| Toolchain | Xcode 26.6 / 17F113, Swift compiler 6.3, SDK 26.5, deployment iOS 17.0 | Exact research baseline; script asserts installed tools and records runner image |
| Storage | Core Data in Application Support; app-owned audio in Documents | Stable UUID/relative locators and real transactions without duplicate songs |
| Model ownership | Programmatic versioned model in LibraryStore.swift; immutable snapshots across isolation | One initial schema owner with background context and explicit migration/version record |
| Playback | One coordinator/start authority, PCMDecoder boundary, bounded producer | All controls/formats share loss inhibition and source timing |
| UI state | Concrete SwiftUI views project immutable playback/library state | No per-view playback clock or duplicate transport state |
| Appearance | One versioned JSON/image Skin model and loader | First real dark screen exercises shared asset roles |
| Auth | No app account; OS/sideloader and gh own their existing credentials | No new account/server feature in scope |
| Deployment | GitHub macos-26 → unsigned IPA → Windows GH_builds → existing iLoader/SideStore | Selected personal-device route; only user pushes |
| Directory layout | MusicPlayer/{App,Audio,Domain,Feature,Library,Persistence,Theme,Diagnostic,Resources}; native and UI tests alongside | Separate responsibilities where replacement/testing helps; native UI remains top layer |

Shared playback/skin interfaces and versioned app-owned persistence are marked costly in the tasks. No public interchange or irreversible production data migration is introduced. Existing product choices are not reapproved.

## Shared execution and verification rules

Use repository root as cwd. Every path in a task is exact; initial source/project/tests are NEW except the already tracked .gitignore. Later plans modify files created by previous plans. Files synchronize into Xcode targets through explicit synchronized groups with target-specific exclusions: app source/resources cannot accidentally include tests, fixture tools or conditional unused sources. The project must include real resource/model/icon membership.

Every non-private Swift type, function, method and initializer has /// documentation explaining purpose; modified undocumented declarations acquire it. Document unclear private functions and explain workarounds immediately above them. Implementation comments/docstrings never cite planning files or IDs. Descriptive singular names, plural arrays, set suffixes, explicit path kinds, centralized shared values and injected external services follow AGENTS.md. Swift6 framework objects remain isolated; do not silence isolation failures with broad unchecked Sendable.

AppCopy is created in 01-01-T1 and owns the exact approved Copywriting Contract strings/templates, including all later Phase 1 screens. AppConfiguration owns named app limits. build_config.json owns build/toolchain/repository/artifact identity and external command timeouts. Skin.swift owns semantic role/state names. Tests may assert expected behavior; they do not maintain duplicate production mappings.

scripts/native_check.py is created in 01-01-T1. From repo root on macOS, it sets DEVELOPER_DIR from build_config.json to /Applications/Xcode_26.6.app/Contents/Developer, verifies Xcode 26.6 / 17F113, resolves a real installed simulator ID to TEST_DESTINATION, builds the current source and runs selected XCTest/UI classes. It accepts repeated --suite CLASS, --ui-suite CLASS, --full, --release and --check-evidence FILE --expected-sha SHA. It uses argument arrays and configured timeouts, unique xcresult paths, actual result parsing and nonzero executed-test counts. test-without-building is allowed only with a current-SHA matching build-for-testing; otherwise rebuild. Missing tool/runtime/class/fixture, zero tests, failed tests, stale report or source mismatch is failure. Capture exact command, source SHA, toolchain, destination, count, elapsed time and evidence path. The under-60-second affected warm-test target must be measured; full builds and long-file tests are explicitly longer verification jobs.

Release invocation is xcodebuild -project MusicPlayer.xcodeproj -scheme MusicPlayer -configuration Release -sdk iphoneos -destination generic/platform=iOS -derivedDataPath build/DerivedData CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO IPHONEOS_DEPLOYMENT_TARGET=17.0 build. Script options and actual project/scheme names must match. Build evidence includes arm64/minimum-OS/resource/link inspection and immediate Payload/MusicPlayer.app packaging. The workflow uploads build/native-evidence.json, manifest, checksum, IPA and native results. The downloader stages/checks them before publication and copies selected native evidence to build/native-evidence.json. The Windows evidence checker resolves HEAD via git rev-parse and checks identity/counts without invoking Xcode; it cannot validate physical observations. Python unittest failure signals include nonzero exit, FAILED or Ran 0 tests.

No push command is issued by the agent. On this Windows host prepare the full concrete diff/automation first, then invoke C:/checkouts3/common-scripts/ntfy.py when the user's push, phone interaction or unresolved workflow choice is actually needed. Native verification in 01-01-T1 is deliberately discharged by the actual user-triggered run in T2; neither task is recorded runtime-complete before that evidence. On later source changes, the same necessary user-only push rule applies. Do not present local checks as Xcode/iPhone proof. There is no paid account/TestFlight/service enrollment in this plan.

Early USB observations must be available before 01-02-T2: LibraryStore's TransferObservation and the initial Files File Details sheet expose/copy current identity, size, mtime, timestamps and parser revisions for every observed regular file, including pending/unsupported MP3. This is instrumentation, never proof that an intended source is complete. A valid MP3 prefix cannot reveal missing intended trailing bytes without external evidence. If a stronger completion proof needs an added mandatory source manifest, ask only at that real execution checkpoint with evidence; the decision must be resolved before dependent readiness work or LIB-01 completion. An optional manifest is not silently made mandatory.

Security uses native-relevant ASVS level 1 checks with high/critical issues blocking completion; no web account/session controls are invented. Canonical package/build review precedes execution. Native codec source provenance and fixture tool provenance remain separate from adoption. File containment and generic dependency integrity are owned by the plans' threat models/security review, not duplicated as bespoke prohibitions.

## Stack touched in Phase 1

- [ ] Native project, resources, app/unit/UI targets and build runner
- [ ] Real Files route and shared player interaction
- [ ] Real Core Data persisted write AND read
- [ ] Real app-owned file and bounded PCM/rendered output
- [ ] Actual macOS build/unsigned IPA and installed phone execution

## Sequential slice plan

| Wave | Plan | Tasks | User-visible result |
|---|---|---|---|
| 1 | 01-01 | 2 | Native file-to-speaker tracer and first macOS build |
| 2 | 01-02 | 2 | Windows IPA retrieval and real USB publication probe |
| 3 | 01-03 | 1 | Reconcile transferred media without disturbing playback |
| 4 | 01-04 | 1 | Ready Files rows and complete read-only file details |
| 5 | 01-05 | 1 | Persist inspectable discovery failures across relaunch |
| 6 | 01-06 | 1 | Shared image-backed dark skin roles |
| 7 | 01-07 | 1 | Eight fixed destinations and silent page restoration |
| 8 | 01-08 | 1 | Installed app icon and measured small-screen appearance |
| 9 | 01-09 | 2 | Bounded audio production and one start authority |
| 10 | 01-10 | 2 | Measure Apple decoding against the complete format matrix |
| 11 | 01-11 | 1 | Reviewed source builds for measured decoder gaps |
| 12 | 01-12 | 2 | Measured Ogg and MP4 gaps through the shared PCM path |
| 13 | 01-13 | 2 | Displayed-order playback queue and silent restoration |
| 14 | 01-14 | 1 | Confirmed source-time seeking for long recordings |
| 15 | 01-15 | 2 | Full and compact shared player controls |
| 16 | 01-16 | 1 | Shared system transport and interruption handling |
| 17 | 01-17 | 1 | Locked-file access and background state checks |
| 18 | 01-18 | 1 | Inspect and copy retained errors from every page |
| 19 | 01-19 | 1 | Complete diagnostic causes and optional file logging |
| 20 | 01-20 | 2 | Final native, accessibility and physical-device acceptance |

All plans depend on the preceding plan because of shared composition/coordinator/store files and the project's sequential execution setting. No same-wave ownership overlap exists. Total: 20 plans, 28 tasks, 20 waves. Oversized expansions were partitioned by consecutive original tasks; single-task plans are intentional context-size splits. All expansion plans touch at most nine files; the first native scaffold retains its documented exception. Estimate calibration returned factor 1, sample_count 0, confidence low; estimates are uncalibrated projections, not measured durations.

## Multi-source coverage audit

COVERED means assigned executable work, never a runtime pass.

| Source | ID | Feature or constraint | Plan(s) | Status |
|---|---|---|---|---|
| GOAL | Goal | Approved transfer/install/local playback/system controls story | 01–20 | COVERED |
| GOAL | Success 1 | Native install, English, navigation and skin | 01,02,06,07,08,20 | COVERED |
| GOAL | Success 2 | USB persistence and all formats | 02,03,10,11,12,20 | COVERED |
| GOAL | Success 3 | Shared transport and long seek | 09,13,14,15 | COVERED |
| GOAL | Success 4 | Locked/system/headphone and unopened next file | 16,17,20 | COVERED |
| GOAL | Success 5 | Silent restoration and visible errors | 13,18,19,20 | COVERED |
| REQ | APP-01 | Requirement text in REQUIREMENTS.md | 01,02,10,20 | COVERED |
| REQ | APP-02 | Requirement text in REQUIREMENTS.md | 01,04,05,06,07,08,15,18,19,20 | COVERED |
| REQ | APP-03 | Requirement text in REQUIREMENTS.md | 07,08,13,15,20 | COVERED |
| REQ | BUILD-01 | Requirement text in REQUIREMENTS.md | 01,02,20 | COVERED |
| REQ | PLAY-01 | Requirement text in REQUIREMENTS.md | 01,03,04,09,10,11,12,19,20 | COVERED |
| REQ | PLAY-02 | Requirement text in REQUIREMENTS.md | 09,13,14,15,20 | COVERED |
| REQ | PLAY-03 | Requirement text in REQUIREMENTS.md | 09,10,11,12,14,15,20 | COVERED |
| REQ | PLAY-04 | Requirement text in REQUIREMENTS.md | 16,17,20 | COVERED |
| REQ | PLAY-05 | Requirement text in REQUIREMENTS.md | 16,17,20 | COVERED |
| REQ | PLAY-06 | Requirement text in REQUIREMENTS.md | 01,09,16,17,20 | COVERED |
| REQ | PLAY-07 | Requirement text in REQUIREMENTS.md | 03,13,20 | COVERED |
| REQ | LIB-01 | Requirement text in REQUIREMENTS.md | 01,02,03,04,05,19,20 | COVERED |
| REQ | SKIN-01 | Requirement text in REQUIREMENTS.md | 01,06,07,08,15,20 | COVERED |
| CONTEXT | D-10 | Filename primary and optional metadata | 04,15 | COVERED |
| CONTEXT | D-11 | Shared JSON/image skin roles now; trio/switching remain Phase 7 | 01,06 | COVERED |
| CONTEXT | D-12 | Apple Devices app-owned individual files | 01,02,03,20 | COVERED |
| CONTEXT | D-13 | USB workflow without audio picker | 01,03,04 | COVERED |
| CONTEXT | D-14 | Foreground discovery, evidence of readiness, no playback disruption | 02,03 | COVERED |
| CONTEXT | D-15 | Real relative locator foundation; folder verification remains Phase 2 | 02,03 | COVERED |
| CONTEXT | D-16 | File tap starts zero and stays in Files | 04,13 | COVERED |
| CONTEXT | D-17 | Displayed-order queue, adjacent navigation, final stop | 04,13 | COVERED |
| CONTEXT | D-18 | Previous goes immediately prior at zero | 13 | COVERED |
| CONTEXT | D-19 | Track and confirmed position restored paused | 13 | COVERED |
| CONTEXT | D-20 | Automatic bounded forward skip and retained warning | 13,19 | COVERED |
| CONTEXT | D-21 | Wired/Bluetooth loss pauses until explicit Play | 01,09,16,20 | COVERED |
| CONTEXT | D-22 | Loss inhibition defeats all automatic starts/reconnects | 09,13,14,15,16,20 | COVERED |
| CONTEXT | D-23 | Mandatory physical output/locked-next/interleaved checks | 16,17,20 | COVERED |
| CONTEXT | D-24 | Conditional other-interruption resume | 09,16,20 | COVERED |
| CONTEXT | D-25 | Original structured causes and recovery | 05,18,19 | COVERED |
| CONTEXT | D-26 | Inspectable/copyable normal diagnostics with logging off | 05,18,19 | COVERED |
| CONTEXT | D-27 | Useful errors now and I/O off main/render; export remains Phase 8 | 05,19 | COVERED |
| CONTEXT | D-28 | Preserve /ref_pics/ ignore and untracked images | 02 | COVERED |
| CONTEXT | D-01 | Native Xcode/macOS unsigned IPA and existing sideload route | 01,02,20 | COVERED |
| CONTEXT | D-02 | Windows downloader publishes to GH_builds | 02 | COVERED |
| CONTEXT | D-03 | User-only pushes, actual CI/installation evidence | 01,02,20 | COVERED |
| CONTEXT | D-04 | Eight fixed destinations/icon meanings | 07 | COVERED |
| CONTEXT | D-05 | Icon-only row, heading and accessible selected state | 07,08 | COVERED |
| CONTEXT | D-06 | Files initially, restore page silently | 07,13 | COVERED |
| CONTEXT | D-07 | Shared compact player above bar on other pages | 15 | COVERED |
| CONTEXT | D-08 | Dark first/default appearance | 01,06 | COVERED |
| CONTEXT | D-09 | Small cover beside metadata, timeline prominence | 15 | COVERED |
| RESEARCH | R1 | Pinned Xcode26.6/17F113, Swift6, iOS17 baseline | 01,10,20 | COVERED |
| RESEARCH | R2 | Checked-in native app/schemes/resources/icon | 01,08 | COVERED |
| RESEARCH | R3 | Official action SHA resolution and build identity | 01,02,20 | COVERED |
| RESEARCH | R4 | Standard-library gh downloader with timeout/staging | 02 | COVERED |
| RESEARCH | R5 | Early physical USB publication/replacement probe | 02 | COVERED |
| RESEARCH | R6 | Incremental readiness, persisted observations and no silent mandatory manifest | 03 | COVERED |
| RESEARCH | R7 | Relative stable identity, background Core Data and no duplicate audio | 01,03,13 | COVERED |
| RESEARCH | R8 | One start authority, generations and media reset | 09,16 | COVERED |
| RESEARCH | R9 | Bounded PCM/conversion/backpressure and heard completion | 09 | COVERED |
| RESEARCH | R10 | Source-time absolute seek including VBR/Opus/MP4 | 10,12,14 | COVERED |
| RESEARCH | R11 | Full Apple-first codec/container matrix and minimum OS | 10 | COVERED |
| RESEARCH | R12 | Legal hashed fixture generation/tool source review | 10 | COVERED |
| RESEARCH | R13 | Conditional canonical Xiph pins and recursive build/fix/license review | 11 | COVERED |
| RESEARCH | R14 | Static platform slices, HTTP/TLS/optional target exclusion | 11 | COVERED |
| RESEARCH | R15 | Audio-only MP4 track selection/timestamps/edit-list reader | 12 | COVERED |
| RESEARCH | R16 | Frozen queue, direct failure and bounded skip | 13 | COVERED |
| RESEARCH | R17 | Lock protection for new media and database sidecars | 03,17,20 | COVERED |
| RESEARCH | R18 | System MediaPlayer command equivalence | 16 | COVERED |
| RESEARCH | R19 | Structured bounded diagnostics, optional writer independence | 05,19 | COVERED |
| RESEARCH | R20 | One versioned skin/image role model with readable error fallback | 01,06 | COVERED |
| RESEARCH | R21 | Long-input memory/seek targets and physical output evidence | 10,20 | COVERED |

Research discovery is already current in 01-RESEARCH.md and 01-PATTERNS.md; this planning pass adds no package installation or duplicate research. Native source/toolchain claims remain pending runtime checks. No prior summaries/working native verification commands exist. Knowledge graph and project skill directories are absent.

Final-scope API coverage probe returned detected:false with no signals after reading the complete plan set plus Phase 1 roadmap section. Assumption-delta returned detected:false. No COVERAGE.md or identity-choice checkpoint is required. No configured ORM schema-push path or AI integration applies to this native app phase.

## UI consideration accounting

The approved UI probe has 44 rows. Every row is lifted verbatim into the owning plan's must_haves.truths, including its category/surface. These are explicit acceptance criteria, not passed evidence.

| Surface | Rows | Owning plan |
|---|---|---|
| navigation | 4 | 07 |
| files | 8 | 04 |
| now-playing | 6 | 15 |
| compact-player | 6 | 15 |
| seek | 4 | 15 |
| diagnostics | 8 | 18 |
| file-details | 4 | 04 |
| placeholder-settings | 4 | 07 |

44 surfaced = 44 authored; zero dismissed or silently omitted. Exact copy remains in the approved UI spec until AppCopy is implemented.

## Spec-less edge accounting

The compiled report supplied by the orchestrator contains 18 items. There is no phase SPEC. Meaningful classified items have explicit truths; unclassified items remain flagged assumptions tied to actual checks.

| Requirement | Category | Disposition | Plan(s) | Explicit criterion or flagged execution assumption |
|---|---|---|---|---|
| APP-01 | adjacency | resolved / explicit | 08 | Eight measured nonoverlapping navigation targets at 375 pt. |
| APP-01 | empty | resolved / explicit | 01 | Fresh Documents storage opens Files silently. |
| APP-01 | ordering | resolved / explicit | 04 | Explicit filename ordering plus stable UUID tie-break. |
| APP-02 | empty | resolved / explicit | 04,18 | Approved empty copy and Not provided for absent fields. |
| APP-02 | encoding | resolved / explicit | 04 | Preserve Unicode original text; English generated copy. |
| APP-03 | empty | resolved / explicit | 07 | Each named destination has actual heading, empty/unavailable content and route. |
| APP-03 | encoding | resolved / explicit | 07 | Full accessible destination names survive icon-only display. |
| APP-03 | concurrency | resolved / explicit | 07 | All destinations remain usable while background work completes, without granting playback. |
| BUILD-01 | unclassified | unresolved / flagged assumption | 02,20 | Actual successful run/download/sideload source identity is required. |
| PLAY-01 | unclassified | unresolved / flagged assumption | 10,12,20 | All codec cells require actual decoding and physical evidence. |
| PLAY-02 | concurrency | resolved / explicit | 09 | Only current generation changes state and starts permitted audio. |
| PLAY-03 | unclassified | unresolved / flagged assumption | 10,14,20 | Known long-file landmarks and measured seek/memory results. |
| PLAY-04 | unclassified | unresolved / flagged assumption | 17,20 | Previously unopened next file must work while physically locked. |
| PLAY-05 | unclassified | unresolved / flagged assumption | 16,20 | Real system controls must use the shared policy. |
| PLAY-06 | unclassified | unresolved / flagged assumption | 16,20 | Real output remains silent after loss until explicit Play. |
| PLAY-07 | unclassified | unresolved / flagged assumption | 13,20 | Disk-backed relaunch must restore paused with no engine start. |
| LIB-01 | concurrency | resolved / explicit | 03 | Serialize changing revisions and preserve active playback/queue. |
| SKIN-01 | unclassified | unresolved / flagged assumption | 06,08,20 | Actual skin assets and measured native UI/accessibility are required. |

18 surfaced = 10 resolved with explicit planned predicates + 8 unresolved flagged assumptions. Zero backstop resolutions and zero dismissals. Resolution here means an acceptance statement exists; execution has not passed. Every unclassified row remains visibly unresolved even where useful tests are planned; the verifier must inspect real evidence instead of treating absence of classification as success.

## Bespoke prohibition accounting

The recall pass retained four product-specific prohibitions; routine code hygiene was dropped and file/source-security concerns were referred to the concrete threat models. The installed probe-core.cjs projectProhibitions serializer projected the retained items. Their descriptor-less statement/status objects are emitted in must_haves.prohibitions:

| Prohibition | Plan | Status |
|---|---|---|
| Agent never pushes; user alone performs required pushes | 01 | unresolved / flagged-unverified |
| Incomplete USB data never becomes confirmed complete merely from readable stable bytes | 02 | unresolved / flagged-unverified |
| Discovery/restoration/page reopening never starts audio or silently replaces active queue | 03 | unresolved / flagged-unverified |
| Headphone loss never permits audible restart until explicit app/system Play | 09 | unresolved / flagged-unverified |

4 surfaced = 4 authored; no fabricated wired-check descriptor or pre-existing test is claimed. Tests/tasks provide separate implementation evidence. Descriptor-less items remain flagged for verifier review rather than silently passing.

## Out of scope and subsequent phases

Phase 2 adds actual folder hierarchy operations/directory-transfer verification and folder modes. Phase 3 adds saved moments. Phase 4 adds waveform, A–B and moment behavior. Phase 5 adds collections/tags. Phase 6 adds EQ. Phase 7 completes all three bundled skins, switching and ZIP/base-skin import/export through the shared loader. Phase 8 adds final portable export/diagnostic export and complete-release checks. The Phase 1 foundations in D-11/D-15 do not implement those later scopes. No deferred idea is reduced or removed from the full release.

## Completion limits

No native source or tests have been executed during planning. No transfer publication rule, minimum-OS runtime, physical silence, sideload installation, memory plateau, seek accuracy or rendered accessibility measurement is presently verified. 01-VALIDATION.md stays draft with nyquist_compliant:false and wave_0_complete:false until execution/audit records actual evidence.
