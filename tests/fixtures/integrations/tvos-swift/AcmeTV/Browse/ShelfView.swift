import SwiftUI

struct Show: Identifiable {
    let id: String
    let title: String
    let offerId: String
}

struct ShelfView: View {
    let shows: [Show]
    @State private var locked: Set<String> = []

    var body: some View {
        ScrollView(.horizontal) {
            HStack {
                ForEach(shows) { show in
                    TileView(title: show.title, locked: locked.contains(show.id))
                        .task {
                            let entitlement = try? await MediaStoreClient.shared.entitlement(offerId: show.offerId)
                            if entitlement?.accessGranted != true { locked.insert(show.id) }
                        }
                }
            }
        }
    }
}

struct TileView: View {
    let title: String
    let locked: Bool

    var body: some View {
        VStack {
            Text(title)
            if locked { Image(systemName: "lock.fill") }
        }
    }
}
