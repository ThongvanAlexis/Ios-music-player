import AVFAudio
import XCTest
@testable import MusicPlayer

/// Exercises disk persistence, transfer evidence, and PCM rendered by the real playback graph.
final class NativeTracerTests: XCTestCase {
    /// A stored identity survives reopening SQLite and points to the original Documents file.
    func testTrackIdentitySurvivesStoreReopen() async throws {
        let location = try makeLocation()
        defer { try? FileManager.default.removeItem(at: location.rootDir) }
        try makeWave(at: location.documentsDir.appendingPathComponent("roundtrip.wav"))
        let firstStore = try await LibraryStore.open(documentsDir: location.documentsDir, supportDir: location.supportDir)
        let firstTracks = try await firstStore.scan()
        let firstTrack = try XCTUnwrap(firstTracks.first)
        XCTAssertEqual(firstTrack.readiness, .ready)
        let secondStore = try await LibraryStore.open(documentsDir: location.documentsDir, supportDir: location.supportDir)
        let reopenedTracks = try await secondStore.scan()
        XCTAssertEqual(reopenedTracks.first?.id, firstTrack.id)
        XCTAssertEqual(reopenedTracks.first?.relativeLocator, "roundtrip.wav")
        let storedTrack = try await secondStore.track(id: firstTrack.id)
        XCTAssertEqual(storedTrack.id, firstTrack.id)
    }

    /// An empty installation has no synthetic rows or automatic playback.
    func testEmptyLibraryAndNewPlayerAreSilent() async throws {
        let location = try makeLocation()
        defer { try? FileManager.default.removeItem(at: location.rootDir) }
        let store = try await LibraryStore.open(documentsDir: location.documentsDir, supportDir: location.supportDir)
        let tracks = try await store.scan()
        XCTAssertTrue(tracks.isEmpty)
        let player = PlaybackCoordinator(store: store, outputMode: .offline)
        let snapshot = await player.snapshot()
        XCTAssertEqual(snapshot.state, .stopped)
        XCTAssertNil(snapshot.trackID)
    }

    /// Audio must cross the production player node into the engine's actual output buffer.
    func testSelectedWaveRendersNonzeroPCMAndAdvancesTime() async throws {
        let location = try makeLocation()
        defer { try? FileManager.default.removeItem(at: location.rootDir) }
        try makeWave(at: location.documentsDir.appendingPathComponent("render.wav"))
        let store = try await LibraryStore.open(documentsDir: location.documentsDir, supportDir: location.supportDir)
        let tracks = try await store.scan()
        let track = try XCTUnwrap(tracks.first)
        let player = PlaybackCoordinator(store: store, outputMode: .offline)
        await player.select(trackID: track.id)
        let result = try await player.renderOffline(frameCount: AppConfiguration.bufferFrameCapacity)
        XCTAssertGreaterThan(result.peakMagnitude, 0)
        let snapshot = await player.snapshot()
        XCTAssertGreaterThan(snapshot.positionMilliseconds, 0)
        XCTAssertEqual(snapshot.trackID, track.id)
        await player.pause()
    }

    /// Selection and stale completion paths cannot clear a loss; explicit Play is required.
    func testRouteLossInhibitsSelectionUntilExplicitPlay() async throws {
        let location = try makeLocation()
        defer { try? FileManager.default.removeItem(at: location.rootDir) }
        try makeWave(at: location.documentsDir.appendingPathComponent("loss.wav"))
        let store = try await LibraryStore.open(documentsDir: location.documentsDir, supportDir: location.supportDir)
        let tracks = try await store.scan()
        let track = try XCTUnwrap(tracks.first)
        let player = PlaybackCoordinator(store: store, outputMode: .offline)
        await player.select(trackID: track.id)
        player.inhibitForRouteLoss()
        await player.finishRouteLoss()
        await player.select(trackID: track.id)
        let inhibited = await player.snapshot()
        XCTAssertTrue(inhibited.requiresExplicitPlay)
        XCTAssertNotEqual(inhibited.state, .playing)
        await player.play()
        let resumed = await player.snapshot()
        XCTAssertFalse(resumed.requiresExplicitPlay)
        XCTAssertEqual(resumed.state, .playing)
        await player.pause()
    }

