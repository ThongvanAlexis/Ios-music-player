import SwiftUI

/// Composes the native Files screen with one long-lived storage and playback owner.
@main
struct MusicPlayerApp: App {
    @State private var model = FilesModel()

    var body: some Scene {
        WindowGroup {
            FilesView(model: model)
                .preferredColorScheme(.dark)
        }
    }
}
