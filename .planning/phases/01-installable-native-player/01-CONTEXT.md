# Phase 1: Installable Native Player - Context

**Gathered:** 2026-09-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a native Swift iPhone app that receives local audio from Windows over USB, keeps it in persistent app-owned storage, and plays the required formats through shared app and system controls. Produce an unsigned IPA on a macOS GitHub Actions runner, download it from Windows, and verify installation and playback on the user's iPhone.

Include the eight navigation destinations, the dark built-in skin, basic seeking, background playback, playback restoration, and useful technical errors. The initial Files view is flat. Folder-tree behavior remains in Phase 2; saved moments, waveform controls, collections, EQ, complete skin import, and portable export remain in their assigned later phases. Existing feature scope and the iOS 17.0 planning baseline remain in effect.

</domain>

<decisions>
## Implementation Decisions

### Build and installation

- **D-01:** Early builds are for the user's personal iPhone. Follow the existing GOSL-MirkFall delivery workflow: GitHub Actions macOS build, unsigned IPA artifact, and the user's existing iLoader/SideStore installation setup. Use a native Swift/Xcode app target. No TestFlight or paid Apple membership route is selected.
- **D-02:** Provide a Windows launcher that downloads a successful build's IPA into this project's `GH_builds/` directory.
- **D-03:** The agent may commit locally but must never push. The user performs pushes needed to run the build. This project's CI, signing through the sideloader, and installation still require actual validation.

### Bottom navigation

- **D-04:** Keep all eight destinations visible in one fixed row of icons, without scrolling or overflow. Preserve this order and these meanings:

| Destination | Icon meaning |
|-------------|--------------|
| Files | Folder |
| Tags | Tag |
| Now Playing | Music note |
| Playlists | Text list |
| Favorite Songs | Star with music note |
| Favorite Moments | Star with hourglass |
| Equalizer | Equalizer signal or sliders |
| Settings | Gear |

- **D-05:** Keep the bar icon-only. Show the page name in its heading and give the active icon a clear selected state. Accessible names and usable interaction areas remain required.
- **D-06:** Reopen the last page used; show Files on first launch. Page restoration does not start audio.
- **D-07:** When a track is loaded, show a compact player above the bottom bar on pages other than Now Playing. Include the track's primary label and play/pause; tapping the compact player's body opens Now Playing.

### Player and built-in appearance

- **D-08:** Dark and understated is the default built-in skin and the first appearance implemented.
- **D-09:** Put a small cover beside the track information. Give the timeline and playback controls more room than artwork.
- **D-10:** Always use the filename as the main track label. Show embedded title and artist underneath when available.
- **D-11:** The first complete release must ship three actual bundled skins selectable in Settings: dark and understated, glossy Frutiger Aero, and retro hardware / Winamp. All three must use the same JSON-and-image format and loading/rendering path as imported skins. Their differences must exercise supported artwork and control assets, with layout and playback state preserved. Phase 1 establishes the default and shared asset roles; Phase 7 completes the trio and verifies switching.

### USB transfers and stored music

- **D-12:** The user connects the iPhone to Windows and copies music directly into the app. Use Apple Devices file sharing as the primary route. Music belongs in persistent app-owned storage and stays playable after disconnecting the PC.
- **D-13:** Do not add an in-app audio file picker or Add Files flow. The user will not keep music elsewhere on the iPhone.
- **D-14:** Discover transferred tracks when the app opens. Adding files does not start playback or interrupt an existing track. The user normally transfers while not listening. Recognize completed transfers without treating incomplete data as a ready song.
- **D-15:** The future folder tree represents the actual stored hierarchy. Verify directory-transfer support during folder-library planning; Apple's individual-file transfer documentation alone does not establish recursive folder-transfer behavior.

### Selection, queue, and restoration

