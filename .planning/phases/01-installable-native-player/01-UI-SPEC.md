---
phase: "01"
slug: "installable-native-player"
status: approved
reviewed_at: "2026-09-12"
shadcn_initialized: false
preset: none
created: "2026-09-12"
---

# Phase 1 — UI Design Contract

Native iPhone visual and interaction contract. Reviewed for planning; rendered UI, builds and physical audio behavior remain subject to execution checks.

## Design System

| Property | Value |
|----------|-------|
| Tool | none |
| Preset | Not applicable; native SwiftUI, iOS 17.0 baseline |
| Component library | Apple SwiftUI with focused UIKit integration where platform behavior requires it; no external UI package |
| Icon library | SF Symbols available on the minimum OS, plus two bundled composite images for the requested favorite destinations |
| Font | System San Francisco; regular 400 and semibold 600 |
| Appearance | Dark and understated; opaque surfaces, restrained cyan accent, small cover, filename first |
| Design-system discovery | No app source, Xcode project, component manifest, existing tokens, or project skills were present during scouting on 2026-09-12 |

No web design-system initialization applies. There is no installed package inventory to enumerate, so the Component Inventory section is omitted. **Could not enumerate native SDK components:** this Windows workspace has no Xcode/iOS SDK; `Get-Command xcrun,swift -ErrorAction SilentlyContinue` returned neither command. Proposed Apple controls below are implementation choices, not claims of installed or verified exports. Record the resolved Xcode/SDK build and verify symbol/API availability during the macOS build.

### Sources and decision authority

| Source | Decisions used |
|--------|----------------|
| 01-CONTEXT.md | D-04 through D-27 govern navigation, appearance, transfers, playback, interruptions, and diagnostics; its phase boundary excludes later feature controls |
| PROJECT.md | Shared JSON/image skin system, fixed layouts, filename priority, native UI, long recordings, English application copy |
| REQUIREMENTS.md | APP-01–03, PLAY-01–07, LIB-01, SKIN-01; basic diagnostics apply now despite final export ownership later |
| ROADMAP.md | Flat Files and honest later-feature destinations in this phase; subsequent phases own folder operations, moments, waveform, collections, EQ, skin selection, and export |
| STATE.md | No build or device behavior has been verified; source checks must not be presented as runtime evidence |
| research/STACK.md | SwiftUI, Apple frameworks, shared skin values and image roles; CONTEXT supersedes its older navigation and delivery alternatives |
| AGENTS.md | Native UI directly; shared definitions once; English application copy; no UI abstraction layer; technical error preservation |
| Research defaults in this document | Numeric spacing, type, colors, overflow, stable flat-list ordering, transport boundaries, and direct-selection failure treatment; these are technical discretion, not additional user decisions |

### Native composition

Use concrete SwiftUI views with standard button, scroll, image, text, progress, and adjustable-control semantics. A custom bottom navigation strip is required to preserve all eight destinations without overflow. Do not use a standard tab configuration that hides destinations behind More. Use one shared playback session for Files selection, full and compact players, and system media controls.

