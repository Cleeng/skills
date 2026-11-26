import SwiftUI

@main
struct AcmeTVApp: App {
    init() {
        SessionManager.shared.start()
    }

    var body: some Scene {
        WindowGroup {
            ShelfView(shows: Catalog.featured)
        }
    }
}

enum Catalog {
    static let featured: [Show] = []
}
