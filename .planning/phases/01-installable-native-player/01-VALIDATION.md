---
phase: "01"
slug: installable-native-player
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-12"
---

# Phase 1 — Validation Strategy

All 20 plans remain incomplete. The first app slice, native tests and build tooling are authored and locally reviewed. Xcode execution, codec measurements, installation and physical output checks remain pending.

## Execution evidence recorded on 2026-09-12

- Python 3.14.3: `python -m unittest discover -s tests -p test_native_check.py -v` passed 23 tests. These exercise build tooling, copied mock evidence rejection, packaging and cross-file build configuration agreement; they do not execute Swift or prove audio behavior.
- `python -m py_compile scripts/native_check.py tests/test_native_check.py` and `git diff --check` passed.
- The native acceptance command exited 1 on Windows with the expected macOS/Xcode requirement. Native RED/GREEN behavior remains unrun, not passed or meaningfully failed.
- The evidence-only command reports missing `build/native-evidence.json`. No actual macOS run or report exists yet.
- Plan 01 is paused at its user-only push checkpoint. Task 1 source is prepared; Task 1 native acceptance and Task 2 evidence remain pending together. No requirement is marked complete.

## Test infrastructure and command preparation

| Property | Concrete planned value |
|---|---|
| Creating task | 01-01-T1 creates MusicPlayer.xcodeproj, shared MusicPlayer scheme, MusicPlayerTests, MusicPlayerUITests and scripts/native_check.py |
| macOS toolchain | DEVELOPER_DIR=/Applications/Xcode_26.6.app/Contents/Developer; require Xcode 26.6 / 17F113; Swift language 6; deployment iOS 17.0 |
| Cwd | Repository root for every command in this document |
| Native wrapper | python3 scripts/native_check.py prepares toolchain, resolves actual simulator ID into TEST_DESTINATION, builds current source and invokes xcodebuild |
| Native test invocation | xcodebuild test -project MusicPlayer.xcodeproj -scheme MusicPlayer -destination "$TEST_DESTINATION" -resultBundlePath uniqueResultPath |
| Warm selected checks | test-without-building is allowed only after current-SHA matching build-for-testing; requested class must execute nonzero tests |
| Full integrated command | python3 scripts/native_check.py --full --release |
| Windows tests | python -m unittest discover -s tests -p test_download_builds.py -v |
| Windows evidence-only check | python scripts/native_check.py --check-evidence build/native-evidence.json --expected-sha HEAD |
| Runtime target | Selected warm tests target under 60 seconds, measured during execution; full build, matrix/long-file workloads and device checks are explicitly longer jobs |

The wrapper resolves HEAD through git rev-parse, requires source identity, records exact commands/toolchain/runtime/test counts and rejects stale/missing/zero-test reports. It cannot turn Windows into Xcode. Missing iOS 17 runtime remains outstanding even when the iOS 17 deployment build and current-OS tests pass. Evidence-only mode does not validate physical observations. 01-01-T1's actual native acceptance is discharged through the user-triggered run in 01-01-T2; neither task is runtime-complete beforehand.

## Per-task verification map

