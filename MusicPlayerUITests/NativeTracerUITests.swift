import XCTest

/// Uses the externally transferred fixture to prove real Files interaction and silent relaunch.
final class NativeTracerUITests: XCTestCase {
    /// A real row starts playback, its rendered clock advances, and relaunch never starts audio.
    @MainActor
    func testTransferredWavePlaysAndRelaunchesSilently() throws {
        let app = XCUIApplication()
        app.launch()
        let appearanceTimeout: TimeInterval = 20
        let playbackTimeout: TimeInterval = 10
        let track = app.buttons["track-native-tracer.wav"]
        XCTAssertTrue(track.waitForExistence(timeout: appearanceTimeout))
        track.tap()
        let state = app.staticTexts["playback-state"]
        let playing = XCTNSPredicateExpectation(predicate: NSPredicate(format: "label == %@", "Playing"), object: state)
        XCTAssertEqual(XCTWaiter.wait(for: [playing], timeout: playbackTimeout), .completed)
        let position = app.staticTexts["playback-position"]
        let firstPosition = position.label
        let advancing = XCTNSPredicateExpectation(predicate: NSPredicate(format: "label != %@", firstPosition), object: position)
        XCTAssertEqual(XCTWaiter.wait(for: [advancing], timeout: playbackTimeout), .completed)
        app.terminate()
        app.launch()
        XCTAssertTrue(state.waitForExistence(timeout: appearanceTimeout))
        XCTAssertEqual(state.label, "Stopped")
        XCTAssertEqual(app.staticTexts["playback-position"].label, "0:00")
    }
}
