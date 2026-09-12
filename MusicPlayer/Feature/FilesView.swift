import Observation
import SwiftUI
import UIKit

/// Owns concrete screen state while service actors perform file, database, and audio work.
@MainActor
@Observable
final class FilesModel {
    var tracks: [TrackSnapshot] = []
    var playback = PlaybackSnapshot.empty
    var skin = Skin.emergency
    var failures: [TechnicalFailure] = []
    var isChecking = false
    private var store: LibraryStore?
    private var coordinator: PlaybackCoordinator?
    private var isStarting = false

    /// Starts the service owners once and reads the first Documents inventory without starting sound.
    func start() async {
        guard !isStarting, store == nil else { return }
        isStarting = true
        defer { isStarting = false }
        do {
            guard let resourceDir = Bundle.main.resourceURL else { throw LibraryStore.failure("The app resource directory is missing.") }
            skin = try await SkinLoader.load(skinDir: resourceDir.appendingPathComponent("Skins/Dark"))
        } catch { retain(TechnicalFailure(operation: "Load Dark appearance", error: error)) }
        do {
            let fileManager = FileManager.default
            let documentsDir = try fileManager.url(for: .documentDirectory, in: .userDomainMask, appropriateFor: nil, create: false)
            let supportDir = try fileManager.url(for: .applicationSupportDirectory, in: .userDomainMask, appropriateFor: nil, create: false)
                .appendingPathComponent(AppConfiguration.supportDirectoryName)
            let store = try await LibraryStore.open(documentsDir: documentsDir, supportDir: supportDir)
            self.store = store
            let coordinator = PlaybackCoordinator(store: store)
            self.coordinator = coordinator
            await coordinator.observeAudioSession()
            await refresh()
        } catch { retain(TechnicalFailure(operation: "Open music library", error: error)) }
    }

    /// Checks foreground transfers without replacing the playback owner or granting start permission.
    func refresh() async {
        guard let store, !isChecking else { return }
        isChecking = true
        defer { isChecking = false }
        do { tracks = try await store.scan() }
        catch { retain(TechnicalFailure(operation: "Check transferred files", error: error)) }
    }

    /// Sends a real persisted identifier to the shared player and keeps the user in Files.
    func select(trackID: UUID) async {
        await coordinator?.select(trackID: trackID)
        await updatePlayback()
    }

    /// Routes the visible transport button through the same explicit Play authority.
    func togglePlayback() async {
        guard let coordinator else { return }
        if playback.state == .playing { await coordinator.pause() }
        else { await coordinator.play() }
        await updatePlayback()
    }

    /// Refreshes display snapshots without calculating playback time in the UI.
    func updatePlayback() async {
        guard let coordinator else { return }
        playback = await coordinator.snapshot()
        if let failure = playback.failure { retain(failure) }
    }

    /// Bounds retained diagnostic text while leaving older errors visible after later successful playback.
    private func retain(_ failure: TechnicalFailure) {
        guard !failures.contains(where: { $0.id == failure.id }) else { return }
        failures.append(failure)
        if failures.count > AppConfiguration.maximumDiagnosticCount { failures.removeFirst() }
    }
}

/// Presents actual transferred files, a shared compact transport, and copyable technical details.
struct FilesView: View {
    @Bindable var model: FilesModel
    @Environment(\.scenePhase) private var scenePhase
    @State private var selectedTrack: TrackSnapshot?
    @State private var showsFailure = false

    var body: some View {
        NavigationStack {
            VStack(spacing: AppConfiguration.pageSpacing) {
                if model.isChecking {
                    ProgressView(model.tracks.isEmpty ? AppCopy.initialDiscovery : AppCopy.existingDiscovery)
                        .tint(model.skin.color(.accent))
                }
                if model.tracks.isEmpty && !model.isChecking {
                    ContentUnavailableView {
                        Label(AppCopy.filesEmptyHeading, systemImage: "music.note")
                    } description: { Text(AppCopy.filesEmptyBody) }
                } else {
                    List(model.tracks) { track in
                        HStack(spacing: AppConfiguration.compactSpacing) {
                            Button {
                                Task { await model.select(trackID: track.id) }
                            } label: {
                                VStack(alignment: .leading, spacing: AppConfiguration.compactSpacing) {
                                    Text(track.filename).foregroundStyle(model.skin.color(.primaryText))
                                    if track.readiness != .ready {
                                        Text(track.readiness == .failed ? AppCopy.failed : AppCopy.incompleteTransfer)
                                            .font(.caption).foregroundStyle(model.skin.color(.secondaryText))
                                    }
                                }.frame(maxWidth: .infinity, alignment: .leading)
                            }
                            .buttonStyle(.plain)
                            .disabled(track.readiness != .ready)
                            .accessibilityIdentifier("track-\(track.filename)")
                            Button { selectedTrack = track } label: { Image(systemName: "info.circle") }
                                .buttonStyle(.borderless)
                                .frame(minWidth: AppConfiguration.minimumControlSize, minHeight: AppConfiguration.minimumControlSize)
                                .accessibilityLabel("\(AppCopy.fileDetails): \(track.filename)")
                        }
                        .listRowBackground(model.skin.color(.panel))
                    }
                    .scrollContentBackground(.hidden)
                    .refreshable { await model.refresh() }
                }
                if model.playback.requiresExplicitPlay {
                    Text(AppCopy.headphonesDisconnected).font(.callout).frame(maxWidth: .infinity, alignment: .leading)
                }
                if !model.failures.isEmpty {
                    Button(AppCopy.errorDetails) { showsFailure = true }
                        .frame(minHeight: AppConfiguration.minimumControlSize)
                        .frame(maxWidth: .infinity).background(model.skin.color(.errorPanel))
                }
                transport
            }
            .padding(.horizontal, AppConfiguration.pageSpacing)
            .background(model.skin.color(.page))
            .foregroundStyle(model.skin.color(.primaryText))
            .tint(model.skin.color(.accent))
            .navigationTitle(AppCopy.files)
            .task {
                await model.start()
                while !Task.isCancelled {
                    await model.updatePlayback()
                    do { try await Task.sleep(for: .seconds(AppConfiguration.snapshotIntervalSeconds)) }
                    catch { return }
                }
            }
            .onChange(of: scenePhase) { _, phase in
                if phase == .active { Task { await model.refresh() } }
            }
            .sheet(item: $selectedTrack) { track in FileDetailsView(track: track) }
            .sheet(isPresented: $showsFailure) { ErrorDetailsView(failures: model.failures) }
        }
    }