| Task | Wave | Requirement coverage | Behavior | Automated command | Status |
|---|---|---|---|---|---|
| 01-01-T1 | 1 | APP-01, APP-02, BUILD-01, LIB-01, PLAY-01, PLAY-06, SKIN-01 | Wire one app-owned WAV from Files through real persistence and audio | `python3 scripts/native_check.py --suite NativeTracerTests --ui-suite NativeTracerUITests --release` | Source prepared; native acceptance pending |
| 01-01-T2 | 1 | APP-01, APP-02, BUILD-01, LIB-01, PLAY-01, PLAY-06, SKIN-01 | Have the user trigger the prepared build and collect native evidence | `python scripts/native_check.py --check-evidence build/native-evidence.json --expected-sha HEAD` | Pending; user action/physical evidence required |
| 01-02-T1 | 2 | BUILD-01, LIB-01, APP-01 | Download the exact successful native build safely from Windows | `python -m unittest discover -s tests -p test_download_builds.py -v` | Pending |
| 01-02-T2 | 2 | BUILD-01, LIB-01, APP-01 | Install the concrete artifact and observe Apple Devices transfers | `python scripts/native_check.py --check-evidence build/native-evidence.json --expected-sha HEAD` | Pending; user action/physical evidence required |
| 01-03-T1 | 3 | LIB-01, PLAY-01, PLAY-07 | Reconcile transferred media and preserve the current listening session | `python3 scripts/native_check.py --suite TransferDiscoveryTests` | Pending |
| 01-04-T1 | 4 | LIB-01, APP-02, PLAY-01 | Expose ready and pending rows with complete read-only file details | `python3 scripts/native_check.py --suite FilesOrderTests --ui-suite FilesViewTests` | Pending |
| 01-05-T1 | 5 | LIB-01, APP-02 | Keep discovery failures inspectable across relaunch | `python3 scripts/native_check.py --suite DiagnosticStoreTests` | Pending |
| 01-06-T1 | 6 | SKIN-01, APP-02 | Render real shared image-backed skin roles in native controls | `python3 scripts/native_check.py --suite SkinTests` | Pending |
| 01-07-T1 | 7 | APP-02, APP-03, SKIN-01 | Navigate all eight pages and restore the last page | `python3 scripts/native_check.py --ui-suite NavigationTests` | Pending |
| 01-08-T1 | 8 | APP-02, APP-03, SKIN-01 | Give the installed native app its bundled icon and inspect small-screen appearance | `python3 scripts/native_check.py --suite SkinTests --ui-suite SkinLayoutTests --release` | Pending |
| 01-09-T1 | 9 | PLAY-01, PLAY-03, PLAY-06, PLAY-02 | Play long files through reusable buffers and correct audible completion | `python3 scripts/native_check.py --suite PCMProducerTests --suite NativeTracerTests` | Pending |
| 01-09-T2 | 9 | PLAY-01, PLAY-03, PLAY-06, PLAY-02 | Make every automatic start obey current user intent and loss inhibition | `python3 scripts/native_check.py --suite PlaybackPolicyTests --suite PlaybackRaceTests` | Pending |
| 01-10-T1 | 10 | PLAY-01, PLAY-03, APP-01 | Create known audio fixtures and exercise the Apple path | `python3 scripts/native_check.py --suite AppleCodecMatrixTests` | Pending |
| 01-10-T2 | 10 | PLAY-01, PLAY-03, APP-01 | Measure long seeks and minimum-OS support before decoder selection | `python3 scripts/native_check.py --suite AppleCodecMatrixTests --suite LongRecordingTests` | Pending |
| 01-11-T1 | 11 | PLAY-01, PLAY-03 | Build only reviewed native sources needed by failed Apple cells | `python3 scripts/build_native_codecs.py --verify-required-gaps docs/codec-matrix.md` | Pending |
| 01-12-T1 | 12 | PLAY-01, PLAY-03 | Play and seek missing Ogg formats through bounded native adapters | `python3 scripts/native_check.py --suite CodecMatrixTests --suite PlaybackRaceTests` | Pending |
| 01-12-T2 | 12 | PLAY-01, PLAY-03 | Play MP4 audio correctly and complete the required codec matrix | `python3 scripts/native_check.py --suite CodecMatrixTests --suite LongRecordingTests --release` | Pending |
| 01-13-T1 | 13 | PLAY-02, PLAY-07, APP-03 | Navigate a frozen queue and skip failed automatic candidates once | `python3 scripts/native_check.py --suite PlaybackQueueTests --suite PlaybackRaceTests` | Pending |
| 01-13-T2 | 13 | PLAY-02, PLAY-07, APP-03 | Restore real persisted position and page without playback | `python3 scripts/native_check.py --suite RestorationTests --ui-suite RestorationUITests` | Pending |
| 01-14-T1 | 14 | PLAY-02, PLAY-03 | Seek through the real decoder and reconcile confirmed source position | `python3 scripts/native_check.py --suite SeekTests --suite LongRecordingTests` | Pending |
| 01-15-T1 | 15 | PLAY-02, PLAY-03, APP-03, SKIN-01, APP-02 | Render the full player with accessible seeking and truthful state | `python3 scripts/native_check.py --suite SeekTests --ui-suite NowPlayingTests` | Pending |
| 01-15-T2 | 15 | PLAY-02, PLAY-03, APP-03, SKIN-01, APP-02 | Control the same playback from the compact player on all other pages | `python3 scripts/native_check.py --ui-suite CompactPlayerTests` | Pending |
| 01-16-T1 | 16 | PLAY-04, PLAY-05, PLAY-06 | Use shared commands for real interruptions and system transport | `python3 scripts/native_check.py --suite SystemMediaTests --suite PlaybackRaceTests` | Pending |
| 01-17-T1 | 17 | PLAY-04, PLAY-05, PLAY-06 | Keep newly opened media available through locked queue transitions | `python3 scripts/native_check.py --suite LockedFileAccessTests --ui-suite BackgroundStateTests` | Pending |
| 01-18-T1 | 18 | APP-02 | Inspect and copy retained errors from every page | `python3 scripts/native_check.py --ui-suite DiagnosticViewTests` | Pending |
| 01-19-T1 | 19 | APP-02, PLAY-01, LIB-01 | Preserve full error causes across every failing operation and optional logging | `python3 scripts/native_check.py --suite DiagnosticStoreTests --suite DiagnosticFlowTests` | Pending |
| 01-20-T1 | 20 | APP-01, APP-02, APP-03, BUILD-01, PLAY-01, PLAY-02, PLAY-03, PLAY-04, PLAY-05, PLAY-06, PLAY-07, LIB-01, SKIN-01 | Build and review the complete final app on the pinned native route | `python3 scripts/native_check.py --full --release` | Pending |
| 01-20-T2 | 20 | APP-01, APP-02, APP-03, BUILD-01, PLAY-01, PLAY-02, PLAY-03, PLAY-04, PLAY-05, PLAY-06, PLAY-07, LIB-01, SKIN-01 | Install and verify the final source on the real iPhone | `python scripts/native_check.py --check-evidence build/native-evidence.json --expected-sha HEAD` | Pending; user action/physical evidence required |

