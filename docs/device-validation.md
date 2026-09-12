# Native and physical validation

The native simulator suite and unsigned Release build passed on GitHub Actions for the source recorded below, including playback retry and clean SQLite teardown. Installation, USB transfer observations and physical audio checks remain pending.

The prepared GitHub workflow builds the checked-in Xcode project using the toolchain in `build_config.json`. Repository instructions authorize agent pushes to trigger IPA builds. After a push, preserve the downloaded run's original artifact and validate a selected copy with:

```powershell
python scripts/native_check.py --check-evidence build/native-evidence.json --expected-sha HEAD
```

The native acceptance command on macOS is:

```sh
python3 scripts/native_check.py --suite NativeTracerTests --ui-suite NativeTracerUITests --release
```

The tests are authored against real SQLite, generated PCM WAV files, the playback engine's actual rendered output, the transferred simulator file, and route-loss inhibition. A successful native run is recorded below. Earlier Swift 6 compile failures were corrected; they do not constitute a meaningful failing behavior test. The native tests were not executed before implementation, so no native RED-before-GREEN result is claimed.

| Build evidence | Recorded result |
|---|---|
| Tested source SHA | 6c7f4bbf972d8f87fa1275537e64a53158651237 |
| Workflow run URL and run ID | https://github.com/ThongvanAlexis/Ios-music-player/actions/runs/34712414765 |
| Runner image and macOS version | 20260907.0351.1; macOS 26.6.2 (25G83), arm64 |
| Xcode version and build | 26.6 / 17F113 |
| iPhone SDK and simulator runtime | SDK 26.5; iOS 26.5 |
| Simulator UUID | CB15797E-6053-40B1-BB72-7F30D005A4F2 |
| Executed native test counts | 9 passed; zero failures or skips |
| Executed UI test counts | 1 passed; zero failures or skips |
| Result bundle location | build/results/20260912T185058Z-56d7048fb7bc42729938105da2524058/NativeTests.xcresult |
| Unsigned IPA SHA-256 | 103aef4863d92e329fd14dac20e5254f80593a583560938deaa18a8be3d719bc |
| Native evidence validation | Passed on Windows against HEAD at the tested source above, before checkpoint documentation |

The successful artifact includes the unsigned IPA, manifest, checksum, native evidence and result bundles. Failed native runs retain a separate diagnostic artifact. No signing credential is required by this workflow; the existing sideload setup signs the unsigned app at installation.

From PowerShell in the repository, use the Windows launcher to retrieve the newest successful configured build:

```powershell
.\download_builds.bat
```

To choose a specific build, pass `--run-id RUN_NUMBER`, `--sha FULL_COMMIT_SHA`, or both. An explicit selection never falls back to another source. The command prints the selected full SHA and verified IPA path under `GH_builds`. Keep that directory's original manifest, reports and ZIP alongside the IPA. If a request fails, previous downloaded builds remain available; use the reported recovery steps and retry the same selection.

The downloader checks the repository, workflow, branch, successful run, GitHub ZIP digest, IPA checksum, embedded app identity and native evidence before publication. It keeps the original native report and copies the selected report to `build/native-evidence.json`. The evidence command above uses `HEAD` only when that commit is the downloaded source; for a deliberately selected older build, supply its full SHA instead.

Windows validation on 2026-09-12 passed 44 tooling tests, including 21 downloader tests and actual batch-launcher execution. The live launcher also retrieved and verified run `34710813866` for source `9115f759514b93a94f4f9856d986c0626ac4b3bd`, preserving the original archive and reports in `GH_builds/run-34710813866-9115f759514b-e5717d423ff1`. This verifies delivery to Windows; installation on the iPhone remains pending.

The prepared phone build is now `GH_builds/run-34712414765-6c7f4bbf972d-33ba8ce83615/artifact/MusicPlayer-unsigned.ipa`, verified by the real launcher for source `6c7f4bbf972d8f87fa1275537e64a53158651237`. Its original ZIP and reports remain in that build directory. The final CI run passed 9 app tests, 1 UI test and unsigned Release; its tooling suite passed with only the two Windows-specific tests skipped on macOS. Both Windows-specific tests passed locally. Use this prepared IPA for the installation observations below.

| Installation evidence | Recorded result |
|---|---|
| Date and time in UTC | Pending |
| iPhone model | Pending |
| Installed iOS version | Pending |
| Installed artifact source SHA, matched to the selected IPA manifest | Pending |
| IPA source run URL and checksum | Pending |
| Sideload method | Pending |
| Initial empty Files screen and silent launch | Pending |
| Relaunch without automatic sound | Pending |