    private var transport: some View {
        HStack(spacing: AppConfiguration.pageSpacing) {
            VStack(alignment: .leading, spacing: AppConfiguration.compactSpacing) {
                Text(model.playback.filename ?? AppCopy.noTrackHeading).lineLimit(2)
                Text(stateLabel).accessibilityIdentifier("playback-state")
                    .foregroundStyle(model.skin.color(.secondaryText))
                Text(AppCopy.elapsedTime(milliseconds: model.playback.positionMilliseconds))
                    .monospacedDigit().accessibilityIdentifier("playback-position")
            }.frame(maxWidth: .infinity, alignment: .leading)
            Button { Task { await model.togglePlayback() } } label: {
                Image(systemName: model.playback.state == .playing ? "pause.fill" : "play.fill")
                    .frame(minWidth: AppConfiguration.minimumControlSize, minHeight: AppConfiguration.minimumControlSize)
            }
            .disabled(model.playback.trackID == nil || model.playback.state == .preparing)
            .accessibilityLabel(model.playback.state == .playing ? AppCopy.pauseTrack : AppCopy.playTrack)
        }
        .padding(AppConfiguration.pageSpacing)
        .background {
            model.skin.color(.controlSurface)
            if let data = model.skin.imageDataByRole[SkinRole.controlSurface.rawValue], let image = UIImage(data: data) {
                Image(uiImage: image).resizable(resizingMode: .tile).accessibilityHidden(true)
            }
        }
    }

    private var stateLabel: String {
        switch model.playback.state {
        case .stopped: AppCopy.stopped
        case .preparing: AppCopy.preparing
        case .playing: AppCopy.playing
        case .paused: AppCopy.paused
        case .failed: AppCopy.failed
        }
    }
}

/// Shows every observed file's actual revisions, including unsupported or pending transfer rows.
struct FileDetailsView: View {
    let track: TrackSnapshot
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: AppConfiguration.pageSpacing) {
                    Text(detailText).textSelection(.enabled).frame(maxWidth: .infinity, alignment: .leading)
                    Button(AppCopy.copyFileDetails) { UIPasteboard.general.string = detailText }
                        .frame(minHeight: AppConfiguration.minimumControlSize)
                }.padding(AppConfiguration.pageSpacing)
            }
            .navigationTitle(AppCopy.fileDetails)
            .toolbar { Button(AppCopy.closeFileDetails) { dismiss() } }
        }
    }

    private var detailText: String {
        let observation = track.observation
        return ["\(AppCopy.filename): \(track.filename)", "\(AppCopy.relativeLocation): \(track.relativeLocator)",
            "\(AppCopy.observedTime): \(observation.observedAt.ISO8601Format())",
            "\(AppCopy.revisionBeforeParsing)\n\(revisionText(observation.revisionBefore))",
            "\(AppCopy.revisionAfterParsing)\n\(revisionText(observation.revisionAfter))",
            "\(AppCopy.declaredContainerLength): \(observation.declaredContainerLength.map(String.init) ?? AppCopy.notProvided)",
            "\(AppCopy.parserResult): \(observation.parserOutcome)"].joined(separator: "\n\n")
    }

    private func revisionText(_ revision: FileRevision) -> String {
        ["\(AppCopy.resourceIdentity): \(revision.resourceIdentity)", "\(AppCopy.byteLength): \(revision.byteLength)",
         "\(AppCopy.modificationTime): \(revision.modificationDate.ISO8601Format())"].joined(separator: "\n")
    }
}

/// Keeps complete captured error text selectable and copyable without interrupting working audio.
struct ErrorDetailsView: View {
    let failures: [TechnicalFailure]
    @Environment(\.dismiss) private var dismiss
    @State private var copied = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: AppConfiguration.pageSpacing) {
                    Text(detailText).textSelection(.enabled).frame(maxWidth: .infinity, alignment: .leading)
                    Button(AppCopy.copyErrorDetails) {
                        UIPasteboard.general.string = detailText
                        copied = true
                    }.frame(minHeight: AppConfiguration.minimumControlSize)
                    if copied { Text(AppCopy.copySuccess) }
                }.padding(AppConfiguration.pageSpacing)
            }
            .navigationTitle(AppCopy.errorDetails)
            .toolbar { Button(AppCopy.closeDiagnostics) { dismiss() } }
        }
    }

    private var detailText: String { failures.reversed().map(\.text).joined(separator: "\n\n") }
}
