# Native and physical validation

No native build, simulator result, installation, USB transfer observation, or physical audio check has passed yet. Windows source checks and Python tooling tests do not supply those results.

The prepared GitHub workflow builds the checked-in Xcode project using the toolchain in `build_config.json`. Repository instructions authorize agent pushes to trigger IPA builds. After a push, preserve the downloaded run's original artifact and validate a selected copy with:

```powershell
python scripts/native_check.py --check-evidence build/native-evidence.json --expected-sha HEAD
```

The native acceptance command on macOS is:

```sh
python3 scripts/native_check.py --suite NativeTracerTests --ui-suite NativeTracerUITests --release
```

The tests are authored against real SQLite, generated PCM WAV files, the playback engine's actual rendered output, the transferred simulator file, and route-loss inhibition. Native RED and GREEN test executions remain pending: an unavailable Xcode command is not a failing behavior test. The first macOS run may reveal compiler or runtime issues that require another fix and push.

| Build evidence | Recorded result |
|---|---|
| Tested source SHA | Pending |
| Workflow run URL and run ID | Pending |
| Runner image and macOS version | Pending |
| Xcode version and build | Pending |
| iPhone SDK and simulator runtime | Pending |
| Simulator UUID | Pending |
| Executed native test counts | Pending |
| Executed UI test counts | Pending |
| Result bundle location | Pending |
| Unsigned IPA SHA-256 | Pending |
| Native evidence validation | Pending |

The successful artifact includes the unsigned IPA, manifest, checksum, native evidence and result bundles. Failed native runs retain a separate diagnostic artifact. No signing credential is required by this workflow; the existing sideload setup signs the unsigned app at installation.

| Installation evidence | Recorded result |
|---|---|
| Date and time in UTC | Pending |
| iPhone model | Pending |
| Installed iOS version | Pending |
| Installed source SHA from app bundle `BuildSourceSHA` | Pending |
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