For USB observations, open the information button beside each Files row. **File Details** contains selectable text and **Copy File Details**, including the relative location, observed time, filesystem identity, size, modification time, revisions before and after parsing, declared WAV length when present, and parser outcome. These details exist for pending or unsupported files as well as playable WAV files. Return to the app or pull the Files list to refresh its observations.

Only a closed integer PCM WAV is playable in this first build. A stable size or a decodable MP3 prefix does not establish the intended source length. Unsupported files remain pending and inspectable. A source manifest is not required by this build.

| Physical behavior | Observation and result |
|---|---|
| Apple Devices exposes this app's Files container | Pending |
| Copy a complete PCM WAV by USB; inspect its pre/post revisions | Pending |
| Disconnect USB and play the transferred WAV audibly | Pending |
| Observe a growing WAV during copying and after completion | Pending |
| Observe an interrupted MP3 copy and a completed MP3 copy | Pending |
| Repeat a filename replacement and compare resource identity | Pending |
| Relaunch the app and verify the file remains available | Pending |
| Lock the iPhone during playback | Pending |
| Disconnect wired headphones while playing | Pending |
| Reconnect wired headphones; confirm no sound before explicit Play | Pending |
| Disconnect Bluetooth output while playing | Pending |
| Reconnect Bluetooth; confirm no sound before explicit Play | Pending |
| Select a different file after output loss; confirm no automatic sound | Pending |
| Open Error Details and copy the original technical message | Pending |

Error Details retains bounded messages during this app process, independently of playback success. Transfer parser observations survive relaunch in SQLite. A general diagnostic history across relaunch and the later full transport controls are not supplied by this first build.

Preserve actual copied observation text and original run artifacts alongside the recorded results. Leave unperformed or unsuccessful checks pending with their observed error.

The first phone session should follow this order:

1. Install the prepared unsigned IPA through the existing iLoader/SideStore setup. Record its full source SHA, run ID and checksum, the installation result, and the iPhone model/iOS version. Open MusicPlayer and check that an empty Files screen is silent.
2. In Apple Devices on Windows, select the iPhone and its file-sharing section, then MusicPlayer. Copy the prepared `build/device-probes/native-tracer.wav`, or an existing integer PCM WAV, as an individual file. Record whether the app was closed or open during copying.
3. Open the app, refresh Files, and use the row's information button to copy File Details. Disconnect USB, tap the WAV row, and record whether sound is audible and the playback time advances. Terminate and reopen the app; confirm that the file remains and playback stays stopped.
4. With larger WAV and MP3 files, repeat individual copies with the app closed and open. Bring the app forward during copying, refresh, and copy File Details before and after completion. Record whether a final filename is visible while its bytes are still arriving.
5. Interrupt each large transfer by disconnecting USB, then record the remaining row, its File Details, and the result after relaunch. For MP3, retain the observed byte length so it can be checked against complete frame boundaries in the PC source. A frame-boundary prefix test remains pending until the actual bytes establish that boundary; a guessed disconnect time is insufficient.
6. Reconnect and retry an interrupted transfer using the same filename. Then replace a completed file with different audio under that same filename. Copy the observations before and after each change, including resource identity, byte length, modification time and parsing revisions.
7. Send the recorded outcomes and copied details. If the writer provides no reliable completion signal, keep the completion question open while choosing between explicit pending/unverified handling and an additional source-size/hash manifest step. Neither a stable file nor a fully decodable MP3 prefix establishes the intended source length.

| Transfer experiment | WAV observations | MP3 observations |
|---|---|---|
| Copy with the app closed; open after completion | Pending | Pending |
| Copy with the app open | Pending | Pending |
| Bring the app forward during copying | Pending | Pending |
| Disconnect USB during copying | Pending | Pending |
| Interrupted copy ending at a complete MP3 frame boundary | Not applicable | Pending |
| Relaunch after an interrupted copy | Pending | Pending |
| Retry/overwrite an interrupted copy | Pending | Pending |
| Replace completed audio under the same filename | Pending | Pending |

For each cell, retain the Windows source filename and size, the app's actual relative location, the observation time, and the copied before/after details. A missing row or failed operation is also an observation; preserve its error rather than assuming completion. MP3 playback is not implemented in this initial build, so its transfer observations remain separate from audible WAV playback.
