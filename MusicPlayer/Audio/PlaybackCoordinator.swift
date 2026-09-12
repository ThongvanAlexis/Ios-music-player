import AVFAudio
import Foundation
import os

/// Describes the single transport's actual state independently of a particular screen.
enum PlaybackState: String, Sendable {
    case stopped, preparing, playing, paused, failed
}

/// Shares confirmed rendered time and start inhibition without transferring audio framework objects.
struct PlaybackSnapshot: Sendable {
    let trackID: UUID?
    let filename: String?
    let state: PlaybackState
    let positionMilliseconds: Int64
    let durationMilliseconds: Int64
    let generation: UInt64
    let requiresExplicitPlay: Bool
    let failure: TechnicalFailure?

    static let empty = PlaybackSnapshot(trackID: nil, filename: nil, state: .stopped, positionMilliseconds: 0,
        durationMilliseconds: 0, generation: 0, requiresExplicitPlay: false, failure: nil)
}

/// Selects hardware output for the app or the same engine graph's offline sink for native tests.
enum PlaybackOutputMode: Sendable {
    case device, offline
}

/// Reports actual engine output without sharing an audio buffer across isolation.
struct RenderedAudioSnapshot: Sendable {
    let peakMagnitude: Float
    let frameCount: UInt32
}

/// Owns the only player node, bounded PCM pool, and authority to start sound.
actor PlaybackCoordinator {
    private let store: LibraryStore
    private let outputMode: PlaybackOutputMode
    private let engine = AVAudioEngine()
    private let player = AVAudioPlayerNode()
    // A notification must inhibit the synchronous start site before actor work can be delayed.
    private nonisolated let startInhibition = OSAllocatedUnfairLock(initialState: false)
    private var notificationTokens: [NSObjectProtocol] = []
    private var file: AVAudioFile?
    private var fileRevision: FileRevision?
    private var buffers: [AVAudioPCMBuffer] = []
    private var trackID: UUID?
    private var filename: String?
    private var state = PlaybackState.stopped
    private var generation: UInt64 = 0
    private var durationMilliseconds: Int64 = 0
    private var confirmedPositionMilliseconds: Int64 = 0
    private var failure: TechnicalFailure?
    private var reachedEnd = false

    /// Injects persistence and output mode while keeping all framework objects owned by this actor.
    init(store: LibraryStore, outputMode: PlaybackOutputMode = .device) {
        self.store = store
        self.outputMode = outputMode
    }

    /// Installs lifetime app observers; tests use explicit loss injection without global observers.
    func observeAudioSession() {
        guard notificationTokens.isEmpty, outputMode == .device else { return }
        let routeToken = NotificationCenter.default.addObserver(forName: AVAudioSession.routeChangeNotification,
            object: nil, queue: nil) { [weak self] notification in
            guard let rawReason = notification.userInfo?[AVAudioSessionRouteChangeReasonKey] as? UInt,
                  AVAudioSession.RouteChangeReason(rawValue: rawReason) == .oldDeviceUnavailable else { return }
            self?.inhibitForRouteLoss()
            Task { await self?.finishRouteLoss() }
        }
        let interruptionToken = NotificationCenter.default.addObserver(forName: AVAudioSession.interruptionNotification,
            object: nil, queue: nil) { [weak self] notification in
            guard let rawType = notification.userInfo?[AVAudioSessionInterruptionTypeKey] as? UInt,
                  AVAudioSession.InterruptionType(rawValue: rawType) == .began else { return }
            // This first audio path resumes any interruption only through an explicit command.
            self?.inhibitForRouteLoss()
            Task { await self?.finishRouteLoss() }
        }
        notificationTokens = [routeToken, interruptionToken]
    }

    /// Selects a persisted track from zero; an existing route-loss latch remains in force.
    func select(trackID: UUID) async {
        generation &+= 1
        let requestGeneration = generation
        stopGraph()
        self.trackID = trackID
        filename = nil
        confirmedPositionMilliseconds = 0
        durationMilliseconds = 0
        failure = nil
        state = .preparing
        let deadline = Date().addingTimeInterval(AppConfiguration.preparationTimeoutSeconds)
        do {
            let selection = try await store.playbackFile(id: trackID)
            guard generation == requestGeneration else { return }
            guard Date() < deadline else { throw LibraryStore.failure("Track preparation timed out.") }
            filename = selection.track.filename
            let revisionBefore = try LibraryStore.revision(filename: selection.filename)
            let selectedFile = try AVAudioFile(forReading: selection.filename)
            guard revisionBefore == selection.track.observation.revisionAfter,
                  try LibraryStore.revision(filename: selection.filename) == revisionBefore else {
                throw LibraryStore.failure("The selected file changed while opening audio.")
            }
            file = selectedFile
            fileRevision = revisionBefore
            durationMilliseconds = selection.track.durationMilliseconds ?? 0
            try prepareGraph(format: selectedFile.processingFormat)
            for bufferIndex in buffers.indices { try schedule(bufferIndex: bufferIndex, requestGeneration: requestGeneration) }
            state = .paused
            try startIfAuthorized()
        } catch {
            guard generation == requestGeneration else { return }
            recordFailure(error, operation: "Prepare playback")
        }
    }

    /// Explicit Play is the only command that clears headphone-loss inhibition.
    func play() async {
        startInhibition.withLock { $0 = false }
        // Read failures invalidate refill callbacks; retry must open and schedule a fresh graph.
        if (state == .failed || reachedEnd || file == nil), let trackID {
            await select(trackID: trackID)
            return
        }
        guard file != nil else { return }
        do { try startIfAuthorized() } catch { recordFailure(error, operation: "Start playback") }
    }

    /// Pauses sound without discarding the confirmed position or clearing route-loss state.
    func pause() {
        if state == .preparing {
            generation &+= 1
            stopGraph()
        }
        updatePosition()
        player.pause()
        if state != .stopped { state = .paused }
    }

    /// Sets the start latch synchronously even if preparation is awaiting a background operation.
    nonisolated func inhibitForRouteLoss() {
        startInhibition.withLock { $0 = true }
    }

    /// Applies the already-latched loss to actor state; reconnect callbacks never invoke Play.
    func finishRouteLoss() {
        guard startInhibition.withLock({ $0 }) else { return }
        pause()
    }

    /// Samples the player-rendered clock, keeping view refreshes separate from audio progression.
    func snapshot() -> PlaybackSnapshot {
        updatePosition()
        return PlaybackSnapshot(trackID: trackID, filename: filename, state: state,
            positionMilliseconds: confirmedPositionMilliseconds, durationMilliseconds: durationMilliseconds,
            generation: generation, requiresExplicitPlay: startInhibition.withLock { $0 }, failure: failure)
    }

    /// Renders the same scheduled player graph into a real offline sink for the native acceptance test.
    func renderOffline(frameCount: UInt32) throws -> RenderedAudioSnapshot {
        guard outputMode == .offline, state == .playing,
              frameCount <= AppConfiguration.bufferFrameCapacity,
              let buffer = AVAudioPCMBuffer(pcmFormat: engine.manualRenderingFormat, frameCapacity: frameCount) else {
            throw LibraryStore.failure("Offline output requires a prepared, playing graph and bounded frame count.")
        }
        let status = try engine.renderOffline(frameCount, to: buffer)
        guard status == .success else { throw LibraryStore.failure("The audio engine did not render the requested PCM frames: \(status.rawValue).") }
        guard let channels = buffer.floatChannelData else { throw LibraryStore.failure("The engine output is not floating-point PCM.") }
        var peak: Float = 0
        for channelIndex in 0..<Int(buffer.format.channelCount) {
            for frameIndex in 0..<Int(buffer.frameLength) { peak = max(peak, abs(channels[channelIndex][frameIndex])) }
        }
        updatePosition()
        return RenderedAudioSnapshot(peakMagnitude: peak, frameCount: buffer.frameLength)
    }

    /// Configures one graph and allocates the fixed pool before any file data reaches the player.
    private func prepareGraph(format: AVAudioFormat) throws {
        guard format.channelCount > 0, format.sampleRate > 0 else { throw LibraryStore.failure("The decoded PCM format is invalid.") }
        engine.attach(player)
        engine.connect(player, to: engine.mainMixerNode, format: format)
        if outputMode == .offline {
            try engine.enableManualRenderingMode(.offline, format: format, maximumFrameCount: AppConfiguration.bufferFrameCapacity)
        } else {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.playback, mode: .default)
        }
        buffers = try (0..<AppConfiguration.maximumScheduledBufferCount).map { _ in
            guard let buffer = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: AppConfiguration.bufferFrameCapacity) else {
                throw LibraryStore.failure("The bounded audio buffer pool could not be allocated.")
            }
            return buffer
        }
        reachedEnd = false
        engine.prepare()
    }

    /// Reuses a buffer only after the player consumed its previous contents, with stale-work rejection.
    private func schedule(bufferIndex: Int, requestGeneration: UInt64) throws {
        guard generation == requestGeneration, let file, file.framePosition < file.length else { return }
        guard try LibraryStore.revision(filename: file.url) == fileRevision else {
            throw LibraryStore.failure("The playing file changed during playback. Playback is paused until it is checked again.")
        }
        let buffer = buffers[bufferIndex]
        try file.read(into: buffer, frameCount: AppConfiguration.bufferFrameCapacity)
        guard buffer.frameLength > 0 else { throw LibraryStore.failure("Audio decoding returned no frames before the expected end.") }
        player.scheduleBuffer(buffer, completionCallbackType: .dataConsumed) { [weak self] _ in
            Task { await self?.refill(bufferIndex: bufferIndex, requestGeneration: requestGeneration) }
        }
    }

    /// Moves refill work off the render callback and contains file read failures in the shared snapshot.
    private func refill(bufferIndex: Int, requestGeneration: UInt64) {
        guard generation == requestGeneration else { return }
        do { try schedule(bufferIndex: bufferIndex, requestGeneration: requestGeneration) }
        catch { recordFailure(error, operation: "Read audio frames") }
    }

    /// Serializes the only audible start with synchronous notification inhibition.
    private func startIfAuthorized() throws {
        guard !startInhibition.withLock({ $0 }), file != nil else { state = .paused; return }
        // Session activation can synchronously deliver a route notification; never hold its latch here.
        if outputMode == .device { try AVAudioSession.sharedInstance().setActive(true) }
        if !engine.isRunning { try engine.start() }
        // This synchronous closure stays on the actor; audio objects must not enter a Sendable closure.
        startInhibition.withLockUnchecked { inhibited in
            guard !inhibited, file != nil else { state = .paused; return }
            player.play()
            state = .playing
        }
    }

    /// Uses engine output timing; view refreshes cannot manufacture progress for a silent player.
    private func updatePosition() {
        guard state == .playing, let file else { return }
        let sampleTime: AVAudioFramePosition
        if outputMode == .offline {
            sampleTime = engine.manualRenderingSampleTime
        } else {
            guard let renderTime = player.lastRenderTime, let playerTime = player.playerTime(forNodeTime: renderTime) else { return }
            sampleTime = playerTime.sampleTime
        }
        let elapsed = Int64(Double(max(0, sampleTime)) / file.processingFormat.sampleRate * AppConfiguration.millisecondsPerSecond)
        confirmedPositionMilliseconds = min(durationMilliseconds, elapsed)
        if elapsed >= durationMilliseconds {
            player.pause()
            state = .stopped
            reachedEnd = true
        }
    }

    private func stopGraph() {
        player.stop()
        engine.stop()
        if engine.isInManualRenderingMode { engine.disableManualRenderingMode() }
        if engine.attachedNodes.contains(player) { engine.detach(player) }
        buffers.removeAll()
        file = nil
        fileRevision = nil
    }

    private func recordFailure(_ error: Error, operation: String) {
        generation &+= 1
        player.pause()
        state = .failed
        failure = TechnicalFailure(operation: operation, file: filename, error: error)
    }
}
