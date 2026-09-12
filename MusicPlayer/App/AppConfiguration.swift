import Foundation

/// Owns shared runtime limits so storage, playback, and presentation agree on bounded work.
enum AppConfiguration {
    static let bufferFrameCapacity: UInt32 = 4_096
    static let maximumScheduledBufferCount = 4
    static let preparationTimeoutSeconds: TimeInterval = 15
    static let seekTimeoutSeconds: TimeInterval = 10
    static let scanQuietIntervalSeconds: TimeInterval = 2
    static let snapshotIntervalSeconds: TimeInterval = 0.1
    static let maximumDiagnosticCount = 50
    static let maximumCauseCount = 8
    static let maximumDiagnosticCharacterCount = 65_536
    static let millisecondsPerSecond: Double = 1_000
    static let secondsPerMinute: Int64 = 60
    static let schemaVersion = 1
    static let errorDomain = "MusicPlayer"
    static let minimumControlSize: CGFloat = 44
    static let pageSpacing: CGFloat = 16
    static let compactSpacing: CGFloat = 8
    static let supportDirectoryName = "MusicPlayer"
}

/// Preserves original OS causes as selectable text before the full diagnostics browser exists.
struct TechnicalFailure: Identifiable, Sendable {
    let id: UUID
    let text: String

    /// Captures the original message, code, domain, and cause chain without replacing OS detail.
    init(operation: String, file: String? = nil, error: Error) {
        id = UUID()
        var lines = ["\(AppCopy.operation): \(operation)", "\(AppCopy.file): \(file ?? AppCopy.notProvided)", "\(AppCopy.time): \(Date().ISO8601Format())"]
        var cause: NSError? = error as NSError
        var causeCount = 0
        while let current = cause, causeCount < AppConfiguration.maximumCauseCount {
            lines.append("\(AppCopy.domain): \(current.domain)")
            lines.append("\(AppCopy.code): \(current.code)")
            lines.append("\(AppCopy.originalMessage): \(current.localizedDescription)")
            if let reason = current.localizedFailureReason { lines.append(reason) }
            if let recovery = current.localizedRecoverySuggestion { lines.append("\(AppCopy.recoveryAction): \(recovery)") }
            cause = current.userInfo[NSUnderlyingErrorKey] as? NSError
            causeCount += 1
            if cause != nil { lines.append(AppCopy.underlyingCauses) }
        }
        text = String(lines.joined(separator: "\n").prefix(AppConfiguration.maximumDiagnosticCharacterCount))
    }
}