    /// A retry after a changed-file read failure must reopen the file and keep refilling real audio.
    func testExplicitPlayRecoversSustainedAudioAfterReadFailure() async throws {
        let location = try makeLocation()
        defer { try? FileManager.default.removeItem(at: location.rootDir) }
        let filename = location.documentsDir.appendingPathComponent("retry.wav")
        try makeWave(at: filename)
        let completeData = try Data(contentsOf: filename)
        let store = try await LibraryStore.open(documentsDir: location.documentsDir, supportDir: location.supportDir)
        let tracks = try await store.scan()
        let track = try XCTUnwrap(tracks.first)
        let player = PlaybackCoordinator(store: store, outputMode: .offline)
        await player.select(trackID: track.id)

        let transfer = try FileHandle(forWritingTo: filename)
        try transfer.seekToEnd()
        try transfer.write(contentsOf: Data([0]))
        try transfer.close()
        _ = try await player.renderOffline(frameCount: AppConfiguration.bufferFrameCapacity)
        let failureTimeoutSeconds: TimeInterval = 2
        let pollingInterval = Duration.milliseconds(10)
        let failureDeadline = Date().addingTimeInterval(failureTimeoutSeconds)
        var failedSnapshot = await player.snapshot()
        while failedSnapshot.state != .failed && Date() < failureDeadline {
            try await Task.sleep(for: pollingInterval)
            failedSnapshot = await player.snapshot()
        }
        XCTAssertEqual(failedSnapshot.state, .failed)
        XCTAssertNotNil(failedSnapshot.failure)

        try completeData.write(to: filename, options: .atomic)
        let recoveredTracks = try await store.scan()
        XCTAssertEqual(recoveredTracks.first?.id, track.id)
        XCTAssertEqual(recoveredTracks.first?.readiness, .ready)
        await player.play()
        let recoveredSnapshot = await player.snapshot()
        XCTAssertEqual(recoveredSnapshot.state, .playing)
        XCTAssertNil(recoveredSnapshot.failure)

        // Rendering beyond the old pool catches a retry that starts old buffers with no refill path.
        let additionalRenderCount = 2
        let sustainedRenderCount = AppConfiguration.maximumScheduledBufferCount + additionalRenderCount
        for _ in 0..<sustainedRenderCount {
            let rendered = try await player.renderOffline(frameCount: AppConfiguration.bufferFrameCapacity)
            XCTAssertGreaterThan(rendered.peakMagnitude, 0)
            try await Task.sleep(for: pollingInterval)
        }
        await player.pause()
    }

    /// A declared WAV length exceeding bytes received remains pending until the closed file exists.
    func testGrowingWaveIsObservedWithoutPublishingReadyTrack() async throws {
        let location = try makeLocation()
        defer { try? FileManager.default.removeItem(at: location.rootDir) }
        let filename = location.documentsDir.appendingPathComponent("growing.wav")
        try makeWave(at: filename)
        let completeData = try Data(contentsOf: filename)
        let missingByteCount = 64
        try completeData.dropLast(missingByteCount).write(to: filename)
        let prefixFile = try AVAudioFile(forReading: filename)
        let prefixBuffer = try XCTUnwrap(AVAudioPCMBuffer(pcmFormat: prefixFile.processingFormat,
            frameCapacity: AppConfiguration.bufferFrameCapacity))
        try prefixFile.read(into: prefixBuffer)
        XCTAssertGreaterThan(prefixBuffer.frameLength, 0, "The fixture must be decodable despite missing intended trailing bytes")
        let store = try await LibraryStore.open(documentsDir: location.documentsDir, supportDir: location.supportDir)
        let pendingTracks = try await store.scan()
        let pending = try XCTUnwrap(pendingTracks.first)
        XCTAssertEqual(pending.readiness, .pending)
        XCTAssertGreaterThan(pending.observation.declaredContainerLength ?? 0, pending.observation.revisionBefore.byteLength)
        try completeData.write(to: filename)
        let completeTracks = try await store.scan()
        XCTAssertEqual(completeTracks.first?.readiness, .ready)
        XCTAssertEqual(completeTracks.first?.id, pending.id)
    }

