import Foundation

final class SessionManager {
    static let shared = SessionManager()
    private var timer: Timer?

    func start() {
        timer = Timer.scheduledTimer(withTimeInterval: 600, repeats: true) { _ in
            Task { try? await MediaStoreClient.shared.refresh() }
        }
    }

    func stop() {
        timer?.invalidate()
    }
}