Every runnable command has its explicit failure signal in the plan's adjacent fails_when element. Native tests fail on nonzero exit, failed results, zero selected-class tests, missing expected matrix rows or stale/mismatched source evidence. Unittest fails on nonzero, FAILED or Ran 0 tests. Conditional codec build checks fail on missing runtime gap evidence, unreviewed/wrong digest or unexpected link targets; they do not claim source checks prove runtime decoding.

## Initial infrastructure ownership

- [ ] 01-01-T1: app/test schemes, actual disk WAV/persistence/UI tracer, pinned native wrapper, uploaded source/count/build evidence, early copyable USB revision observations.
- [ ] 01-01-T2: user-only push and actual macOS run; no source-only success.
- [ ] 01-02-T1: subprocess fakes and safe downloader tests; manifest/checksum/result retrieval.
- [ ] 01-02-T2: actual install/USB writer observations and any evidence-backed required workflow choice before readiness work.
- [ ] 01-03-T1: changing-revision, failed-save, containment and idempotent scan tests.
- [ ] 01-05-T1: bounded original-cause/persistent-history tests.
- [ ] 01-06-T1, 01-07-T1, 01-08-T1: skin JSON/image, navigation and measured layout tests.
- [ ] 01-09-T1, 01-09-T2: bounded producer, delayed callbacks and event-order policy fakes.
- [ ] 01-10-T1, 01-10-T2: canonical legal fixture/tool pins, full codec matrix and long landmarks; large generated files remain ignored.
- [ ] 01-11-T1, 01-12-T1, 01-12-T2: conditional reviewed native source builds and actual production decoder matrix.
- [ ] 01-13-T1, 01-13-T2: queue traversal and real disk/silent-relaunch tests.
- [ ] 01-14-T1, 01-15-T1, 01-15-T2: real source-time seeks, full and compact UI checks.
- [ ] 01-16-T1, 01-17-T1: system-command and unopened-media/protection integration tests.
- [ ] 01-18-T1, 01-19-T1: full diagnostic UI/copy and per-operation original-cause flow tests.
- [ ] 01-20-T1: integrated current-source suite, Release artifact and final metadata validation.
- [ ] 01-20-T2: physical acceptance and explicit unresolved-probe review on final installed SHA.

No third-party test package is planned. Conditional native and fixture-generation source review happens before execution. API/code-source inspection is preparation, never decoder runtime success.

## Sampling and evidence lifetime

Run affected classes after each changed behavior and the full integrated suite at each wave. Measure latency once on the actual environment; do not repeatedly broaden already successful testing without a changed scope or unresolved issue. Capture source SHA, dirty state, toolchain, destination, counts, exact command, duration and unique result path. Final delivery uses clean-source evidence and the exact same artifact hash.