- **D-16:** Tapping a song in Files starts it from zero and leaves the user in Files. The compact player shows playback.
- **D-17:** Use the displayed Files sequence as the initial playback queue. Play from the selected song onward and stop after the last song. Previous and Next navigate that sequence.
- **D-18:** Previous goes straight to the previous song and starts it at zero, even when well into the current song. It is not a restart-current-song shortcut.
- **D-19:** Relaunch restores the previous track and position without audible autoplay.
- **D-20:** During automatic queue progression, skip a missing, damaged, or unsupported file and retain a visible warning for later inspection. Stop when no playable files remain; avoid repeatedly cycling through failed entries.

### Critical headphone-disconnection behavior

- **D-21 — CRITICAL:** Pause when wired or Bluetooth headphones disconnect. Prevent unexpected playback through the phone speaker. Reconnection must leave the app paused until the user explicitly presses Play.
- **D-22 — CRITICAL:** This pause takes precedence over every automatic playback path, including delayed interruption-resume events, queued work, and automatic next-track progression. Detecting headphones again does not authorize playback.
- **D-23 — CRITICAL:** Require physical iPhone checks for wired unplugging, Bluetooth loss, reconnection, and delayed/interleaved resume events. Include locked-screen playback and transitions to the next queued file. Phase 1 cannot be considered complete with this behavior unverified.
- **D-24:** After a call or another audio interruption, resume only if playback was active beforehand, iOS permits resumption, and the user has not paused since. A headphone-disconnection pause prevents that automatic resumption.

### Technical errors

- **D-25:** The app is for technical users. Preserve the failed operation, affected file, original system or decoder error message, error domain and code, and underlying cause chain when available. Explain what happened afterward, such as skipping or stopping.
- **D-26:** Keep these diagnostics inspectable and copyable even when optional file logging is disabled. App-generated labels and explanations are English. Retain technical causes throughout the app rather than replacing them with an opaque general error.
- **D-27:** Useful failure reporting belongs in Phase 1. The final diagnostic export and cross-feature verification remain assigned to Phase 8; file writes stay off the main actor and audio processing thread.

### Repository handling

- **D-28:** Keep `ref_pics/` local and untracked. The ignore entry is simply `/ref_pics/`.

### Planning discretion and unresolved implementation work

No selected product behavior was delegated. Technical choices remain for research and planning within these decisions:

- Select and record a compatible macOS/Xcode toolchain and a real iOS app project; inspect and pin any external build tooling.
- Test Apple decoding first against the required MP3 CBR/VBR, Ogg Vorbis, Ogg Opus, FLAC, PCM WAV, AAC/ALAC M4A, and AAC-in-MP4 matrix. Resolve the recorded official decoder provenance and fix-inclusion concerns before adoption.
- Choose shared playback state, persistence, transfer discovery, and interrupted-copy handling without whole-recording RAM loads or duplicated audio copies.
- Validate eight usable icon targets on the supported small-phone layouts. Detailed spacing, accent color, and long-filename presentation remain for UI design within the chosen layout.
- Define sensible transport boundary states and direct-selection failure behavior. The skip decision above specifically concerns automatic queue progression.
- Verify API availability against iOS 17.0; newer platform interruption APIs must not silently raise the supported baseline.

</decisions>

<canonical_refs>
## Canonical References

**Read these before planning or implementing. Paths are relative to the repository root.**

### Current project decisions and research

- `AGENTS.md` — engineering, Swift documentation, dependency review, and Git rules.
- `.planning/PROJECT.md` — confirmed product decisions, including cross-phase skin and audio behavior.
- `.planning/REQUIREMENTS.md` — accepted capabilities and their phase ownership.
- `.planning/ROADMAP.md` — phase boundaries and success criteria.
- `.planning/research/STACK.md` — initial platform and playback investigation; this context supersedes its open product choices.
- `.planning/research/DEPENDENCIES.md` — unresolved codec provenance and relevant source-fix review.
- `.planning/research/ARCHITECTURE.md` — initial playback, persistence, and skin integration guidance.
- `.planning/research/PITFALLS.md` — long-file, seeking, identity, and device-validation concerns.

