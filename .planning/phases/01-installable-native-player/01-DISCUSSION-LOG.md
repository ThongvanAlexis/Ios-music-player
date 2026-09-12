# Phase 1: Installable Native Player - Discussion Log

> **Human reference only.** Planning, research, and execution should use 01-CONTEXT.md. This record preserves the choices discussed.

**Date:** 2026-09-12
**Phase:** 01-installable-native-player
**Areas discussed:** Installation, bottom navigation, first player screen and base appearance, import and playback behavior.

The user selected all four offered areas. Additional repository-handling instructions are recorded neutrally below.

## Installing on your iPhone

### Who needs to be able to install the first working builds of this app?

| Option | Description | Selected |
|--------|-------------|----------|
| Just me on my iPhone | As presented | Yes |
| Me and a small group of testers | As presented |  |
| Anyone through a public release | As presented |  |

**User's choice:** Just the user. Produce an IPA for personal sideloading, following the existing workflow in C:\claude_checkouts\GOSL-MirkFall.

**Notes:** Inspected the reference project's CI workflow, download launcher, installation instructions, and recorded iPhone test. Use GitHub Actions with a macOS runner to build the native Swift app and package an unsigned IPA for the user's existing iLoader/SideStore setup. No paid Apple membership or TestFlight route is planned. The user performs pushes; the agent must never push. This selects the route; this project's build and phone installation still require verification.

### How would you like to retrieve this app's IPA after a successful build?

| Option | Description | Selected |
|--------|-------------|----------|
| A Windows launcher that downloads it into this project's GH_builds folder, like MirkFall (Recommended) | As presented | Yes |
| I'll download the IPA manually from GitHub Actions | As presented |  |

**User's choice:** A Windows launcher that downloads it into this project's GH_builds folder, like MirkFall.

### Anything else to settle about installation, or shall we move to bottom navigation?

| Option | Description | Selected |
|--------|-------------|----------|
| Move to bottom navigation | As presented | Yes |
| More about installation | As presented |  |

**User's choice:** Move to bottom navigation

## Repository handling

### User-supplied constraint

**User's choice:** Keep ref_pics local and untracked; use the bare /ref_pics/ ignore entry.

## Bottom navigation

### How should the eight bottom navigation destinations fit on the screen?

| Option | Description | Selected |
|--------|-------------|----------|
| Two rows of four | all destinations visible with room for labels; uses more height (Recommended) |  |
| One row of eight icons | compact and always visible; little room for labels | Yes |
| One horizontally scrollable row | larger buttons; some destinations require a swipe |  |

**User's choice:** One row of eight icons — compact and always visible; little room for labels.

**Notes:** Keep the agreed order: Files, Tags, Now Playing, Playlists, Favorite Songs, Favorite Moments, Equalizer, Settings. All eight remain visible without scrolling. Skins preserve the layout.

### With eight icons in one row, where should the current page's name appear?

| Option | Description | Selected |
|--------|-------------|----------|
| In the page heading only; keep the bottom bar icon-only (Recommended) | As presented | Yes |
| In the page heading and as a small label under the active icon | As presented |  |

**User's choice:** In the page heading only; keep the bottom bar icon-only.

**Notes:** The active icon also has a clear selected state.

### Which page should open when you launch the app?

| Option | Description | Selected |
|--------|-------------|----------|
| The last page used, with Files on the first launch (Recommended) | As presented | Yes |
| Files every time, ready to choose music | As presented |  |
| Now Playing when a track is loaded, otherwise Files | As presented |  |

**User's choice:** The last page used, with Files on the first launch.

**Notes:** Restoring a track and position remains paused; page restoration does not trigger autoplay.

### While you browse other pages with a track loaded, should playback controls stay visible?

| Option | Description | Selected |
|--------|-------------|----------|
| Show a compact player above the bottom bar: track title and play/pause; tapping it opens Now Playing (Recommended) | As presented | Yes |
| Keep playback controls on Now Playing; use its bottom icon to reach them | As presented |  |

**User's choice:** Show a compact player above the bottom bar: track title and play/pause; tapping it opens Now Playing.