CI explicitly uploads build/native-evidence.json, manifest, checksum, IPA, codec report and xcresult output. Downloader validates and retains original downloaded results, then copies selected native-evidence.json to build/native-evidence.json for Windows evidence checks. A failed run may upload diagnostic test output separately but cannot masquerade as a successful IPA. Actual user-only pushes are required when source has to reach the remote runner; invoke the specified notification script only at that necessary point.

## Physical and rendered completion conditions

| Check | Owning task | Required evidence |
|---|---|---|
| First native install/launch | 01-02-T2 | Actual run/source SHA, IPA checksum, iPhone/OS, existing sideloader result |
| Early USB publication facts | 01-02-T2 | App closed/open, foreground mid-copy, unplug mid-copy including readable MP3 prefix, overwrite/retry/replacement, observed identities/sizes/times/revisions |
| Final USB persistence/readiness | 01-20-T2 | Completed file plays after cable removal; interrupted/unverified bytes are not ready; accepted workflow documented |
| Required codec/container playback | 01-10-T2, 01-20-T2 | All nine named codec/container cases, actual audible start, duration and seek landmarks; per-OS results |
| Long seek/memory | 01-10-T2, 01-20-T2 | Three-hour input, known landmarks within 100 ms target, fixed scheduling limits, memory plateau within 32 MiB of comparable short warm baseline |
| Wired and Bluetooth loss | 01-20-T2 | Playing/locked unplug or loss, no speaker audio, reconnect remains paused until explicit app/system Play |
| Delayed/interleaved next-file behavior | 01-20-T2 | Loss around interruption-end/preparation/seek/EOF and newly opened next file; Next/selection/seek cannot clear loss latch |
| Background and system commands | 01-17-T1, 01-20-T2 | After first unlock, lock and open previously unopened next media; real play/pause/previous/next/seek and current metadata |
| Silent restoration | 01-13-T2, 01-20-T2 | Terminate/relaunch restores confirmed track/time/page without sound or activation; missing file error retained |
| Small-phone touch/contrast | 01-08-T1, 01-20-T1, 01-20-T2 | 375-by-667 and target sizes, portrait/landscape safe widths, actual separate >=44 pt targets and measured rendered contrast |
| Accessibility | 01-15-T1, 01-15-T2, 01-20-T1, 01-20-T2 | Largest accessibility type, VoiceOver order/labels/selection/seek adjustments/focus, long filenames/causes and warning+compact+navigation |
| Diagnostics without optional logging | 01-18-T1, 01-19-T1, 01-20-T2 | Inspect and copy full original causes after errors, later successful playback and relaunch with optional writer disabled |
| Minimum-OS runtime | 01-10-T2, 01-20-T2 | Actual iOS 17 simulator/device evidence; newer SDK/current-OS runs do not substitute |

Any required physical result absent or failed remains outstanding. For arbitrary truncated MP3, successful open, stable size and even a valid full decode of the prefix cannot prove source intent. If actual publication semantics do not suffice, the necessary user workflow choice stays pending before 01-03 readiness completion; no silent mandatory manifest or invented guarantee is permitted.

## Probe and source accounting

SKELETON.md contains the complete GOAL/REQ/RESEARCH/CONTEXT assignment table. All 13 requirement IDs and D-01 through D-28 are assigned. All 44 approved UI consideration rows are lifted verbatim into relevant must_haves as planned criteria.

The supplied edge report has 18 rows: 10 classified rows have explicit planned truths; 8 unclassified rows remain unresolved flagged assumptions tied to real execution checks. Four bespoke prohibitions were emitted through projectProhibitions as descriptor-less unresolved objects in plans 01, 02, 03 and 09. No test descriptor, previous passing test or automatic prohibition pass is fabricated. Runtime verifier review must retain flagged items until supported by actual evidence.

## Validation sign-off

- [x] Every task has a grounded automated command and adjacent observable failure statement in its plan.
- [x] New scripts/test classes have concrete creating tasks; native evidence upload/download is explicit.
- [x] Final plan/task/wave mapping is complete.
- [ ] Initial infrastructure actually exists and has executed.
- [ ] Selected-test latency is measured on macOS.
- [ ] All required native and physical results are recorded for final source.
- [ ] All probe assumptions/prohibitions and high/critical threats have explicit verified dispositions.
- [ ] Nyquist execution/audit has confirmed compliance.

**Approval:** Planning map complete; execution and validation audit pending.
