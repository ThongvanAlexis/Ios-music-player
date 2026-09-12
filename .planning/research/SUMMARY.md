# Project Research Summary

**Project:** iOS Music Player
**Domain:** Native local music player with annotated favorite moments
**Researched:** 2026-09-12
**Confidence:** Medium overall; no iOS build or device test has been performed.

## Executive Summary

The requested app is technically plausible with Swift, native screens, persistent local files, and a shared audio pipeline. Following the user's dependency guidance, start with Apple audio APIs, Apple's multiband EQ, and Core Data. Investigate official codec sources only for measured format gaps, and evaluate a focused ZIP library for interoperable skins. These choices still need an executable experiment. Full detail and primary sources are in [STACK.md](STACK.md) and [DEPENDENCIES.md](DEPENDENCIES.md).

The defining workflow is saving a point or passage with one note and returning to it accurately. Stable media identity and a single playback timeline are foundational. Themes need to influence concrete UI components from the first screens; broad visual customization cannot be added cheaply after every control hardcodes its appearance. See [ARCHITECTURE.md](ARCHITECTURE.md).

The user has no Mac. A hosted or remote macOS environment and an installation/signing route are necessary for iOS validation. Planning can proceed, but the first implementation work must establish how a build reaches the phone. There is no basis to report a working iOS app from Windows-only checks.

## Key Findings

### Recommended Stack

- Swift and native SwiftUI screens, using UIKit where the platform API needs it.
- Proposed iOS 17 minimum to support older iPhones, subject to the product compatibility decision and testing.
- Apple audio APIs as the first playback/decoding path; investigate MP4 and Ogg gaps early before selecting any external codec revision.
- AVAudioUnitEQ within the same audio-processing path used for normal and passage playback.
- Core Data for durable references, relationships, and local persistence without an external database package.
- A versioned theme schema shared with base-skin export; ZIPFoundation 0.9.20 is a candidate exception pending review, not an adopted library.
- Cached waveform reductions rendered natively, with bounded memory and background generation.

### Expected Features

All explicitly requested features remain in the first complete release. The priority is reliable annotated points and passages, with folder browsing as the primary library view. The requested eight destinations must stay discoverable on small screens. Research proposes restore/import alongside JSON export, but the user has not yet confirmed it. [FEATURES.md](FEATURES.md) distinguishes explicit scope from recommendations.

### Architecture Approach

Use one playback session across app and system controls; a durable library with stable IDs; background import and waveform operations; concrete native screens that consume shared theme values; and a portable JSON model separate from database rows. Interface boundaries should support real replacement and testing, without forwarding-only wrappers or an abstract UI framework.

### Critical Pitfalls

The most consequential failures are an unbuildable Windows-only project, notes becoming detached after file changes, delayed seeks briefly playing the wrong audio, loops driven by UI timers, long waveforms exhausting memory, and skins or exports designed too late. [PITFALLS.md](PITFALLS.md) maps these to prevention and observable checks.

## Implications for Roadmap

These are proposed slices, not an approved phase structure:

| Suggested slice | User-visible result | Why it belongs here |
|-----------------|---------------------|---------------------|
| Build route and playable native shell | Install the app, import a test track, play and control it while locked | Expose toolchain, signing, format, and device risks before building many screens; start theme-aware controls now. |
| Durable folder library | Import a hierarchy and browse an expandable tree | Establish stable media identity and useful daily browsing. |
| Annotated moments | Save points and passages with one note each; return from a library-wide list | Validate the app's purpose early. |
| Waveform navigation and A–B repeat | Seek visually and repeat a chosen passage | Build on the trusted source timeline and range model. |
| Playlists, song favorites, and tag browsing | Organize the same library in several ways | Reuse stable track references without copying media. |
| Equalizer presets | Adjust sound and recall saved settings | Finish the already-proven processing integration. |
| Imported skins and base export | Preview/apply external styles and export a reference skin | Complete the theme support introduced in the first UI work. |
| Portable JSON data | Export the library's personal data; restore if approved | All feature models now exist and can participate in the schema. |
| Compatibility and recovery | Use the full app reliably on the declared device range | Verify lifecycle, storage failures, diagnostics, large collections, and accessibility together. |

Final grouping should follow the chosen workflow granularity. Requested capabilities must not disappear when phases are combined.

### Research Before Implementation

- Audio experiment: Apple format coverage, official decoder provenance and relevant fixes, VBR seeking, MP4 audio, EQ graph changes, and region timing.
- Build environment: hosted macOS availability, compatible Xcode/runtime, source transfer within the no-push rule, signing, and phone installation.
- UI: compact eight-destination navigation, practical fine-seeking for long mixes, and the chosen theme customization boundary.
- Portability: media identity during restore, conflict policy, and behavior for missing music.

## Confidence Assessment

| Area | Confidence | Remaining evidence |
|------|------------|--------------------|
| Native platform APIs | High | App-specific integration tests |
| Exact library release existence | High | A resolved, locked, compiled dependency set |
| External dependency adoption | Pending | Resolve reported post-release codec fixes, inspect build steps and transitive code, then select an exact source revision |
| Engine plus EQ plus MP4 | Medium | Executable format and timing experiment |
| Core user need | High | User clearly described annotated moments and confirmed point/range support |
| Complete requirements | Medium | Pending passage policy, theme freedom, workflow, and a few supporting-scope decisions |
| Older-iPhone performance | Low until measured | Device/runtime baseline and long-file measurements |
| Windows-to-iPhone delivery | Medium feasibility, unresolved access | Selected macOS host and signing/installation setup |

## Open Questions

- Saved passage end behavior: asked, awaiting answer.
- Theme restyling versus rearrangeable layouts: asked, awaiting answer.
- Workflow preferences: asked, awaiting answer.
- JSON restore/import and embedded versus custom tags: recommendations still to review.
- Exact minimum iOS version, public/private distribution, build-host access, and signing budget.
- Any external dependency must satisfy the user's official-source, reputation, maintenance, and untrusted-repository rules; the original community-heavy recommendation was revised accordingly.

## Sources

Research uses Apple documentation, versioned upstream library sources and releases, GitHub's runner documentation, and Evermusic's own feature guides. Links appear near claims in the detailed documents. The main planning constraints are supported by [Xcode requirements](https://developer.apple.com/xcode/system-requirements), [Apple audio scheduling](https://developer.apple.com/documentation/avfaudio/avaudioplayernode/schedulesegment(_:startingframe:framecount:at:completionhandler:)), [Apple directory access](https://developer.apple.com/documentation/uikit/providing-access-to-directories), [Apple background playback](https://developer.apple.com/documentation/avfoundation/configuring-your-app-for-media-playback), and [hosted macOS runners](https://docs.github.com/en/actions/concepts/runners/github-hosted-runners).

---
*Research completed: 2026-09-12. Research is ready to inform requirements; product decisions and final roadmap remain pending.*
