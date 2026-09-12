# Feature Research

**Domain:** Folder-based native audio player with annotated favorite moments
**Researched:** 2026-09-12
**Confidence:** High for stated user needs; medium for inferred supporting behaviors.

## Feature Landscape

The user's own requirements define scope. Every originally requested feature belongs in the first complete release; smaller implementation phases must not silently defer those features to a later release.

| Feature group | User value | Complexity | Planning implication |
|---------------|------------|------------|----------------------|
| App-owned library and folder tree | Keep a familiar, durable collection | High | Import whole hierarchies, preserve identity, handle partial failures, and keep large trees responsive. |
| Playback and format coverage | Listen to existing files without manual conversion | High | Verify an explicit codec/container matrix before expanding the UI. |
| Background and lock-screen playback | Keep listening while the phone is locked | High | Establish audio session, remote commands, and phone tests early. |
| Favorite moments and passages | Remember the part and the reason | High | One note field per saved item, multiple items per song, accurate seeking, persistent references. |
| Waveform and A–B repeat | Locate and revisit musical details | High | Long-file peak caching, fine navigation, and audio-clock-based repeat behavior. |
| Playlists and favorite songs | Organize daily listening | Medium | Ordered entries, stable track references, editing, and clear play-from-zero behavior for favorites. |
| Tag explorer | Find music through metadata | Medium | Define whether tags mean embedded metadata, user tags, or both. |
| Equalizer and saved presets | Reuse a preferred sound | Medium to high | Share the same processing pipeline across file formats and background playback. |
| Imported skins and base-skin export | Make the player look personal | High | Theme-aware native components must precede the theme importer. Layout freedom is still pending. |
| JSON export | Preserve personal organization and notes | Medium to high | Versioned schema, stable media references, and explicit separation from audio files. Restore is proposed, not yet confirmed. |

These complexity estimates are engineering judgments for this app, not market statistics.

## Existing Product Evidence

Evermusic documents audio bookmarks, an equalizer, a queue, and playlist actions; its library guide exposes favorites and bookmarks. This confirms that some related capabilities already exist in other players. It does not establish that another app offers this user's desired combination or experience. Position the product around how well it supports annotated timestamps and passages within an Explorer-style collection, without claiming bookmarks are an industry first. [Evermusic player guide](https://everappz.com/docs/guide/evermusic/evermusic-guide-player/), [library guide](https://www.everappz.com/docs/guide/evermusic/evermusic-guide-music-library/)

## Core User Journeys

### Capture a moment while listening

The user hears something memorable, taps the moment action, and saves the playback position without losing it while typing. A point has a timestamp and one note. A passage has start and end positions and one note. Editing the note must not move the saved position accidentally. The same song can contain many saved items.

### Return to a favorite

From Favorite Moments, the user selects an item. The player resolves its track, changes the current song, and starts at the saved position. It must not briefly start at zero while waiting for a later seek. For a passage, behavior at its end is pending user input. A favorite song is a separate feature and explicitly starts at zero.

### Import and browse a mix collection

The user selects a directory or files through the system picker. Imported audio is copied into persistent app storage. The app preserves relative hierarchy and displays expandable folders with files beneath them. It reports skipped or failed files and does not announce an incomplete copy as successful. Apple supports directory selection and scoped recursive access; the app owns the copy and recovery behavior. [Apple directory-import documentation](https://developer.apple.com/documentation/uikit/providing-access-to-directories)

### Apply a skin

The user imports a ZIP, previews it, and applies it without losing their player state. Missing optional visual fields can fall back to the base theme; an invalid required schema must fail with a usable explanation. The built-in base skin must export through the same documented format used by imports. Whether skins can rearrange controls is pending.

## Supporting Behaviors to Propose During Requirements Review

- Resume the last playing item and position after relaunch, without starting audible playback unexpectedly.
- Keep a playback queue with previous/next, shuffle, and track/queue repeat; distinguish these from passage repeat.
- Search filenames and embedded metadata, and search notes in Favorite Moments.
- Create, rename, move, and delete library entries with clear consequences for references.
- Include JSON import/restore so an export serves as a practical backup; preview conflicts and unresolved audio references.
- Make missing media recoverable instead of discarding its notes or silently assigning them to a same-named file.
- Let playback begin before waveform analysis completes, showing an honest progress state and a usable ordinary seek control.
- Support large text, VoiceOver labels, and fine time adjustment for long mixes.

These are recommendations that support the requested features. They have not all been explicitly accepted by the user.

## Feature Dependencies

| Capability | Depends on |
|------------|------------|
| Accurate saved moments | A single playback timeline, persistent track identity, and reliable seek behavior |
| Saved passages | Timestamp capture plus endpoint validation and agreed end behavior |
| Waveform markers | Cached waveform data and the same timeline used for playback |
| A–B looping | Region playback or equivalent audio scheduling, not just a UI timer |
| Stable playlists and favorites | Persistent media identities independent of path and filename |
| JSON backup | Stable record identifiers, a media-reference strategy, and versioned models |
| Theme import | Concrete controls already using theme values and assets |
| Locked-screen next track | Background session, readable next-file storage, and queue state |

## Release Boundaries

The first executable slice should prove importing and playing a local track, keeping playback alive while locked, and installing on the user's phone through a viable build route. Annotated moments should follow as soon as track identity and seeking are reliable. This ordering validates the purpose of the app before completing secondary screens.

Streaming subscriptions, accounts, social sharing, recommendations, lyrics downloads, CarPlay, a standalone watch app, and cloud sync were not requested. Treat them as possible future work rather than quietly adding them to the current release. DRM-protected subscription media should not be implied by support for ordinary local music files.

## Decisions Still Needed

- Saved passage end behavior.
- Theme layout freedom.
- Embedded versus custom tags.
- JSON restore/import scope.
- Public versus personal release and the Mac build/signing route.

The base app name and detailed icon artwork can wait until UI planning.