Use a bottom safe-area inset for the navigation strip and compact player. Content must receive the inset and scroll above it. Background may extend into the system bottom inset; hit targets must remain above it. Apple documents [safe-area inset composition](https://developer.apple.com/documentation/swiftui/view/safeareainset(edge:alignment:spacing:content:)). The minimum deployment build must verify the chosen overload.

## Spacing Scale

Values are **iOS points**, not CSS pixels. Centralize them as named shared values.

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4 pt | Metadata separation, selection marker height |
| sm | 8 pt | Compact gaps, navigation outer inset, row vertical padding |
| md | 16 pt | Page horizontal inset, ordinary gaps, row leading/trailing inset |
| lg | 24 pt | Section separation, metadata-to-timeline separation |
| xl | 32 pt | Empty-state top inset, timeline-to-transport separation |
| 2xl | 48 pt | Secondary transport targets, empty-state symbol frame |
| 3xl | 64 pt | Cover frame, main Play/Pause target, minimum compact-player height |

Exceptions: 44 pt is the minimum interaction dimension; 56 pt is the navigation strip height before the system safe-area inset; both are multiples of four. Eight equal navigation slots use a calculated fractional width, not a new spacing token. A one-physical-pixel separator is a rendering detail, not layout spacing. Corner radii are 8 pt for panels and artwork and 4 pt for navigation selection backgrounds; circular transport backgrounds use their frame's half-width.

## Typography

Four authored base sizes and exactly two weights. Values describe the standard Dynamic Type category; scaled accessibility sizes are adaptations of these roles, not new fixed tokens.

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body | 16 pt | 400 | 1.5 / 24 pt baseline |
| Label | 14 pt | 400 | 1.5 / 21 pt baseline |
| Heading | 20 pt | 600 | 1.2 / 24 pt baseline |
| Display | 28 pt | 600 | 1.2 / 33.6 pt baseline |

Body is used for filenames and primary actions. Label is used for embedded metadata, time labels, row statuses, and diagnostic field values. Heading is the page title and empty-state heading. Display is reserved for the elapsed-time readout in Now Playing. Semibold 600 may emphasize a Body filename or selected label without introducing a third weight. Use monospaced digits within the system font for times; diagnostics remain selectable, wrapping system text.

Scale through system Dynamic Type text styles and scaled metrics; preserve at least the stated line-height ratios and allow native metrics to expand. Apple documents [ScaledMetric](https://developer.apple.com/documentation/swiftui/scaledmetric) and recommends checking large accessibility sizes in [typography guidance](https://developer.apple.com/design/human-interface-guidelines/typography). No automatic text shrinking, fixed-height text clipping, or Dynamic Type cap is permitted.

## Color

The 60/30/10 split describes visual emphasis, not an exact pixel-area quota. Small surfaces may contain less accent; do not add cyan decoration to meet a percentage.

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | #101216 | Main page background, empty-state background |
| Secondary (30%) | #1C2026 | Compact player, navigation strip, diagnostic panels, transport surfaces |
| Accent (10%) | #6ED7E5 | Active destination glyph/marker, primary Play/Pause surface, elapsed seek track/thumb, current Files-row marker |
| Primary text | #F2F4F7 | Filenames, page headings, active control content on dark surfaces |
| Secondary text | #B0B8C4 | Metadata, time units, empty-state explanations, diagnostics labels |
| Inactive control | #7D8794 | Disabled transport glyphs, with disabled semantics |
| Track and boundary | #707B89 | Unplayed timeline track, required control outlines and visible focus boundary |
| Subtle separator | #343B46 | Decorative row and panel separation; never the sole control boundary |
| On-accent text/icon | #101216 | Play/Pause glyph on cyan surface |
| Destructive | Not used in this phase | No destructive actions or red action styling |

Accent reserved for: selected destination glyph and 4 pt marker; main Play/Pause surface; elapsed seek fill and thumb; current track marker in Files. Other buttons use neutral high-contrast text. Error/warning rows use an exclamation symbol, explicit text, and a neutral outlined surface; do not introduce a second bright decorative color.

Require at least 4.5:1 contrast for normal text and 3:1 for meaningful control graphics against their actual backgrounds. Selected state also has a marker and accessibility trait; status never depends on color alone. These are acceptance targets to measure in rendered UI, including pressed and disabled states. Apple's [accessibility guidance](https://developer.apple.com/design/human-interface-guidelines/accessibility) covers contrast and distinguishable controls.

## Layout and Navigation Contract

### Persistent shell

Order from top to bottom: safe-area page heading; scrollable page content; persistent playback warning/status when present; compact player when eligible; navigation strip; system bottom inset. Now Playing displays its status in its player content and omits the compact player. Keep active warnings reachable on every destination without covering transport or navigation.

The strip is 56 pt tall with 8 pt outer horizontal insets and zero inter-slot spacing. At a 375 pt safe content width, each of eight equal slots is `(375 - 16) / 8 = 44.875 pt` wide. Each button occupies its own full slot and the full 56 pt height; content shapes must not extend into adjacent slots. At 390 pt the slots are 46.75 pt wide. Wider layouts retain equal slots in the available safe width. Supported small-phone portrait acceptance is 375 pt; verify landscape using its actual safe width. Do not claim a narrower width passes the 44 pt requirement without a measurement.

Use 24 pt icon frames centered in each slot, a subtle selected background, and the 4 pt bottom marker inside the strip. Keep all eight controls visible with no scrolling, folding, two-row arrangement, or overflow menu. Larger text does not enlarge or collapse this icon-only strip. Supply exact full accessible labels and a selected trait. Apple recommends [44-by-44-point touch controls](https://developer.apple.com/design/tips/); the dimensions here meet that recommendation without overlapping invisible targets.

| Position | Page heading and accessible name | Icon meaning and concrete artwork direction |
|----------|----------------------------------|---------------------------------------------|
| 1 | Files | Folder; use the minimum-OS `folder` symbol |
| 2 | Tags | Tag; `tag` |
| 3 | Now Playing | Music note; `music.note` |
| 4 | Playlists | Text list; `list.bullet` |
| 5 | Favorite Songs | Bundled composite image containing a star and music note |
| 6 | Favorite Moments | Bundled composite image containing a star and hourglass |
| 7 | Equalizer | Three sliders; `slider.horizontal.3` |
| 8 | Settings | Gear; `gearshape` |

Do not invent SF Symbol names for the composite favorites. Render both meanings recognizably within the 24 pt frame and test their distinction at native scale. Icons are decorative inside their single labeled buttons. Verify all named system symbols on iOS 17; preserve meanings with bundled artwork if necessary.

First launch selects Files; later launches restore the last destination without audio. Re-selecting the current destination preserves its page state. Page headings wrap if needed and use no filename truncation rule. Bottom navigation remains available while scanning or preparing audio.

### Files

Flat vertically scrolling list; no tree controls in this phase. Page inset is 16 pt. Each file row is at least 64 pt tall with 8 pt vertical padding, filename in Body semibold, optional embedded title and artist in Label below, and a trailing current-track/status indicator. Rows expand with text. Use a stable, explicit filename ordering with a stable identity tie-breaker; display and initial queue share exactly that sequence, never filesystem enumeration order. Exact natural-sort behavior remains later work.

At ordinary text sizes, filenames wrap to two lines, then truncate in the middle so the extension remains visible. Metadata is at most two lines per available field. At accessibility text sizes, allow full wrapping in Files. Missing metadata removes its line; do not invent title or artist values. Artwork absence is a neutral music-note placeholder in Now Playing, not an error. Distinguish duplicate basenames with their relative storage path in a secondary line when necessary.

Expose the full filename to assistive technology. A row context menu provides **File Details**, showing the full selectable filename, relative location, available metadata, and any technical error; it provides no rename, move, delete, favorite, or collection actions. The detail view has a labeled Close File Details control and scrolls vertically with no horizontal text overflow.

Tap a ready row to start that file at zero and stay in Files, subject to the headphone-loss manual-Play requirement below. Newly discovered completed files appear without interrupting audio. A scan preserves the existing playable list. Not-yet-complete transfers must not appear as ready tappable rows; if exposed as pending entries they have the documented waiting status, disabled playback, and no fabricated percentage.

### Now Playing

Page heading first. Then a 64-by-64 pt cover on the leading side of filename and metadata. Filename wraps fully; metadata fields wrap independently. Keep cover small even at large text sizes. Track information may grow vertically while retaining cover beside the beginning of the text. Page content scrolls on short-height/large-text layouts.

After 24 pt, place elapsed time in Display at the leading edge and total duration in Label at the trailing edge. Show `m:ss` below one hour and `h:mm:ss` for hour-long values, without wrapping numbers; at large text sizes stack elapsed and duration with their labels. Unknown duration is `--:--`, never a fake zero or infinite slider bound.

Below the time row, use a full-width continuous seek control in a 44 pt tall interaction frame, with an 8 pt visible track and 24 pt thumb. Below 32 pt of separation, center Previous, Play/Pause, Next in that order with 24 pt gaps; outer targets are 48 pt squares and the middle target is a 64 pt square. Keep the three controls in one row. Allow the whole page to scroll rather than shrinking them.

The timeline is a basic seekbar. Do not display a fake waveform, A–B, repeat, moment, shuffle, favorite, or EQ controls. Their future responsibilities do not justify disabled controls in this phase.

### Compact player

Present only with a loaded track and only outside Now Playing, including placeholder pages. Use the Secondary surface, 16 pt outer content insets, 64 pt minimum height, filename in Body, and a distinct trailing 48 pt Play/Pause button. The remaining body is one button labeled `Open Now Playing, {filename}`. It must not wrap the Play/Pause button in a second active tap region.

Filename uses one line with middle truncation at ordinary sizes and up to two lines with an expanding container at accessibility sizes. Full text is available in its accessible name and Now Playing. Compact transport reflects the exact shared playing/paused/preparing state, including a nonblocking progress indicator while preparing. No independent compact-player timer or transport state is permitted.

### Placeholder destinations and Settings

Tags, Playlists, Favorite Songs, Favorite Moments, and Equalizer show their actual page title, the corresponding neutral symbol, and the specific unavailable-feature copy below. Do not populate demo items or offer nonfunctional creation/edit controls. Each offers **Go to Files**; the compact player still works.

Settings shows a read-only `Appearance` row with `Dark` and the explanation below, plus **View Diagnostics**. It does not present a skin picker, import/export controls, EQ preferences, or a file-logging switch before those behaviors exist. Diagnostics may also be opened from a persistent warning; successful playback never erases the recorded failure.

## Playback Interaction and State Contract

| State or event | Required visible and interaction behavior |
|----------------|-------------------------------------------|
| No track | Now Playing shows its empty state and Go to Files; no compact player; hide inactive transport rather than showing a functional-looking seekbar |
| Preparing selection | Show the target filename and Preparing track; time remains unknown until measured; disable seek and duplicate start commands; show progress without percentage; keep navigation responsive; expose Cancel Preparation to cancel pending playback intent |
| Preparation canceled | Return to the previous loaded track paused, if available, otherwise no track; stale completion must not start audio or relabel the player |
| Ready / paused | Show Play track; seeking updates the paused position without starting audio |
| Playing | Show Pause track; elapsed time follows playback state; seeking commits an absolute position and preserves intent only if no intervening pause/interruption forbids it |
| Seek dragging | Display provisional elapsed position while dragging; do not fight the thumb with timer updates; commit on release, clamp to duration, and show Seeking until confirmed |
| Seek failed | Reconcile display to the actual confirmed position, retain a visible error, and remain paused; retry through another seek or explicit Play; never show the requested position as confirmed |
| First queue entry | Previous is disabled and exposed as unavailable; it does not restart the current file |
| Previous / Next within queue | Select the adjacent file at zero; preserve whether playback was playing or paused unless an interruption requires pause; direct Previous never restarts the current file |
| Last queue entry | Next is disabled; natural completion pauses at the final duration with End of queue; no wraparound; explicit Play restarts the loaded final track from zero |
| One-item queue | Both Previous and Next are disabled; completion follows the same final-entry rule |
| Direct-selection failure | No automatic skip: pause any previous track, retain it as the loaded track if available, and show the failed selection separately in the error; with no previous loaded track retain the empty player and visible failure; allow retry from the failed Files row |
| Automatic progression failure | Record each failed file once per forward traversal, show retained skipped-file warning, continue to the next candidate only when playback is permitted; navigation remains usable |
| No playable candidate remains | Stop; show No playable tracks remain; retain failure records and loaded-track details if available; never loop over failures |
| Relaunch | Restore destination, loaded track, and confirmed position while paused; restoration progress never grants playback intent; missing restored media produces the explicit restoration error |
| Wired/Bluetooth loss | Immediately show paused UI and headphone-disconnection message; all automatic starts are forbidden until an explicit app or system Play command; reconnecting leaves message and paused state in place |
| Selection after headphone loss | File taps and Previous/Next may prepare a new selection but leave it paused; they do not clear the manual-Play requirement; seek also leaves it paused |
| Other interruption begins | Reflect paused/interrupted state and preserve position; any user Pause or Cancel during the interruption invalidates later automatic resume |
| Other interruption ends | Resume only if previously playing, iOS allows it, no later user pause exists, and no headphone-loss block exists; otherwise remain paused with the appropriate status |
| Background/locked | On return, render actual shared state, never infer playback from the old view; system previous/next/seek/play/pause obey the same boundaries and interruption rules |

Preparation and seeking must have bounded failure handling using the playback configuration's timeout; no indefinitely spinning UI after the operation fails. Late callbacks from superseded requests must not replace the current filename, time, queue, or playback intent.

VoiceOver exposes the seek control as **Playback position**, an elapsed/total spoken value, and adjustment in 10-second increments clamped to the valid range. This is a technical accessibility default, not the later fine-seeking feature. Use native adjustable-control semantics; Apple documents [accessible controls](https://developer.apple.com/documentation/swiftui/accessible-controls). Do not announce every playback tick. Announce state transitions and actionable failures once, retain reading focus, and expose transport as distinct controls.

Apple describes [audio interruptions](https://developer.apple.com/documentation/avfaudio/handling-audio-interruptions) and [audio-route changes](https://developer.apple.com/documentation/avfaudio/responding-to-audio-route-changes). The stricter manual-Play behavior here comes from the locked product decisions and takes priority over any permissive resume signal.

## Copywriting Contract

Placeholders in braces are real values, not literal application text. Preserve original technical messages verbatim even if supplied by the OS or file metadata in another language; generated labels and explanations are English.

| Element | Copy |
|---------|------|
| Primary CTA | Play track |
| Playing action | Pause track |
| Transport labels | Previous track; Next track |
| Files empty heading | No music files yet |
| Files empty body | Connect your iPhone to Windows by USB. In Apple Devices, open Files, select this app, and copy your music. Return here when the transfer finishes. |
| Files initial discovery | Checking for transferred files… |
| Files discovery with existing rows | Checking for new files… |
| Incomplete transfer | Waiting for transfer to finish |
| Discovery failure | Could not check for new files. Your existing tracks are still available. Return to the app to try again, or open Error Details. |
| Now Playing empty heading | No track selected |
| Now Playing empty body | Open Files and tap a track to start listening. |
| Empty-page action | Go to Files |
| Tags unavailable heading | Tag browsing is not available yet |
| Tags unavailable body | Listen to your music from Files in this build. |
| Playlists unavailable heading | Playlists are not available yet |
| Playlists unavailable body | Listen to your music from Files in this build. |
| Favorite Songs unavailable heading | Song favorites are not available yet |
| Favorite Songs unavailable body | Listen to your music from Files in this build. |
| Favorite Moments unavailable heading | Favorite moments are not available yet |
| Favorite Moments unavailable body | Listen to your music from Files in this build. |
| Equalizer unavailable heading | Equalizer controls are not available yet |
| Equalizer unavailable body | Listen to your music from Files in this build. |
| Settings appearance value | Dark |
| Settings appearance explanation | More skins and skin import will be available in a later build. |
| Preparation | Preparing track… |
| Preparation action | Cancel Preparation |
| Preparation canceled | Preparation canceled. |
| Seeking | Seeking… |
| Queue completion | End of queue. Press Play to replay this track. |
| Direct-selection error | Could not play “{filename}”. Playback is paused. Open Error Details, or choose another file. |
| Seek error | Could not seek in “{filename}”. Playback is paused at the last confirmed position. Try seeking again or open Error Details. |
| Automatic skip, one file | Skipped 1 unplayable file. View Diagnostics for details. |
| Automatic skip, multiple files | Skipped {count} unplayable files. View Diagnostics for details. |
| Exhausted queue | No playable tracks remain. View Diagnostics to inspect the failed files, or choose a track in Files. |
| Headphones disconnected | Headphones disconnected. Playback is paused. Press Play when you are ready to listen. |
| Other interruption | Playback interrupted. |
| Interrupted and not resumed | Playback is paused. Press Play to continue. |
| Restored position | Position restored. Press Play to continue. |
| Missing restored track | Could not restore “{filename}”. The file is unavailable. Check its transfer in Apple Devices, or choose another track in Files. |
| Error affordance | Error Details |
| Diagnostics entry | View Diagnostics |
| Diagnostics empty heading | No errors recorded |
| Diagnostics empty body | Playback and file errors will appear here when they occur. |
| Diagnostic fields | Operation; File; Original Message; Domain; Code; Underlying Causes; Recovery Action; Time |
| Missing diagnostic field | Not provided |
| Copy action | Copy Error Details |
| Copy success | Error details copied. |
| Copy failure | Could not copy error details. Select the text to copy it manually. |
| File information action | File Details |
| File-details dismissal | Close File Details |
| Diagnostics dismissal | Close Diagnostics |
| Destructive confirmation | Not applicable. This phase exposes no delete, reset, remove, or destructive overwrite actions. |

### Diagnostic presentation and recovery

Warnings persist as a compact status row until acknowledged by opening their detail; the recorded entries remain accessible through Settings. Opening details must not pause working audio or clear the headphone-loss state. In the details view, the summary comes first, followed by the full selectable original message, labeled domain/code, affected file, cause chain, and recovery action. Use a vertically scrolling layout with full wrapping, no truncation of diagnostic text, and a 44 pt minimum Copy Error Details button. Copy the full record, not just the friendly summary. Show a stable ordered list of records with singular/plural counts, newest first, and retain records across page switches and successful subsequent playback. Storage lifetime across relaunch must be stated by the diagnostics implementation; this contract does not promise permanent history or final diagnostic export.

Record preparation, direct playback, automatic skip, seek, restoration, and discovery failures with the same record format. Error reporting works when optional file logging is disabled. File writes belong outside the main actor and audio processing thread. Do not expose final export or logging settings as nonfunctional controls.

## Shared Skin Roles and Asset Contract

Load the bundled Dark appearance through the shared versioned JSON-and-image description from the first screen. Keep one source of truth for role names, colors, spacing, type, and supported control states; do not mirror separate hardcoded palettes in each view. The future importer, three bundled skins, and base-skin exporter will consume the same description and asset-loading path.

| Role family | Initial role responsibilities |
|-------------|-------------------------------|
| Surface | Page, panel, compact player, navigation, error panel; optional background/texture images |
| Text | Primary, secondary, disabled, on-accent roles |
| Navigation | Each of the eight named destinations; normal, selected, pressed, disabled icon assets and selection frame |
| Artwork | Track-cover frame and missing-cover image; actual track artwork remains track data |
| Transport | Previous, Play, Pause, Next glyph/image assets; normal, pressed, disabled surface/frame appearance |
| Timeline | Unplayed track, played track, thumb, and interaction-state appearance |
| Status | Preparing indicator and warning symbol appearance without replacing the real progress/error semantics |

Declare role/state keys centrally and permit image-backed rendering now, including the composite destination icons. Missing optional images fall back to the role's declared color/system artwork. Missing or invalid required built-in skin data must produce a technical diagnostic and an app-owned emergency readable appearance so the user can still reach diagnostics; do not crash or leave invisible controls. Preserve image aspect ratio and provide suitable scale assets. The native controls own layout, hit areas, focus, accessibility labels, and playback actions; JSON does not specify executable behavior or arbitrary control coordinates.

Do not implement waveform rendering, additional bundled skins, skin switching, ZIP import/export, or layout editors in this phase. This role table covers the first rendered controls and can be extended by later phases through the same model. It must not become a second list that diverges from the shared Swift definition.

## Accessibility, Motion, and Visual Verification

No decorative motion, autoplaying artwork, or marquee filenames. Default interaction feedback is an immediate selected/pressed change; optional short system transitions must respect Reduce Motion. Keep loading feedback understandable without animation. Use opaque surfaces so increased contrast and reduced transparency do not reveal unreadable content.

Verify at 375-by-667 pt and the target phone's logical dimensions, portrait and landscape, default and largest supported accessibility text settings. Inspect zero, one, and many Files entries; long Unicode filenames; duplicate basenames; absent and multiline metadata; multi-hour duration; unknown duration; very long cause chains; simultaneous warning plus compact player; every selected navigation destination. At large text sizes the content scrolls, filenames/headings reflow, and transport/navigation targets remain separate and visible in their designated areas. Diagnostic text must be fully reachable without horizontal scrolling.

Validate VoiceOver reading order, exact icon labels, selected traits, unavailable previous/next state, seek adjustment, compact-player body versus Play/Pause separation, and accessibility focus after dismissing details. The app-owned bottom row remains single-row and icon-only throughout; native system media UI retains the system's layout and does not inherit the skin.

Runtime acceptance must include actual iOS 17-compatible compilation, measured touch frames at 375 pt, rendered contrast, Dynamic Type, and physical-device headphone-loss/interruption/locked-screen sequences. A screenshot or source inspection does not establish that audio remained paused. The physical checks in CONTEXT remain mandatory before phase completion.


## UI Considerations

The compiled UI consideration probe raised 44 element/state checks across eight surfaces. All 44 are specified below; zero are dismissed or unresolved. Classification was reviewed against the native surfaces described above. Covered means a concrete acceptance criterion exists, not that execution has passed. Exact empty/error text remains centralized in Copywriting Contract.

| Category | Element | Status | Resolution |
|---|---|---|---|
| loading | navigation | covered (explicit) | All eight destinations remain enabled during discovery, preparation and restoration. |
| error | navigation | covered (explicit) | A discovery or playback error leaves navigation usable and retains an Error Details affordance. |
| overflow | navigation | covered (explicit) | All eight icons occupy separate slots in one fixed row at 375 pt and wider supported layouts; content scrolls above the bottom inset. |
| long-text | navigation | covered (explicit) | Page headings wrap; full accessible destination names remain available while the strip remains icon-only. |
| empty | files | covered (explicit) | Zero ready tracks show the Files empty copy from Copywriting Contract; pending transfers remain distinguishable. |
| loading | files | covered (explicit) | Initial and refresh scans use their documented copy, preserve existing playable rows and never show invented progress. |
| error | files | covered (explicit) | Discovery and row failures remain inspectable while unaffected ready rows remain available. |
| populated | files | covered (explicit) | Ready rows show filename first, available metadata beneath and a distinct current-track indicator in explicit stable order. |
| partial | files | covered (explicit) | Pending rows cannot start playback; missing metadata lines are omitted; confirmed ready rows remain playable. |
| overflow | files | covered (explicit) | Files scroll vertically above the compact player and navigation; rows expand for text. |
| zero-one-many | files | covered (explicit) | Zero uses the documented empty state, one uses an ordinary row, and many use the same scrolling list without artificial filler. |
| long-text | files | covered (explicit) | Ordinary filenames use the specified two-line middle truncation; accessibility text wraps fully and File Details exposes the full name. |
| empty | now-playing | covered (explicit) | No selected track shows the documented empty state and Go to Files with no functional-looking inactive transport. |
| loading | now-playing | covered (explicit) | Preparation shows the target filename, unknown time and Cancel Preparation; seek stays disabled until duration is known. |
| error | now-playing | covered (explicit) | Failed selection or seek retains technical details and a truthful confirmed paused position. |
| populated | now-playing | covered (explicit) | A 64 pt cover sits beside filename-led metadata, above time, seek and Previous Play/Pause Next controls. |
| overflow | now-playing | covered (explicit) | Short-height and large-text player content scrolls without shrinking or overlapping transport targets. |
| long-text | now-playing | covered (explicit) | Filename and metadata wrap fully; large time labels stack and multi-hour values keep complete digits. |
| empty | compact-player | covered (explicit) | The compact player is absent with no loaded track and absent on Now Playing. |
| loading | compact-player | covered (explicit) | Preparation reflects shared state with nonblocking progress and no duplicate start command. |
| error | compact-player | covered (explicit) | Paused or failed shared playback is reflected in the compact control and reachable warning details. |
| populated | compact-player | covered (explicit) | Loaded tracks show filename and a separate Play/Pause button; the body opens Now Playing without triggering transport. |
| overflow | compact-player | covered (explicit) | The compact player expands for accessibility text and remains above the navigation strip without covering content. |
| long-text | compact-player | covered (explicit) | Ordinary filename uses one middle-truncated line, accessibility uses up to two lines, and its full accessible name opens full player details. |
| loading | seek | covered (explicit) | Unknown duration disables seek; dragging shows a provisional value and committing shows Seeking until confirmation. |
| error | seek | covered (explicit) | A failed seek returns to the actual confirmed position, remains paused and exposes Error Details. |
| overflow | seek | covered (explicit) | The seek target remains within the full-width 44 pt interaction frame; time labels stack when horizontal space is insufficient. |
| long-text | seek | covered (explicit) | Multi-hour time values remain complete and the accessible Playback position value includes elapsed and total time. |
| empty | diagnostics | covered (explicit) | No records use the Diagnostics empty copy from Copywriting Contract. |
| loading | diagnostics | covered (explicit) | Available diagnostic records remain inspectable while history loads; any pending load is exposed as progress without disabling playback. |
| error | diagnostics | covered (explicit) | Copy failure leaves full selectable text visible and uses the documented manual-copy recovery message. |
| populated | diagnostics | covered (explicit) | Newest-first records expose operation, file, original message, domain, code, cause chain, recovery action and time. |
| partial | diagnostics | covered (explicit) | Unavailable diagnostic fields display Not provided while available original causes remain intact. |
| overflow | diagnostics | covered (explicit) | Record lists and full details scroll vertically; no original diagnostic message is truncated. |
| zero-one-many | diagnostics | covered (explicit) | Zero uses the empty state; singular and plural failure counts agree with retained records. |
| long-text | diagnostics | covered (explicit) | Long original messages and cause chains wrap fully and remain copyable without horizontal scrolling. |
| loading | file-details | covered (explicit) | Available file facts render immediately; optional metadata loading does not block dismissal or navigation. |
| error | file-details | covered (explicit) | Unavailable files or metadata retain the available filename and relative location and expose the underlying error. |
| overflow | file-details | covered (explicit) | File Details scrolls vertically with a reachable Close File Details control and selectable full content. |
| long-text | file-details | covered (explicit) | Full Unicode filename, relative location and available metadata wrap without truncation. |
| loading | placeholder-settings | covered (explicit) | Bundled placeholder content and navigation remain immediately available while shared playback or diagnostics loads. |
| error | placeholder-settings | covered (explicit) | Playback warnings remain reachable from later-feature pages and Settings; failed skin loading preserves an emergency readable appearance. |
| overflow | placeholder-settings | covered (explicit) | Placeholder and Settings content scrolls above the compact player and fixed navigation without clipped actions. |
| long-text | placeholder-settings | covered (explicit) | Headings and explanatory copy wrap at accessibility text sizes; Go to Files and View Diagnostics remain separately reachable. |

## Registry Safety

Not applicable: Tool none; Apple system frameworks and project-owned skin assets only. No shadcn registry, third-party UI block, remote font, or downloaded UI package is declared or installed by this contract. Any later external dependency needs its own source and version review under AGENTS.md.

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS
- [x] Dimension 2 Visuals: PASS
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS
- [x] Dimension 7 Inventory Provenance: PASS

**Approval:** Approved for planning on 2026-09-12. The checker passed all blocking dimensions; its copywriting suggestion was applied as contextual dismissal labels. Physical and rendered checks remain pending.