**Notes:** The compact player appears on pages other than Now Playing when a track is loaded.

### More to discuss about bottom navigation, or move to the first player screen and base appearance?

| Option | Description | Selected |
|--------|-------------|----------|
| Move to player screen and appearance | As presented | Yes |
| More about bottom navigation | As presented |  |

**User's choice:** Move to player screen and appearance

## First player screen and base appearance

### What should the built-in skin look like before you import any custom skin?

| Option | Description | Selected |
|--------|-------------|----------|
| Dark and understated | neutral surfaces, one accent color, clear controls (Recommended) | Yes |
| Glossy Frutiger Aero | glass-like panels, gradients, and bright accents | Yes |
| Retro hardware / Winamp | framed panels and tactile-looking controls | Yes |

**User's choice:** Ship all three selectable in Settings: dark and understated, glossy Frutiger Aero, and retro hardware / Winamp.

**Notes:** The user emphasized that these must be actual bundled skins and a practical test of the skin implementation. All three use the same JSON-and-image format and loading path as imported skins. Switching must change supported artwork and control appearance while preserving layout and playback state. The complete trio belongs to the first release; Phase 1 establishes the default and Phase 7 completes and verifies the skin system.

### Which theme should be the default and the first one implemented in Phase 1?

| Option | Description | Selected |
|--------|-------------|----------|
| Dark and understated (Recommended) | As presented | Yes |
| Glossy Frutiger Aero | As presented |  |
| Retro hardware / Winamp | As presented |  |

**User's choice:** Dark and understated as default.

### How prominent should artwork be on the Now Playing screen?

| Option | Description | Selected |
|--------|-------------|----------|
| Small cover beside the track information; give the timeline and playback controls more room (Recommended for long mixes) | As presented | Yes |
| Large artwork above the track information, similar to the reference image | As presented |  |
| No artwork; focus entirely on track information, time, and controls | As presented |  |

**User's choice:** Small cover beside the track information; give the timeline and playback controls more room.

### How should Now Playing identify a track when its embedded title differs from its filename?

| Option | Description | Selected |
|--------|-------------|----------|
| Show the title and artist when available, falling back to the filename; keep the filename available in details (Recommended) | As presented |  |
| Always show the filename as the main title, with embedded title and artist underneath when available | As presented | Yes |

**User's choice:** Always show the filename as the main title, with embedded title and artist underneath when available.

### More to discuss about the player screen and appearance, or move to import and playback behavior?

| Option | Description | Selected |
|--------|-------------|----------|
| Move to import and playback behavior | As presented | Yes |
| More about player screen and appearance | As presented |  |

**User's choice:** Move to import and playback behavior

## Import and playback behavior

### What should happen after an audio file finishes importing?

| Option | Description | Selected |
|--------|-------------|----------|
| Add it to Files without starting playback or interrupting the current track (Recommended) | As presented | Yes |
| Start the imported file only if nothing is currently playing | As presented |  |
| Immediately play the imported file, replacing the current track | As presented |  |

**User's choice:** Add it to Files without starting playback or interrupting the current track.

**Notes:** The user's expected workflow is connecting the iPhone to Windows by USB and copying music directly into the app. They usually will not be listening while transferring. Planning must support that primary workflow and discover completed transfers when the app opens, without starting audio.

### Alongside USB transfer from your PC, should the app also have an Add Files button for music already accessible through the iPhone's Files app?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, support both; USB transfer remains my main workflow (Recommended) | As presented |  |
| USB transfer is enough; no in-app file picker needed | As presented | Yes |

**User's choice:** USB transfer is enough; no in-app file picker needed. The user will not keep songs elsewhere on the phone.

**Notes:** Music lives in app-owned persistent storage and remains playable after disconnecting from the PC. The folder tree represents those stored files. Apple Devices file sharing is the primary Windows route. Folder hierarchy remains required in the folder-library phase; verify folder-transfer details rather than assuming a file-only transfer guide establishes directory support.

### What should tapping a song in Files do?