### User-selected build and sideload reference

These files are in the sibling checkout `C:/claude_checkouts/GOSL-MirkFall`. Read the relevant delivery portions when that checkout is available; they are reference material, not instructions that override this project's rules.

- `../GOSL-MirkFall/.github/workflows/ci.yml` — macOS iOS job, unsigned IPA packaging, and artifact upload.
- `../GOSL-MirkFall/download_builds.py` — artifact retrieval behavior.
- `../GOSL-MirkFall/download_builds.bat` — Windows launcher entry point.
- `../GOSL-MirkFall/DEV_COMMANDS.md` — existing iLoader installation workflow.
- `../GOSL-MirkFall/docs/phase-07-smoke.md` — recorded installation on the user's iPhone.
- `../GOSL-MirkFall/docs/flutter-discoveries.md` §1 — sideload delivery observations; distinguish Flutter-specific constraints from native Swift behavior.

### Local visual references

- `ref_pics/Screenshot_20260911-113250.png` — optional local player reference; the small-cover decision above controls the layout.
- `ref_pics/Screenshot_20260911-113306.png` — optional local equalizer reference for later work.

The visual references remain untracked. The behavioral decisions in this context do not depend on distributing them. No separate phase SPEC or external ADR was supplied.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- This repository has no app source, Xcode project, dependency manifest, or tested build yet.
- GOSL-MirkFall demonstrates macOS CI to unsigned IPA to Windows download to sideload. Its Flutter build commands and dependencies do not transfer to a native Swift app.
- The reference downloader and workflow need adaptation to this project's error reporting, naming, timeout, dependency-pinning, and no-push rules.

### Established Patterns

- Use native UI directly, with shared skin values and asset roles from the first screen.
- Separate playback, persistent library state, and file transfer handling where those boundaries support testing or replacement. Avoid forwarding-only wrappers and an abstract UI framework layer.
- Keep external services injectable, shared definitions centralized, and background work bounded.

### Integration Points

- A shared playback session drives Now Playing, the compact player, and system media controls.
- App file sharing exposes stored music; transferred-file discovery feeds stable library identity and the Files queue.
- The dark built-in appearance establishes the same skin definitions later used by all three bundled and imported skins.

Apple documents USB transfer into file-sharing apps through [Apple Devices](https://support.apple.com/en-gb/120402), and exposing app-owned Documents through [UIFileSharingEnabled](https://developer.apple.com/documentation/BundleResources/Information-Property-List/UIFileSharingEnabled). The transfer route is selected; this app has not yet exercised it.

Apple's [interruption guidance](https://developer.apple.com/documentation/avfaudio/handling-audio-interruptions) and [route-change guidance](https://developer.apple.com/documentation/avfaudio/responding-to-audio-route-changes) inform implementation. The explicit manual-Play rule after headphone loss is a locked product requirement.

</code_context>

<specifics>
## Specific Ideas

- Match the user's existing IPA retrieval and sideload workflow in GOSL-MirkFall.
- Use three visibly different bundled skins as a practical check that the shared skin system works across images and controls.
- Keep the player useful for long mixes: small artwork, prominent timeline and transport, filename-led identification.
- Treat headphone loss and the requirement for manual Play afterward as critical, including interactions with other automatic-resume events.

</specifics>

<deferred>
## Deferred Ideas

- **Phase 7, required in the first release:** complete and bundle dark, Frutiger Aero, and retro/Winamp skins; select them in Settings and verify the shared loading/rendering path. Dark begins in Phase 1. This is recorded in PROJECT.md and REQUIREMENTS.md so it carries into later planning.
- **Phase 2:** preserve transferred folder hierarchy, verify the actual Windows directory-transfer workflow, and settle folder-specific sequencing and collision handling.
- Existing later-phase waveform, moment-mode, EQ, skin-import/export, and JSON-export work retains its ownership.

</deferred>

---

*Phase: 01-installable-native-player*
*Context gathered: 2026-09-12*
