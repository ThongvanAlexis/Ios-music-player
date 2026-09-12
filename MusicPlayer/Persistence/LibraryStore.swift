import AVFAudio
import CoreData
import Foundation

/// Distinguishes observed bytes from a file that the supported decoder can safely open.
enum TransferReadiness: String, Codable, Sendable {
    case pending, validating, ready, failed
}

/// Captures the identity and length of a regular file at one observation point.
struct FileRevision: Codable, Equatable, Sendable {
    let resourceIdentity: String
    let byteLength: Int64
    let modificationDate: Date
}

/// Retains both sides of parsing so a transfer's actual changes can be inspected on a phone.
struct TransferObservation: Codable, Sendable {
    let locator: String
    let revisionBefore: FileRevision
    let revisionAfter: FileRevision
    let declaredContainerLength: Int64?
    let parserOutcome: String
    let observedAt: Date
}

/// Carries file information across isolation without exposing a managed object or absolute sandbox path.
struct TrackSnapshot: Identifiable, Sendable {
    let id: UUID
    let filename: String
    let relativeLocator: String
    let metadata: String?
    let readiness: TransferReadiness
    let durationMilliseconds: Int64?
    let observation: TransferObservation
}

/// Owns the versioned SQLite model and all Documents discovery outside the main actor.
actor LibraryStore {
    private let documentsDir: URL
    private let context: NSManagedObjectContext
    private let coordinator: NSPersistentStoreCoordinator
    private static let entityName = "TrackRecord"

    /// Defines managed field names once for model construction, reads, and transactional writes.
    private enum Field {
        static let id = "id"
        static let relativeLocator = "relativeLocator"
        static let revision = "revision"
        static let readiness = "readiness"
        static let durationMilliseconds = "durationMilliseconds"
        static let observation = "observation"
    }

    /// Opens a real disk-backed store on a worker executor, including the first SQLite creation.
    static func open(documentsDir: URL, supportDir: URL) async throws -> LibraryStore {
        try await Task.detached(priority: .userInitiated) {
            try LibraryStore(documentsDir: documentsDir, supportDir: supportDir)
        }.value
    }

    /// Releases SQLite and its journal handles before temporary storage is removed; repeated closes are safe.
    func close() throws {
        try context.performAndWait {
            context.reset()
            let persistentStores = coordinator.persistentStores
            for persistentStore in persistentStores {
                try coordinator.remove(persistentStore)
            }
        }
    }

    /// Creates disk storage and a private Core Data context while startup runs on a worker executor.
    private init(documentsDir: URL, supportDir: URL) throws {
        self.documentsDir = documentsDir.standardizedFileURL.resolvingSymlinksInPath()
        try FileManager.default.createDirectory(at: documentsDir, withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: supportDir, withIntermediateDirectories: true)
        coordinator = NSPersistentStoreCoordinator(managedObjectModel: Self.makeModel())
        let storeFilename = supportDir.appendingPathComponent("Library.sqlite")
        try coordinator.addPersistentStore(ofType: NSSQLiteStoreType, configurationName: nil, at: storeFilename,
            options: [NSMigratePersistentStoresAutomaticallyOption: true,
                      NSInferMappingModelAutomaticallyOption: true,
                      NSPersistentStoreFileProtectionKey: FileProtectionType.completeUntilFirstUserAuthentication])
        context = NSManagedObjectContext(concurrencyType: .privateQueueConcurrencyType)
        context.persistentStoreCoordinator = coordinator
        // The imported global policy is mutable shared state; each store owns its own policy.
        context.mergePolicy = NSMergePolicy(merge: .mergeByPropertyObjectTrumpMergePolicyType)
    }

    /// Records every observed regular file, retaining unsupported formats as inspectable pending rows.
    func scan() throws -> [TrackSnapshot] {
        let keys: [URLResourceKey] = [.isRegularFileKey, .isSymbolicLinkKey]
        var filenames: [URL] = []
        var enumerationError: Error?
        guard let enumerator = FileManager.default.enumerator(at: documentsDir, includingPropertiesForKeys: keys,
            options: [.skipsHiddenFiles], errorHandler: { _, error in enumerationError = error; return false }) else {
            throw Self.failure("Documents could not be enumerated.")
        }
        for case let filename as URL in enumerator {
            let value = try filename.resourceValues(forKeys: Set(keys))
            guard value.isSymbolicLink != true, value.isRegularFile == true else { continue }
            filenames.append(filename)
        }
        if let enumerationError { throw enumerationError }
        filenames.sort { $0.path < $1.path }
        var tracks: [TrackSnapshot] = []
        for filename in filenames {
            let locator = String(filename.path.dropFirst(documentsDir.path.count + 1))
            let observation = try observe(relativeLocator: locator)
            let track = try persist(observation: observation.value, readiness: observation.readiness, durationMilliseconds: observation.durationMilliseconds)
            tracks.append(track)
        }
        return tracks.sorted {
            let order = $0.filename.localizedStandardCompare($1.filename)
            return order == .orderedSame ? $0.id.uuidString < $1.id.uuidString : order == .orderedAscending
        }
    }

    /// Reads the selected persisted row so UI identities always traverse SQLite before playback.
    func track(id: UUID) throws -> TrackSnapshot {
        try context.performAndWait {
            let request = NSFetchRequest<NSManagedObject>(entityName: Self.entityName)
            request.predicate = NSPredicate(format: "%K == %@", Field.id, id as NSUUID)
            request.fetchLimit = 1
            guard let record = try context.fetch(request).first else { throw Self.failure("The selected track is missing from the library.") }
            return try Self.snapshot(record)
        }
    }

    /// Resolves relative storage only inside the current Documents root and rejects symbolic links.
    func resolve(relativeLocator: String) throws -> URL {
        let components = relativeLocator.split(separator: "/", omittingEmptySubsequences: false)
        guard !relativeLocator.isEmpty, !relativeLocator.hasPrefix("/"), !relativeLocator.contains("\\"),
              components.allSatisfy({ !$0.isEmpty && $0 != "." && $0 != ".." }) else {
            throw Self.failure("The file location is not a contained relative path.")
        }
        var candidate = documentsDir
        for component in components {
            candidate.appendPathComponent(String(component))
            let value = try candidate.resourceValues(forKeys: [.isSymbolicLinkKey])
            guard value.isSymbolicLink != true else { throw Self.failure("Symbolic links are not supported in the music library.") }
        }
        let resolvedFilename = candidate.standardizedFileURL.resolvingSymlinksInPath()
        guard resolvedFilename.path.hasPrefix(documentsDir.path + "/"),
              try resolvedFilename.resourceValues(forKeys: [.isRegularFileKey]).isRegularFile == true else {
            throw Self.failure("The selected location is not a regular file inside Documents.")
        }
        return resolvedFilename
    }

    /// Rechecks observed identity immediately before opening the selected decoder.
    func playbackFile(id: UUID) throws -> (filename: URL, track: TrackSnapshot) {
        let track = try track(id: id)
        let observation = try observe(relativeLocator: track.relativeLocator)
        guard observation.readiness == .ready,
              observation.value.revisionAfter == track.observation.revisionAfter else {
            throw Self.failure("The file changed or its complete WAV container could not be verified. Return to Files to check it again.")
        }
        return (try resolve(relativeLocator: track.relativeLocator), track)
    }

    /// Captures filesystem metadata directly so cached URL values cannot conceal an active transfer.
    static func revision(filename: URL) throws -> FileRevision {
        let attributeByKey = try FileManager.default.attributesOfItem(atPath: filename.path)
        guard let length = attributeByKey[.size] as? NSNumber,
              let modified = attributeByKey[.modificationDate] as? Date,
              let number = attributeByKey[.systemFileNumber] as? NSNumber,
              let device = attributeByKey[.systemNumber] as? NSNumber,
              attributeByKey[.type] as? FileAttributeType == .typeRegular else {
            throw failure("Required regular-file attributes are unavailable.")
        }
        return FileRevision(resourceIdentity: "\(device):\(number)", byteLength: length.int64Value, modificationDate: modified)
    }

    /// Observes unsupported formats without inventing a completion proof from stable size or a prefix.
    private func observe(relativeLocator: String) throws -> (value: TransferObservation, readiness: TransferReadiness, durationMilliseconds: Int64?) {
        let filename = try resolve(relativeLocator: relativeLocator)
        let before = try Self.revision(filename: filename)
        var readiness = TransferReadiness.pending
        var declaredLength: Int64?
        var durationMilliseconds: Int64?
        var outcome = "Container completion is not established. Only closed PCM WAV files are playable in this build."
        if filename.pathExtension.lowercased() == "wav" {
            do {
                let parsed = try Self.validateWave(filename: filename, byteLength: before.byteLength)
                declaredLength = parsed.declaredLength
                if parsed.complete {
                    let file = try AVAudioFile(forReading: filename)
                    guard file.length > 0, file.processingFormat.sampleRate > 0 else { throw Self.failure("The WAV contains no decodable audio frames.") }
                    durationMilliseconds = Int64(Double(file.length) / file.processingFormat.sampleRate * AppConfiguration.millisecondsPerSecond)
                    readiness = .ready
                    outcome = "Closed PCM WAV: RIFF length and chunk boundaries match the observed bytes."
                } else {
                    outcome = "The RIFF declaration exceeds the received bytes. Transfer completion is not established."
                }
            } catch {
                readiness = .failed
                outcome = TechnicalFailure(operation: "Inspect WAV", file: relativeLocator, error: error).text
            }
        }
        let after = try Self.revision(filename: filename)
        if before != after {
            readiness = .pending
            durationMilliseconds = nil
            outcome = "The file changed during inspection. Transfer completion is not established."
        }
        return (TransferObservation(locator: relativeLocator, revisionBefore: before, revisionAfter: after,
            declaredContainerLength: declaredLength, parserOutcome: outcome, observedAt: Date()), readiness, durationMilliseconds)
    }

    /// Validates bounded RIFF headers and complete PCM data while never loading the song into memory.
    private static func validateWave(filename: URL, byteLength: Int64) throws -> (declaredLength: Int64, complete: Bool) {
        let file = try FileHandle(forReadingFrom: filename)
        defer { try? file.close() }
        let riffHeaderByteCount = 12
        let chunkHeaderByteCount = 8
        let identifierByteCount = 4
        let riffLengthOffset = 4
        let waveIdentifierOffset = 8
        let pcmFormatByteCount = 16
        let formatTagOffset = 0
        let blockAlignmentOffset = 12
        let pcmIntegerFormatTag: UInt16 = 1
        let header = try file.read(upToCount: riffHeaderByteCount) ?? Data()
        guard header.count == riffHeaderByteCount,
              String(data: header.prefix(identifierByteCount), encoding: .ascii) == "RIFF",
              String(data: header.suffix(from: waveIdentifierOffset), encoding: .ascii) == "WAVE" else {
            throw failure("A complete RIFF/WAVE header is required.")
        }
        let declaredLength = Int64(readUInt32(header, offset: riffLengthOffset)) + Int64(chunkHeaderByteCount)
        guard declaredLength <= byteLength else { return (declaredLength, false) }
        guard declaredLength == byteLength else { throw failure("The RIFF length does not match the file length.") }
        var offset = Int64(riffHeaderByteCount)
        var blockAlignment: UInt16?
        var audioByteLength: Int64?
        let deadline = Date().addingTimeInterval(AppConfiguration.preparationTimeoutSeconds)
        while offset < declaredLength {
            guard Date() < deadline, declaredLength - offset >= Int64(chunkHeaderByteCount) else { throw failure("The WAV chunk list is incomplete or inspection timed out.") }
            try file.seek(toOffset: UInt64(offset))
            let chunk = try file.read(upToCount: chunkHeaderByteCount) ?? Data()
            guard chunk.count == chunkHeaderByteCount else { throw failure("The WAV chunk header is incomplete.") }
            let kind = String(data: chunk.prefix(identifierByteCount), encoding: .ascii)
            let length = Int64(readUInt32(chunk, offset: riffLengthOffset))
            let contentOffset = offset + Int64(chunkHeaderByteCount)
            let nextOffset = contentOffset + length + length % 2
            guard nextOffset <= declaredLength else { throw failure("A WAV chunk extends past the received file.") }
            if kind == "fmt " {
                guard blockAlignment == nil, length >= Int64(pcmFormatByteCount) else { throw failure("The PCM format chunk is missing or duplicated.") }
                let format = try file.read(upToCount: pcmFormatByteCount) ?? Data()
                guard format.count == pcmFormatByteCount,
                      readUInt16(format, offset: formatTagOffset) == pcmIntegerFormatTag else { throw failure("This build supports integer PCM WAV only.") }
                blockAlignment = readUInt16(format, offset: blockAlignmentOffset)
            } else if kind == "data" {
                guard audioByteLength == nil else { throw failure("Multiple audio data chunks are not supported.") }
                audioByteLength = length
            }
            offset = nextOffset
        }
        guard let blockAlignment, blockAlignment > 0, let audioByteLength, audioByteLength > 0,
              audioByteLength % Int64(blockAlignment) == 0 else { throw failure("The WAV lacks complete aligned PCM frames.") }
        return (declaredLength, true)
    }

    private static func readUInt32(_ data: Data, offset: Int) -> UInt32 {
        let byteCount = MemoryLayout<UInt32>.size
        let bitsPerByte = 8
        return (0..<byteCount).reduce(0) { $0 | UInt32(data[offset + $1]) << (bitsPerByte * $1) }
    }

    private static func readUInt16(_ data: Data, offset: Int) -> UInt16 {
        let byteCount = MemoryLayout<UInt16>.size
        let bitsPerByte = 8
        return (0..<byteCount).reduce(0) { $0 | UInt16(data[offset + $1]) << (bitsPerByte * $1) }
    }

    /// Upserts by relative locator in one background transaction, then materializes the stored row.
    private func persist(observation: TransferObservation, readiness: TransferReadiness, durationMilliseconds: Int64?) throws -> TrackSnapshot {
        try context.performAndWait {
            let request = NSFetchRequest<NSManagedObject>(entityName: Self.entityName)
            request.predicate = NSPredicate(format: "%K == %@", Field.relativeLocator, observation.locator)
            request.fetchLimit = 1
            let record = try context.fetch(request).first ?? NSEntityDescription.insertNewObject(forEntityName: Self.entityName, into: context)
            if record.value(forKey: Field.id) == nil { record.setValue(UUID(), forKey: Field.id) }
            record.setValue(observation.locator, forKey: Field.relativeLocator)
            record.setValue(try JSONEncoder().encode(observation.revisionAfter), forKey: Field.revision)
            record.setValue(readiness.rawValue, forKey: Field.readiness)
            record.setValue(durationMilliseconds.map(NSNumber.init(value:)), forKey: Field.durationMilliseconds)
            record.setValue(try JSONEncoder().encode(observation), forKey: Field.observation)
            do { try context.save() } catch { context.rollback(); throw error }
            return try Self.snapshot(record)
        }
    }

    private static func snapshot(_ record: NSManagedObject) throws -> TrackSnapshot {
        guard let id = record.value(forKey: Field.id) as? UUID,
              let locator = record.value(forKey: Field.relativeLocator) as? String,
              let state = record.value(forKey: Field.readiness) as? String,
              let readiness = TransferReadiness(rawValue: state),
              let observationData = record.value(forKey: Field.observation) as? Data else { throw failure("A stored track record is incomplete.") }
        return TrackSnapshot(id: id, filename: URL(fileURLWithPath: locator).lastPathComponent, relativeLocator: locator,
            metadata: nil, readiness: readiness,
            durationMilliseconds: (record.value(forKey: Field.durationMilliseconds) as? NSNumber)?.int64Value,
            observation: try JSONDecoder().decode(TransferObservation.self, from: observationData))
    }

    /// Keeps the initial app-owned model version and field declarations in one location.
    private static func makeModel() -> NSManagedObjectModel {
        let model = NSManagedObjectModel()
        model.versionIdentifiers = ["MusicPlayer-\(AppConfiguration.schemaVersion)"]
        let entity = NSEntityDescription()
        entity.name = entityName
        entity.managedObjectClassName = "NSManagedObject"
        let fieldDescriptions: [(String, NSAttributeType, Bool)] = [
            (Field.id, .UUIDAttributeType, false), (Field.relativeLocator, .stringAttributeType, false),
            (Field.revision, .binaryDataAttributeType, false), (Field.readiness, .stringAttributeType, false),
            (Field.durationMilliseconds, .integer64AttributeType, true), (Field.observation, .binaryDataAttributeType, false)]
        entity.properties = fieldDescriptions.map { name, type, optional in
            let attribute = NSAttributeDescription()
            attribute.name = name
            attribute.attributeType = type
            attribute.isOptional = optional
            return attribute
        }
        entity.uniquenessConstraints = [[Field.id], [Field.relativeLocator]]
        model.entities = [entity]
        return model
    }

    /// Creates an English operation failure while allowing callers to retain any underlying NSError.
    static func failure(_ description: String) -> NSError {
        let invalidFileCode = 1
        return NSError(domain: AppConfiguration.errorDomain, code: invalidFileCode, userInfo: [NSLocalizedDescriptionKey: description])
    }
}