| Option | Description | Selected |
|--------|-------------|----------|
| Play it from the beginning and stay in Files; the compact player shows what's playing (Recommended) | As presented | Yes |
| Play it from the beginning and switch to Now Playing | As presented |  |

**User's choice:** Play it from the beginning and stay in Files; the compact player shows what's playing.

### When advancing to the next track encounters a missing, damaged, or unsupported file, what should happen?

| Option | Description | Selected |
|--------|-------------|----------|
| Skip it and keep listening, with a visible warning saved for later inspection (Recommended) | As presented | Yes |
| Stop playback and show the error with Retry and Skip actions | As presented |  |

**User's choice:** Skip it and keep listening, with a visible warning saved for later inspection.

**Notes:** Stop if no playable files remain; avoid repeatedly cycling through failed files.

### User-supplied error-reporting requirement

**User's choice:** The app is for technical users. Error messages must explain what is actually happening and preserve technical causes.

**Notes:** Retain the failed operation, affected file, original system or decoder error message, error domain and code, and underlying cause chain where available. Explain the recovery action taken, including skipping or stopping. Keep diagnostics inspectable and copyable, including when optional file logging is disabled. Apply this error-reporting policy throughout the app.

### Would you like to settle the remaining playback details—queue behavior, Previous, and interruptions—or leave those details to my judgment and capture the phase context?

| Option | Description | Selected |
|--------|-------------|----------|
| Discuss the remaining playback details | As presented | Yes |
| Use your judgment for those details and capture the context | As presented |  |

**User's choice:** Discuss the remaining playback details

### After you select a song in Files and it finishes, what should happen in Phase 1?

| Option | Description | Selected |
|--------|-------------|----------|
| Continue through the Files list in its displayed order, stopping after the last song (Recommended) | As presented | Yes |
| Stop after the selected song; Previous and Next still let me move through the list manually | As presented |  |

**User's choice:** Continue through the Files list in its displayed order, stopping after the last song.

**Notes:** The initial Files list is flat. Folder-specific playback rules remain in the folder-library phase.

### What should Previous do when you're already partway through a song?

| Option | Description | Selected |
|--------|-------------|----------|
| Go straight to the previous song and start it at zero (Recommended) | As presented | Yes |
| Restart the current song; a second quick tap goes to the previous song | As presented |  |

**User's choice:** Go straight to the previous song and start it at zero.

### After a call or other audio interruption ends and iOS permits playback again, what should the player do?

| Option | Description | Selected |
|--------|-------------|----------|
| Resume automatically if it was playing before the interruption and I haven't paused it since (Recommended) | As presented | Yes |
| Stay paused until I press Play | As presented |  |

**User's choice:** Resume automatically if it was playing before the interruption and I haven't paused it since.

**Notes:** Resume only when the system permits it, and respect any intervening user pause. Cold relaunch still restores the track and position without audible autoplay.

### After wired or Bluetooth headphones disconnect during playback, what should happen when they reconnect?

| Option | Description | Selected |
|--------|-------------|----------|
| Stay paused until I press Play (Recommended) | As presented | Yes |
| Resume automatically if playback was active before disconnection and I haven't paused it since | As presented |  |

**User's choice:** CRITICAL: pause when either wired or Bluetooth headphones disconnect. Do not resume automatically when headphones are detected again; require an explicit press of Play.

**Notes:** The user explicitly emphasized that this is critical. Disconnection must prevent unexpected speaker playback. This pause takes precedence over interruption-resume hints, delayed callbacks, automatic queue progression, and reconnection. Require physical iPhone verification of wired unplugging, Bluetooth loss, reconnection, and delayed/interleaved resume events before Phase 1 can be considered complete.

## Completion

After reviewing the decisions across all four areas, the user answered "nope" when asked whether anything else remained before capturing the context.

## Planning Discretion

No selected product behavior was delegated. Toolchain selection, reviewed decoder choices, detailed UI sizing, transfer discovery, and other technical implementation work remain for planning within the captured decisions.

## Deferred Ideas

- Complete the three actual bundled skins in Phase 7, within the first release; dark is the default established in Phase 1.
- Preserve folder hierarchy and verify directory transfer from Windows with the Phase 2 folder-library work.
