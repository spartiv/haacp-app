import Foundation
import Observation

@MainActor
@Observable
final class AuthStore {
    private(set) var currentUser: UserResponse?
    private(set) var organizationId: String?
    private(set) var accessToken: String?
    private(set) var refreshToken: String?

    var isAuthenticated: Bool { accessToken != nil && organizationId != nil }

    private var refreshTask: Task<TokenResponse, Error>?

    init() {
        accessToken = KeychainHelper.load(forKey: "access_token")
        refreshToken = KeychainHelper.load(forKey: "refresh_token")
        organizationId = UserDefaults.standard.string(forKey: "org_id")
    }

    // MARK: - Public auth actions

    func login(email: String, password: String) async throws {
        let response = try await APIClient.login(email: email, password: password)
        guard response.organizationId != nil else {
            throw HaacpError.api(code: "no_organization", message: "Акаунт не прив'язаний до організації")
        }
        apply(response)
    }

    func signup(email: String, password: String, fullName: String, organizationName: String) async throws {
        let response = try await APIClient.signup(
            email: email, password: password,
            fullName: fullName, organizationName: organizationName
        )
        guard response.organizationId != nil else {
            throw HaacpError.api(code: "no_organization", message: "Акаунт не прив'язаний до організації")
        }
        apply(response)
    }

    func logout() async {
        if let token = accessToken, let rt = refreshToken {
            try? await APIClient.logout(refreshToken: rt, token: token)
        }
        clear()
    }

    // MARK: - Authenticated call wrapper (handles 401 → refresh → retry)

    func call<T: Sendable>(_ work: @Sendable (String) async throws -> T) async throws -> T {
        guard let token = accessToken else {
            clear()
            throw HaacpError.unauthorized
        }
        do {
            return try await work(token)
        } catch HaacpError.unauthorized {
            guard let rt = refreshToken else {
                clear()
                throw HaacpError.unauthorized
            }
            do {
                let tokens = try await refreshSerially(refreshToken: rt)
                return try await work(tokens.accessToken)
            } catch {
                clear()
                throw HaacpError.unauthorized
            }
        }
    }

    // MARK: - Private

    // Serializes concurrent refresh attempts so a single-use refresh token is
    // not consumed twice when two requests receive 401 simultaneously.
    private func refreshSerially(refreshToken rt: String) async throws -> TokenResponse {
        if let existing = refreshTask {
            return try await existing.value
        }
        let task = Task { try await APIClient.refreshTokens(refreshToken: rt) }
        refreshTask = task
        defer { refreshTask = nil }
        let tokens = try await task.value
        updateTokens(tokens)
        return tokens
    }

    private func apply(_ response: AuthResponse) {
        currentUser = response.user
        accessToken = response.tokens.accessToken
        refreshToken = response.tokens.refreshToken
        if let orgId = response.organizationId {
            organizationId = orgId
            UserDefaults.standard.set(orgId, forKey: "org_id")
        }
        KeychainHelper.save(response.tokens.accessToken, forKey: "access_token")
        KeychainHelper.save(response.tokens.refreshToken, forKey: "refresh_token")
    }

    private func updateTokens(_ tokens: TokenResponse) {
        accessToken = tokens.accessToken
        refreshToken = tokens.refreshToken
        KeychainHelper.save(tokens.accessToken, forKey: "access_token")
        KeychainHelper.save(tokens.refreshToken, forKey: "refresh_token")
    }

#if DEBUG
    func setupForPreview() {
        accessToken = "preview-token"
        refreshToken = "preview-refresh"
        organizationId = UUID().uuidString
    }
#endif

    func clear() {
        currentUser = nil
        accessToken = nil
        refreshToken = nil
        organizationId = nil
        refreshTask?.cancel()
        refreshTask = nil
        KeychainHelper.delete(forKey: "access_token")
        KeychainHelper.delete(forKey: "refresh_token")
        UserDefaults.standard.removeObject(forKey: "org_id")
    }
}