    /// A parseable prefix says nothing about the intended source length for unsupported formats.
    func testDecodablePrefixObservationDoesNotProveMP3Completion() async throws {
        let location = try makeLocation()
        defer { try? FileManager.default.removeItem(at: location.rootDir) }
        // A complete MPEG-1 Layer III silent frame is independently parseable but may only be a prefix.
        let header = Data([0xFF, 0xFB, 0x90, 0x64])
        let frameByteCount = 417
        var frame = header
        frame.append(Data(repeating: 0, count: frameByteCount - header.count))
        let filename = location.documentsDir.appendingPathComponent("prefix.mp3")
        try frame.write(to: filename)
        let store = try await LibraryStore.open(documentsDir: location.documentsDir, supportDir: location.supportDir)
        let tracks = try await store.scan()
        let track = try XCTUnwrap(tracks.first)
        XCTAssertEqual(track.readiness, .pending)
        XCTAssertNil(track.observation.declaredContainerLength)
        XCTAssertEqual(track.observation.revisionBefore.byteLength, Int64(frameByteCount))
        XCTAssertEqual(track.observation.revisionBefore, track.observation.revisionAfter)
        XCTAssertTrue(track.observation.parserOutcome.contains("not established"))
    }

    /// A relative locator cannot escape Documents through parent segments or a symbolic link.
    func testFileContainmentRejectsEscapes() async throws {
        let location = try makeLocation()
        defer { try? FileManager.default.removeItem(at: location.rootDir) }
        let store = try await LibraryStore.open(documentsDir: location.documentsDir, supportDir: location.supportDir)
        do {
            _ = try await store.resolve(relativeLocator: "../outside.wav")
            XCTFail("Parent traversal was accepted")
        } catch {
            XCTAssertEqual((error as NSError).domain, AppConfiguration.errorDomain)
        }
        let outsideFilename = location.rootDir.appendingPathComponent("outside.wav")
        try makeWave(at: outsideFilename)
        try FileManager.default.createSymbolicLink(at: location.documentsDir.appendingPathComponent("linked.wav"), withDestinationURL: outsideFilename)
        do {
            _ = try await store.resolve(relativeLocator: "linked.wav")
            XCTFail("Symbolic link escape was accepted")
        } catch {
            XCTAssertEqual((error as NSError).domain, AppConfiguration.errorDomain)
        }
    }

    /// Checks actual packaged JSON and image membership through the same loader used by Files.
    func testBundledDarkSkinLoadsRequiredImage() async throws {
        let resourceDir = try XCTUnwrap(Bundle.main.resourceURL)
        let skin = try await SkinLoader.load(skinDir: resourceDir.appendingPathComponent("Skins/Dark"))
        XCTAssertEqual(skin.description.schemaVersion, AppConfiguration.schemaVersion)
        XCTAssertEqual(skin.description.name, AppCopy.dark)
        XCTAssertFalse(try XCTUnwrap(skin.imageDataByRole[SkinRole.controlSurface.rawValue]).isEmpty)
    }

    /// Each test receives disk-backed isolated directories without touching a user's library.
    private func makeLocation() throws -> (rootDir: URL, documentsDir: URL, supportDir: URL) {
        let rootDir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        let documentsDir = rootDir.appendingPathComponent("Documents")
        let supportDir = rootDir.appendingPathComponent("Application Support")
        try FileManager.default.createDirectory(at: documentsDir, withIntermediateDirectories: true)
        return (rootDir, documentsDir, supportDir)
    }

    /// Writes a real closed PCM container whose samples are large enough to detect a silent graph.
    private func makeWave(at filename: URL) throws {
        let sampleRate = 48_000.0
        let sampleCount = 96_000
        let amplitude: Int16 = 8_192
        let format = try XCTUnwrap(AVAudioFormat(commonFormat: .pcmFormatInt16, sampleRate: sampleRate, channels: 1, interleaved: true))
        let buffer = try XCTUnwrap(AVAudioPCMBuffer(pcmFormat: format, frameCapacity: AVAudioFrameCount(sampleCount)))
        buffer.frameLength = buffer.frameCapacity
        let channelIndex = 0
        let sample = try XCTUnwrap(buffer.int16ChannelData?[channelIndex])
        let periodSampleCount = 100
        for sampleIndex in 0..<sampleCount {
            sample[sampleIndex] = sampleIndex % periodSampleCount < periodSampleCount / 2 ? amplitude : -amplitude
        }
        let file = try AVAudioFile(forWriting: filename, settings: format.settings, commonFormat: .pcmFormatInt16, interleaved: true)
        try file.write(from: buffer)
    }
}
