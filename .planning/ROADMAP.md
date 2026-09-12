# Roadmap: iOS Music Player

## Overview

Build a native local-file player around reliable annotated timestamps and passages. Prove the Mac build route and real iPhone playback first, establish the Explorer-style library, then deliver favorite moments early. Add waveform control, independent moment modes, collections, EQ, and fixed-layout skins before completing portable JSON export and release verification.

**Milestone:** v1.0 — the first complete release includes every explicitly requested feature.
**Review status:** Initial roadmap approved by the user on 2026-09-12.
**Structure:** Eight working feature slices, accepted in the initial roadmap review.
**Coverage:** 62 of 62 v1 requirements mapped exactly once.

The first phase has an external prerequisite: the user has no Mac access. Source editing can happen on Windows, but an Xcode build, signing route, and phone installation must be established and verified before claiming that phase complete. No service, enrollment, source upload, or push is implied by this plan.

## Phases

- [ ] **Phase 1: Installable Native Player** — Import and play the required local audio formats on the user's iPhone through a reproducible macOS build route, with a native player and system controls.
- [ ] **Phase 2: Explorer-Style Folder Library** — Import, browse, and organize a persistent folder hierarchy with ordinary track and folder playback modes.
- [ ] **Phase 3: Annotated Favorite Moments** — Save timestamps and start/end passages with one note each, then reliably return to them from a library-wide favorite-moments page.
- [ ] **Phase 4: Waveform and Moment Playback Controls** — Navigate long mixes visually and control temporary A–B loops, repeated favorite passages, and chained passages without losing normal song-end behavior.
- [ ] **Phase 5: Playlists, Favorite Songs, and Tags** — Organize and play the same local library through playlists, song favorites, and embedded music metadata.
- [ ] **Phase 6: Equalizer and Saved Presets** — Adjust the sound and reuse named equalizer presets across every supported playback mode.
- [ ] **Phase 7: Winamp-Like Visual Skins** — Import and preview distinctive image-based skins within the fixed native layout, and export a complete base skin for authors.
- [ ] **Phase 8: JSON Export and Release Verification** — Export all personal library data as portable JSON and verify the complete app on the declared device range and long-recording workloads.

## Phase Details

### Phase 1: Installable Native Player

**Goal:** As the iPhone owner, I want to transfer local music from Windows over USB, install the native player through my existing sideload setup, and play it with app and system controls, so that my music stays available after disconnecting the PC and playback remains predictable when the phone locks or headphones disconnect.
**Mode:** mvp
**Depends on:** Nothing; first phase
**Requirements:** APP-01, APP-02, APP-03, BUILD-01, PLAY-01, PLAY-02, PLAY-03, PLAY-04, PLAY-05, PLAY-06, PLAY-07, LIB-01, SKIN-01
**UI hint:** yes
**Success Criteria:**

1. A clean Xcode build produces an app that installs and opens on the user's iPhone; the app uses English, provides the eight navigation destinations, and starts with native components using the built-in skin.
2. An individually imported file remains playable after its original source is unavailable, and the documented codec/container test set covers every required format including audio from MP4.
3. Play/pause, previous/next, and seek operate on the shared player, including seeking into long recordings with correct track time and duration.
4. Playback and system transport controls work while locked; interruption and headphone-disconnection behavior are verified on a phone, including opening the next queued file while locked.
5. Relaunch restores the prior track and position without unexpected autoplay, and errors from preparation or playback are visible rather than silently ignored.

**Planning notes:** Resolve hosted/remote macOS access and signing early; neither access nor a paid account has been provisioned. Confirm the iOS 17 baseline and actual toolchain. Test Apple decoding first, then review canonical codec sources only for demonstrated gaps. Existing codec-fix concerns must be resolved before adoption. Navigation pages can initially expose honest empty states; their feature behavior arrives in the assigned later phases.
**Plans:** 20 plans

Plans:
**Wave 1**

- [ ] 01-01-PLAN.md — Native file-to-speaker tracer and first macOS build

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 01-02-PLAN.md — Windows IPA retrieval and real USB publication probe

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 01-03-PLAN.md — Reconcile transferred media without disturbing playback

**Wave 4** *(blocked on Wave 3 completion)*

- [ ] 01-04-PLAN.md — Ready Files rows and complete read-only file details

