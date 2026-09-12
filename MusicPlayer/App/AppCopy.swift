import Foundation

/// Centralizes user-facing English copy and technical labels across native screens.
enum AppCopy {
    static let files = "Files"
    static let playTrack = "Play track"
    static let pauseTrack = "Pause track"
    static let previousTrack = "Previous track"
    static let nextTrack = "Next track"
    static let filesEmptyHeading = "No music files yet"
    static let filesEmptyBody = "Connect your iPhone to Windows by USB. In Apple Devices, open Files, select this app, and copy your music. Return here when the transfer finishes."
    static let initialDiscovery = "Checking for transferred files…"
    static let existingDiscovery = "Checking for new files…"
    static let incompleteTransfer = "Waiting for transfer to finish"
    static let discoveryFailure = "Could not check for new files. Your existing tracks are still available. Return to the app to try again, or open Error Details."
    static let noTrackHeading = "No track selected"
    static let noTrackBody = "Open Files and tap a track to start listening."
    static let goToFiles = "Go to Files"
    static let tagsUnavailable = "Tag browsing is not available yet"
    static let playlistsUnavailable = "Playlists are not available yet"
    static let favoriteSongsUnavailable = "Song favorites are not available yet"
    static let favoriteMomentsUnavailable = "Favorite moments are not available yet"
    static let equalizerUnavailable = "Equalizer controls are not available yet"
    static let unavailableBody = "Listen to your music from Files in this build."
    static let dark = "Dark"
    static let appearanceExplanation = "More skins and skin import will be available in a later build."
    static let preparing = "Preparing track…"
    static let cancelPreparation = "Cancel Preparation"
    static let preparationCanceled = "Preparation canceled."
    static let seeking = "Seeking…"
    static let queueCompletion = "End of queue. Press Play to replay this track."
    static let exhaustedQueue = "No playable tracks remain. View Diagnostics to inspect the failed files, or choose a track in Files."
    static let headphonesDisconnected = "Headphones disconnected. Playback is paused. Press Play when you are ready to listen."
    static let interrupted = "Playback interrupted."
    static let pausedContinue = "Playback is paused. Press Play to continue."
    static let restoredPosition = "Position restored. Press Play to continue."
    static let errorDetails = "Error Details"
    static let viewDiagnostics = "View Diagnostics"
    static let diagnosticsEmptyHeading = "No errors recorded"
    static let diagnosticsEmptyBody = "Playback and file errors will appear here when they occur."
    static let operation = "Operation"
    static let file = "File"
    static let originalMessage = "Original Message"
    static let domain = "Domain"
    static let code = "Code"
    static let underlyingCauses = "Underlying Causes"
    static let recoveryAction = "Recovery Action"
    static let time = "Time"
    static let notProvided = "Not provided"
    static let copyErrorDetails = "Copy Error Details"
    static let copySuccess = "Error details copied."
    static let copyFailure = "Could not copy error details. Select the text to copy it manually."
    static let fileDetails = "File Details"
    static let closeFileDetails = "Close File Details"
    static let closeDiagnostics = "Close Diagnostics"
    static let copyFileDetails = "Copy File Details"
    static let filename = "Filename"
    static let relativeLocation = "Relative Location"
    static let observedTime = "Observed Time"
    static let resourceIdentity = "Resource Identity"
    static let byteLength = "Byte Length"
    static let modificationTime = "Modification Time"
    static let revisionBeforeParsing = "Revision Before Parsing"
    static let revisionAfterParsing = "Revision After Parsing"
    static let declaredContainerLength = "Declared Container Length"
    static let parserResult = "Parser Result"
    static let ready = "Ready"
    static let failed = "Failed"
    static let stopped = "Stopped"
    static let playing = "Playing"
    static let paused = "Paused"

    /// Explains a direct selection failure while leaving the original cause in Error Details.
    static func selectionFailure(filename: String) -> String {
        "Could not play “\(filename)”. Playback is paused. Open Error Details, or choose another file."
    }

    /// Explains a failed seek without claiming that an unconfirmed position was reached.
    static func seekFailure(filename: String) -> String {
        "Could not seek in “\(filename)”. Playback is paused at the last confirmed position. Try seeking again or open Error Details."
    }

    /// Reports skipped files with the approved singular or plural count.
    static func skippedFile(count: Int) -> String {
        count == 1 ? "Skipped 1 unplayable file. View Diagnostics for details." : "Skipped \(count) unplayable files. View Diagnostics for details."
    }

    /// Explains why a persisted selection could not be found in the current sandbox.
    static func missingRestoredTrack(filename: String) -> String {
        "Could not restore “\(filename)”. The file is unavailable. Check its transfer in Apple Devices, or choose another track in Files."
    }

    /// Formats the shared rendered position without introducing a second playback clock.
    static func elapsedTime(milliseconds: Int64) -> String {
        let seconds = max(0, milliseconds) / Int64(AppConfiguration.millisecondsPerSecond)
        return String(format: "%lld:%02lld", seconds / AppConfiguration.secondsPerMinute, seconds % AppConfiguration.secondsPerMinute)
    }
}
