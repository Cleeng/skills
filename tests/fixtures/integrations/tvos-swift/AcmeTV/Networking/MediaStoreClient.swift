import Foundation

struct Entitlement: Decodable {
    let offerId: String
    let accessGranted: Bool
}

final class MediaStoreClient {
    static let shared = MediaStoreClient()
    private let base = URL(string: "https://mediastoreapi.cleeng.com")!
    private let session: URLSession = {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 8
        return URLSession(configuration: config)
    }()

    var jwt: String?
    var refreshToken: String?

    func entitlement(offerId: String) async throws -> Entitlement {
        var request = URLRequest(url: base.appendingPathComponent("entitlements/\(offerId)"))
        request.setValue("Bearer \(jwt ?? "")", forHTTPHeaderField: "Authorization")
        let (data, _) = try await session.data(for: request)
        return try JSONDecoder().decode(Envelope<Entitlement>.self, from: data).responseData
    }

    func refresh() async throws {
        var request = URLRequest(url: base.appendingPathComponent("auths/refresh_token"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(["refreshToken": refreshToken ?? ""])
        let (data, _) = try await session.data(for: request)
        let tokens = try JSONDecoder().decode(Envelope<Tokens>.self, from: data).responseData
        jwt = tokens.jwt
        refreshToken = tokens.refreshToken
    }
}

struct Tokens: Decodable {
    let jwt: String
    let refreshToken: String
}

struct Envelope<T: Decodable>: Decodable {
    let responseData: T
}