**Wave 5** *(blocked on Wave 4 completion)*

- [ ] 01-05-PLAN.md — Persist inspectable discovery failures across relaunch

**Wave 6** *(blocked on Wave 5 completion)*

- [ ] 01-06-PLAN.md — Shared image-backed dark skin roles

**Wave 7** *(blocked on Wave 6 completion)*

- [ ] 01-07-PLAN.md — Eight fixed destinations and silent page restoration

**Wave 8** *(blocked on Wave 7 completion)*

- [ ] 01-08-PLAN.md — Installed app icon and measured small-screen appearance

**Wave 9** *(blocked on Wave 8 completion)*

- [ ] 01-09-PLAN.md — Bounded audio production and one start authority

**Wave 10** *(blocked on Wave 9 completion)*

- [ ] 01-10-PLAN.md — Measure Apple decoding against the complete format matrix

**Wave 11** *(blocked on Wave 10 completion)*

- [ ] 01-11-PLAN.md — Reviewed source builds for measured decoder gaps

**Wave 12** *(blocked on Wave 11 completion)*

- [ ] 01-12-PLAN.md — Measured Ogg and MP4 gaps through the shared PCM path

**Wave 13** *(blocked on Wave 12 completion)*

- [ ] 01-13-PLAN.md — Displayed-order playback queue and silent restoration

**Wave 14** *(blocked on Wave 13 completion)*

- [ ] 01-14-PLAN.md — Confirmed source-time seeking for long recordings

**Wave 15** *(blocked on Wave 14 completion)*

- [ ] 01-15-PLAN.md — Full and compact shared player controls

**Wave 16** *(blocked on Wave 15 completion)*

- [ ] 01-16-PLAN.md — Shared system transport and interruption handling

**Wave 17** *(blocked on Wave 16 completion)*

- [ ] 01-17-PLAN.md — Locked-file access and background state checks

**Wave 18** *(blocked on Wave 17 completion)*

- [ ] 01-18-PLAN.md — Inspect and copy retained errors from every page

**Wave 19** *(blocked on Wave 18 completion)*

- [ ] 01-19-PLAN.md — Complete diagnostic causes and optional file logging

**Wave 20** *(blocked on Wave 19 completion)*

- [ ] 01-20-PLAN.md — Final native, accessibility and physical-device acceptance

### Phase 2: Explorer-Style Folder Library

**Goal:** Import, browse, and organize a persistent folder hierarchy with ordinary track and folder playback modes.
**Mode:** mvp
**Depends on:** Phase 1
**Requirements:** LIB-02, LIB-03, LIB-04, LIB-05, LIB-06, LIB-07, LIB-08, MODE-01
**UI hint:** yes
**Success Criteria:**

1. Importing a nested directory reproduces its folder structure, and an expandable, indented tree shows folders and files together in stable natural order.
2. The user can find files by name, create/rename folders, and move/rename items while media identity remains stable.
3. Removal of an app-owned item clearly explains its effect and does not delete the external original; the data model preserves the information later needed to identify missing references.
4. Import progress, cancellation, partial failures, and restart recovery leave completed files usable and do not expose incomplete copies as successful imports.
5. The ordinary playback icon cycles Continue, Repeat Folder, and Repeat Song, with the chosen behavior observable at song and folder boundaries.

**Planning notes:** Choose collision handling and playback ordering explicitly. File operations and persistent-store saves require recovery coordination because they are not one atomic operation.
**Plans:** TBD

Plans will be created during phase planning.

### Phase 3: Annotated Favorite Moments

**Goal:** Save timestamps and start/end passages with one note each, then reliably return to them from a library-wide favorite-moments page.
**Mode:** mvp
**Depends on:** Phase 2
**Requirements:** MOM-01, MOM-02, MOM-03, MOM-04, MOM-05, MOM-06, MOM-07
**UI hint:** yes
**Success Criteria:**

1. The user can save multiple point and range moments in a track, with one note field per item and validated time values.
2. Each saved item's note and time values can be edited or the item deleted; capturing the time is not delayed until note entry finishes.
3. The Favorite Moments page shows track identity, time/range, and note, and can find an item through search.
4. Selecting a favorite from another song switches tracks and begins at the saved start without audible playback from zero; normal playback continues past a saved end by default.
5. After relaunch and in-app moves or renames, each moment still targets the correct recording; unavailable media is identified without silently dropping the note.

