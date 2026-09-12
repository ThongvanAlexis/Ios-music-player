import Foundation
import ImageIO
import SwiftUI

/// Names semantic appearance roles shared by bundled data and native controls.
enum SkinRole: String, Codable, CaseIterable, Sendable {
    case page, panel, controlSurface, primaryText, secondaryText, accent, errorPanel
}

/// Associates a semantic color with an optional image while leaving layout in native code.
struct SkinAppearance: Codable, Sendable {
    let color: String
    let image: String?
}

/// Defines the first versioned, app-owned JSON appearance format.
struct SkinDescription: Codable, Sendable {
    let schemaVersion: Int
    let name: String
    let appearanceByRole: [String: SkinAppearance]
}

/// Carries validated appearance and image bytes from the background loader to SwiftUI.
struct Skin: Sendable {
    let description: SkinDescription
    let imageDataByRole: [String: Data]

    /// Resolves a validated role's hex color for the native drawing layer.
    func color(_ role: SkinRole) -> Color {
        let maximumChannelValue: Double = 255
        let bitsPerChannel = 8
        let blueMask: UInt32 = 0xFF
        let greenShift = bitsPerChannel
        let redShift = bitsPerChannel * 2
        let value = UInt32(description.appearanceByRole[role.rawValue]?.color ?? "FFFFFF", radix: 16) ?? 0xFFFFFF
        return Color(red: Double((value >> redShift) & blueMask) / maximumChannelValue,
            green: Double((value >> greenShift) & blueMask) / maximumChannelValue,
            blue: Double(value & blueMask) / maximumChannelValue)
    }

    /// Keeps diagnostics reachable if packaged appearance data cannot be decoded.
    static let emergency = Skin(description: SkinDescription(schemaVersion: AppConfiguration.schemaVersion, name: "Emergency",
        appearanceByRole: Dictionary(uniqueKeysWithValues: SkinRole.allCases.map { role in
            let isSurface = [SkinRole.page, .panel, .controlSurface, .errorPanel].contains(role)
            return (role.rawValue, SkinAppearance(color: isSurface ? "000000" : "FFFFFF", image: nil))
        })), imageDataByRole: [:])
}

/// Loads the same versioned JSON-and-image format that subsequent appearance sources will use.
enum SkinLoader {
    /// Performs all resource reads and JSON validation away from the main actor.
    static func load(skinDir: URL) async throws -> Skin {
        try await Task.detached(priority: .userInitiated) {
            let description = try JSONDecoder().decode(SkinDescription.self,
                from: Data(contentsOf: skinDir.appendingPathComponent("skin.json")))
            guard description.schemaVersion == AppConfiguration.schemaVersion else { throw LibraryStore.failure("The skin schema version is unsupported.") }
            let hexColorCharacterCount = 6
            var imageDataByRole: [String: Data] = [:]
            for role in SkinRole.allCases {
                guard let appearance = description.appearanceByRole[role.rawValue],
                      appearance.color.count == hexColorCharacterCount,
                      UInt32(appearance.color, radix: 16) != nil else {
                    throw LibraryStore.failure("Skin role \(role.rawValue) is missing or has an invalid color.")
                }
                if let basename = appearance.image {
                    guard !basename.isEmpty, !basename.contains("/"), !basename.contains("\\"), basename != ".", basename != ".." else {
                        throw LibraryStore.failure("A skin image must name a local resource in its own directory.")
                    }
                    let imageFilename = skinDir.appendingPathComponent(basename).resolvingSymlinksInPath()
                    guard imageFilename.deletingLastPathComponent() == skinDir.resolvingSymlinksInPath() else {
                        throw LibraryStore.failure("A skin image escapes its resource directory.")
                    }
                    let data = try Data(contentsOf: imageFilename)
                    let firstImageIndex = 0
                    guard let source = CGImageSourceCreateWithData(data as CFData, nil),
                          CGImageSourceCreateImageAtIndex(source, firstImageIndex, nil) != nil else {
                        throw LibraryStore.failure("Skin image \(basename) could not be decoded.")
                    }
                    imageDataByRole[role.rawValue] = data
                }
            }
            guard imageDataByRole[SkinRole.controlSurface.rawValue] != nil else { throw LibraryStore.failure("The bundled control surface image is missing.") }
            return Skin(description: description, imageDataByRole: imageDataByRole)
        }.value
    }
}