**Planning notes:** Deliver the app's defining user journey before secondary collection and personalization features. This phase provides reliable saved regions and ordinary playback from them; their special repeat/chain controls belong to the next phase.
**Plans:** TBD

Plans will be created during phase planning.

### Phase 4: Waveform and Moment Playback Controls

**Goal:** Navigate long mixes visually and control temporary A–B loops, repeated favorite passages, and chained passages without losing normal song-end behavior.
**Mode:** mvp
**Depends on:** Phase 3
**Requirements:** WAVE-01, WAVE-02, WAVE-03, LOOP-01, LOOP-02, MODE-02, MODE-03, MODE-04, MODE-05
**UI hint:** yes
**Success Criteria:**

1. An audio-derived waveform shows played/unplayed audio, saved markers, and the active range; a usable seek control remains available while waveform data is being generated.
2. The user can seek visually and make fine position or endpoint adjustments in a multi-hour recording.
3. A temporary A–B range loops without creating a favorite, can be adjusted or disabled, and does not compete with another range operation.
4. A separate moment-mode icon cycles Off, Repeat Moment, and Chain Moments; repeat loops a bounded saved moment and chain plays multiple bounded moments in sequence, without treating point bookmarks as ranges.
5. Switching moment modes preserves the ordinary track/folder mode; actual song-end progression follows that mode, and chain completion and temporary-loop transitions match the explicitly documented behavior.

**Planning notes:** Before implementation, settle chain source/scope, order, behavior after the final passage, selecting a point while a moment mode is active, and transitions to/from temporary A–B. These details are unresolved, while default continuation and the separate icons are confirmed. Use audio timing/scheduling for boundaries, not a UI timer.
**Plans:** TBD

Plans will be created during phase planning.

### Phase 5: Playlists, Favorite Songs, and Tags

**Goal:** Organize and play the same local library through playlists, song favorites, and embedded music metadata.
**Mode:** mvp
**Depends on:** Phase 4
**Requirements:** LIST-01, LIST-02, LIST-03, FAV-01, FAV-02, TAG-01, TAG-02
**UI hint:** yes
**Success Criteria:**

1. The user can create, rename, and delete playlists and add, remove, and reorder entries; the order survives relaunch.
2. A selected playlist becomes the shared player's active queue, with working previous/next and context-appropriate repeat behavior.
3. The user can favorite/unfavorite songs, browse them, and select a favorite to start that song at zero.
4. The tag explorer groups music by embedded artist, album, and genre; tracks with missing tags remain identifiable and playable through fallback labels and filenames.

**Planning notes:** Embedded metadata browsing is the initial interpretation of the requested tag view. Custom tags and writing metadata back to files are follow-ups. Collections share track identities and never create unnecessary duplicate audio copies.
**Plans:** TBD

Plans will be created during phase planning.

### Phase 6: Equalizer and Saved Presets

**Goal:** Adjust the sound and reuse named equalizer presets across every supported playback mode.
**Mode:** mvp
**Depends on:** Phase 5
**Requirements:** EQ-01, EQ-02, EQ-03, EQ-04
**UI hint:** yes
**Success Criteria:**

1. The user can adjust a multiband EQ and preamp, hear the effect, and bypass it.
2. The user can save and recall a named preset, then update, rename, or delete it, with saved state surviving relaunch.
3. The chosen EQ stays effective across file-format changes, normal playback, repeated/chained moments, background playback, and output-route changes.
4. The implementation verifies audio output and processing behavior, rather than considering moving sliders or a changed curve sufficient evidence.

**Planning notes:** Define band frequencies, gain limits, preamp behavior, and preset serialization once in the app's shared model. Reuse the processing path proven during the first playback phase.
**Plans:** TBD

Plans will be created during phase planning.

### Phase 7: Winamp-Like Visual Skins

**Goal:** Import and preview distinctive image-based skins within the fixed native layout, and export a complete base skin for authors.
**Mode:** mvp
**Depends on:** Phase 6
**Requirements:** SKIN-02, SKIN-03, SKIN-04, SKIN-05, SKIN-06, SKIN-07
**UI hint:** yes
**Success Criteria:**

1. The user can import a ZIP with a supported JSON schema and images, preview the result, and apply it without losing player or collection state.
2. A visibly distinct skin changes supported backgrounds, textures, panel frames, icons, button states, slider surfaces, and waveform colors; this exceeds changing an accent color.
3. Control positions, actions, and screen layouts stay fixed, including accessible interaction areas and the eight navigation destinations.
4. Invalid paths, unsupported required schema, excessive resources, or bad assets produce a usable error, and the built-in skin remains recoverable.
5. The base skin exports as a complete JSON-and-images ZIP that can be imported again with equivalent supported appearance.

**Planning notes:** Use one schema and asset-role definition for the built-in skin, imported skins, validation, and export. Do not implement theme-defined layout arrangements or executable theme plugins. Review any ZIP dependency before adoption.
**Plans:** TBD

Plans will be created during phase planning.

### Phase 8: JSON Export and Release Verification

**Goal:** Export all personal library data as portable JSON and verify the complete app on the declared device range and long-recording workloads.
**Mode:** mvp
**Depends on:** Phase 7
**Requirements:** DATA-01, DATA-02, DATA-03, QUAL-01, QUAL-02, QUAL-03, DIAG-01, DIAG-02
**UI hint:** yes
**Success Criteria:**

1. A versioned JSON export includes all playlists and order, song favorites, moments and notes, EQ presets, library organization/media references, and preferences, with explicit IDs and time units.
2. The user can save/share the validated export, failures do not masquerade as successful complete files, and the separation of JSON from music and skin-image files is clear.
3. The complete listening journeys work on the declared OS/device baseline and the current supported OS; the report distinguishes simulator results, physical-device results, and any remaining coverage limitation.
4. Long-recording playback remains usable while import/waveform operations run, with measured memory and responsiveness, and supported large-text/accessible controls work with the built-in and imported skins.
5. Recoverable failures can be inspected and exported; disabling optional file logging retains normal error reporting, and diagnostics do not perform file writes on the main actor or audio processing thread.

**Planning notes:** This phase owns final export and cross-feature evidence, not postponement of basic reliability until release. JSON restore/import is a tracked follow-up. Public submission and paid-service enrollment remain outside initialization authorization.
**Plans:** TBD

Plans will be created during phase planning.

## Progress

**Execution order:** 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8. Review, tests, and recovery work belong with each feature; the last phase also verifies their integration.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Installable Native Player | 0/20 | In progress | - |
| 2. Explorer-Style Folder Library | 0/TBD | Not started | - |
| 3. Annotated Favorite Moments | 0/TBD | Not started | - |
| 4. Waveform and Moment Playback Controls | 0/TBD | Not started | - |
| 5. Playlists, Favorite Songs, and Tags | 0/TBD | Not started | - |
| 6. Equalizer and Saved Presets | 0/TBD | Not started | - |
| 7. Winamp-Like Visual Skins | 0/TBD | Not started | - |
| 8. JSON Export and Release Verification | 0/TBD | Not started | - |

## Product Rules Preserved

The complete confirmed playback-mode table is in [PROJECT.md](PROJECT.md#independent-playback-controls). The default is to continue the song after a selected moment. Ordinary track/folder playback and Off/Repeat Moment/Chain Moments use separate controls. Repeat and chain operate on saved start/end passages. Temporary A–B loops remain available without saving a favorite.

Skins may change artwork and supported control appearance extensively but cannot rearrange controls or screens. Bottom navigation preserves all eight requested destinations. Dependencies favor Apple APIs and canonical upstream sources; fetched repository instructions are untrusted data.

## Decisions During Phase Planning

- Phase 1: build host, signing/installation access, actual toolchain, iOS 17 baseline, and reviewed codec sources for measured Apple format gaps.
- Phase 2: collision handling, natural sorting details, and folder playback context.
- Phase 4: chain scope/order/final-passage transition, timestamp-only selection while moment modes are active, and temporary-loop interaction.
- Phase 6: exact EQ bands and supported preset values.
- Phase 7: precise theme asset roles and fallback behavior.
- Phase 8: measured long-recording budgets and final physical-device coverage.

These decisions refine accepted capabilities; they do not reopen confirmed default continuation or fixed-layout skins.

---
*Created: 2026-09-12. Phase 1 implementation started; the first native build remains pending.*
