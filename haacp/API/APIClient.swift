import Foundation

enum APIClient {
    static let baseURL = "http://localhost:8000"

    private static let session = URLSession.shared
    private static let encoder = JSONEncoder()
    private static let decoder = JSONDecoder()

    // MARK: - Core

    private static func makeRequest(
        method: String,
        path: String,
        bodyData: Data?,
        token: String?
    ) throws -> URLRequest {
        guard let url = URL(string: baseURL + path) else { throw HaacpError.unknown }
        var req = URLRequest(url: url)
        req.httpMethod = method
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token { req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization") }
        req.httpBody = bodyData
        return req
    }

    private static func performRequest<T: Decodable>(
        method: String,
        path: String,
        bodyData: Data? = nil,
        token: String? = nil,
        expectedStatus: Int = 200
    ) async throws -> T {
        let req = try makeRequest(method: method, path: path, bodyData: bodyData, token: token)
        let (data, response) = try await session.data(for: req)
        let status = (response as? HTTPURLResponse)?.statusCode ?? 0

        if status == 401 { throw HaacpError.unauthorized }

        if status != expectedStatus {
            if let env = try? decoder.decode(APIErrorEnvelope.self, from: data) {
                throw HaacpError.api(code: env.error.code, message: env.error.message)
            }
            throw HaacpError.unknown
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw HaacpError.unknown
        }
    }

    private static func performVoid(
        method: String,
        path: String,
        bodyData: Data? = nil,
        token: String? = nil,
        expectedStatus: Int = 204
    ) async throws {
        let req = try makeRequest(method: method, path: path, bodyData: bodyData, token: token)
        let (data, response) = try await session.data(for: req)
        let status = (response as? HTTPURLResponse)?.statusCode ?? 0

        if status == 401 { throw HaacpError.unauthorized }

        if status != expectedStatus {
            if let env = try? decoder.decode(APIErrorEnvelope.self, from: data) {
                throw HaacpError.api(code: env.error.code, message: env.error.message)
            }
            throw HaacpError.unknown
        }
    }

    // MARK: - Auth

    static func signup(email: String, password: String, fullName: String, organizationName: String) async throws -> AuthResponse {
        let body = try encoder.encode([
            "email": email,
            "password": password,
            "full_name": fullName,
            "organization_name": organizationName,
            "timezone": TimeZone.current.identifier
        ])
        return try await performRequest(method: "POST", path: "/api/v1/auth/signup", bodyData: body, expectedStatus: 201)
    }

    static func login(email: String, password: String) async throws -> AuthResponse {
        let body = try encoder.encode(["email": email, "password": password])
        return try await performRequest(method: "POST", path: "/api/v1/auth/login", bodyData: body)
    }

    static func refreshTokens(refreshToken: String) async throws -> TokenResponse {
        let body = try encoder.encode(["refresh_token": refreshToken])
        return try await performRequest(method: "POST", path: "/api/v1/auth/refresh", bodyData: body)
    }

    static func logout(refreshToken: String, token: String) async throws {
        let body = try encoder.encode(["refresh_token": refreshToken])
        try await performVoid(method: "POST", path: "/api/v1/auth/logout", bodyData: body, token: token)
    }

    // MARK: - Products

    static func listProducts(orgId: String, token: String) async throws -> [ProductResponse] {
        try await performRequest(method: "GET", path: "/api/v1/organizations/\(orgId)/products", token: token)
    }

    static func createProduct(orgId: String, name: String, token: String) async throws -> ProductResponse {
        let body = try encoder.encode(["name": name])
        return try await performRequest(method: "POST", path: "/api/v1/organizations/\(orgId)/products", bodyData: body, token: token, expectedStatus: 201)
    }

    static func deleteProduct(orgId: String, productId: String, token: String) async throws {
        try await performVoid(method: "DELETE", path: "/api/v1/organizations/\(orgId)/products/\(productId)", token: token)
    }

    // MARK: - Checklist Items

    static func listChecklistItems(orgId: String, productId: String, token: String) async throws -> [ChecklistItemResponse] {
        try await performRequest(method: "GET", path: "/api/v1/organizations/\(orgId)/products/\(productId)/checklist-items", token: token)
    }

    static func addChecklistItem(orgId: String, productId: String, label: String, token: String) async throws -> ChecklistItemResponse {
        let body = try encoder.encode(["label": label])
        return try await performRequest(method: "POST", path: "/api/v1/organizations/\(orgId)/products/\(productId)/checklist-items", bodyData: body, token: token, expectedStatus: 201)
    }

    static func deleteChecklistItem(orgId: String, productId: String, itemId: String, token: String) async throws {
        try await performVoid(method: "DELETE", path: "/api/v1/organizations/\(orgId)/products/\(productId)/checklist-items/\(itemId)", token: token)
    }

    // MARK: - Batches

    static func listBatches(orgId: String, productId: String, token: String) async throws -> [BatchResponse] {
        try await performRequest(method: "GET", path: "/api/v1/organizations/\(orgId)/products/\(productId)/batches", token: token)
    }

    static func recordBatch(orgId: String, productId: String, body: BatchCreateRequest, token: String) async throws -> BatchResponse {
        let bodyData = try encoder.encode(body)
        return try await performRequest(method: "POST", path: "/api/v1/organizations/\(orgId)/products/\(productId)/batches", bodyData: bodyData, token: token, expectedStatus: 201)
    }

    static func deleteBatch(orgId: String, batchId: String, token: String) async throws {
        try await performVoid(method: "DELETE", path: "/api/v1/organizations/\(orgId)/batches/\(batchId)", token: token)
    }

    static func updateBatch(orgId: String, batchId: String, body: BatchUpdateRequest, token: String) async throws -> BatchResponse {
        let bodyData = try encoder.encode(body)
        return try await performRequest(method: "PATCH", path: "/api/v1/organizations/\(orgId)/batches/\(batchId)", bodyData: bodyData, token: token)
    }

    // MARK: - Equipment

    static func listEquipment(orgId: String, token: String) async throws -> [EquipmentResponse] {
        try await performRequest(method: "GET", path: "/api/v1/organizations/\(orgId)/equipment", token: token)
    }

    static func createEquipment(orgId: String, body: EquipmentCreateRequest, token: String) async throws -> EquipmentResponse {
        let bodyData = try encoder.encode(body)
        return try await performRequest(method: "POST", path: "/api/v1/organizations/\(orgId)/equipment", bodyData: bodyData, token: token, expectedStatus: 201)
    }

    static func updateEquipment(orgId: String, equipmentId: String, body: EquipmentUpdateRequest, token: String) async throws -> EquipmentResponse {
        let bodyData = try encoder.encode(body)
        return try await performRequest(method: "PATCH", path: "/api/v1/organizations/\(orgId)/equipment/\(equipmentId)", bodyData: bodyData, token: token)
    }

    static func deleteEquipment(orgId: String, equipmentId: String, token: String) async throws {
        try await performVoid(method: "DELETE", path: "/api/v1/organizations/\(orgId)/equipment/\(equipmentId)", token: token)
    }

    // MARK: - Waste types

    static func listWasteTypes(orgId: String, token: String) async throws -> [WasteTypeResponse] {
        try await performRequest(method: "GET", path: "/api/v1/organizations/\(orgId)/waste-types", token: token)
    }

    static func createWasteType(orgId: String, body: WasteTypeCreateRequest, token: String) async throws -> WasteTypeResponse {
        let bodyData = try encoder.encode(body)
        return try await performRequest(method: "POST", path: "/api/v1/organizations/\(orgId)/waste-types", bodyData: bodyData, token: token, expectedStatus: 201)
    }

    static func updateWasteType(orgId: String, wasteTypeId: String, body: WasteTypeUpdateRequest, token: String) async throws -> WasteTypeResponse {
        let bodyData = try encoder.encode(body)
        return try await performRequest(method: "PATCH", path: "/api/v1/organizations/\(orgId)/waste-types/\(wasteTypeId)", bodyData: bodyData, token: token)
    }

    static func deleteWasteType(orgId: String, wasteTypeId: String, token: String) async throws {
        try await performVoid(method: "DELETE", path: "/api/v1/organizations/\(orgId)/waste-types/\(wasteTypeId)", token: token)
    }

    // MARK: - Medical checks

    static func listMedicalChecks(orgId: String, token: String) async throws -> [MedicalCheckResponse] {
        try await performRequest(method: "GET", path: "/api/v1/organizations/\(orgId)/medical-checks", token: token)
    }

    static func createMedicalCheck(orgId: String, body: MedicalCheckCreateRequest, token: String) async throws -> MedicalCheckResponse {
        let bodyData = try encoder.encode(body)
        return try await performRequest(method: "POST", path: "/api/v1/organizations/\(orgId)/medical-checks", bodyData: bodyData, token: token, expectedStatus: 201)
    }

    static func updateMedicalCheck(orgId: String, checkId: String, body: MedicalCheckUpdateRequest, token: String) async throws -> MedicalCheckResponse {
        let bodyData = try encoder.encode(body)
        return try await performRequest(method: "PATCH", path: "/api/v1/organizations/\(orgId)/medical-checks/\(checkId)", bodyData: bodyData, token: token)
    }

    static func deleteMedicalCheck(orgId: String, checkId: String, token: String) async throws {
        try await performVoid(method: "DELETE", path: "/api/v1/organizations/\(orgId)/medical-checks/\(checkId)", token: token)
    }

    // MARK: - Allergens

    static func listAllergens(orgId: String, token: String) async throws -> [AllergenStatusResponse] {
        try await performRequest(method: "GET", path: "/api/v1/organizations/\(orgId)/allergens", token: token)
    }

    static func updateAllergenPresence(orgId: String, allergenId: String, present: Bool, token: String) async throws -> AllergenStatusResponse {
        let bodyData = try encoder.encode(AllergenPresenceUpdateRequest(present: present))
        return try await performRequest(method: "PATCH", path: "/api/v1/organizations/\(orgId)/allergens/\(allergenId)", bodyData: bodyData, token: token)
    }

    // MARK: - Chemicals

    static func listChemicals(orgId: String, token: String) async throws -> [ChemicalResponse] {
        try await performRequest(method: "GET", path: "/api/v1/organizations/\(orgId)/chemicals", token: token)
    }

    static func createChemical(orgId: String, body: ChemicalCreateRequest, token: String) async throws -> ChemicalResponse {
        let bodyData = try encoder.encode(body)
        return try await performRequest(method: "POST", path: "/api/v1/organizations/\(orgId)/chemicals", bodyData: bodyData, token: token, expectedStatus: 201)
    }

    static func updateChemical(orgId: String, chemicalId: String, body: ChemicalUpdateRequest, token: String) async throws -> ChemicalResponse {
        let bodyData = try encoder.encode(body)
        return try await performRequest(method: "PATCH", path: "/api/v1/organizations/\(orgId)/chemicals/\(chemicalId)", bodyData: bodyData, token: token)
    }

    static func deleteChemical(orgId: String, chemicalId: String, token: String) async throws {
        try await performVoid(method: "DELETE", path: "/api/v1/organizations/\(orgId)/chemicals/\(chemicalId)", token: token)
    }

    // MARK: - Event Log

    static func listEventLogTypes(orgId: String, token: String) async throws -> [EventLogTypeResponse] {
        try await performRequest(method: "GET", path: "/api/v1/organizations/\(orgId)/event-log-types", token: token)
    }

    static func listEventEntries(orgId: String, typeId: String, token: String) async throws -> [EventEntryResponse] {
        try await performRequest(method: "GET", path: "/api/v1/organizations/\(orgId)/event-log-types/\(typeId)/entries", token: token)
    }

    static func createEventEntry(orgId: String, typeId: String, body: EventEntryCreateRequest, token: String) async throws -> EventEntryResponse {
        let bodyData = try encoder.encode(body)
        return try await performRequest(method: "POST", path: "/api/v1/organizations/\(orgId)/event-log-types/\(typeId)/entries", bodyData: bodyData, token: token, expectedStatus: 201)
    }

    static func deleteEventEntry(orgId: String, entryId: String, token: String) async throws {
        try await performVoid(method: "DELETE", path: "/api/v1/organizations/\(orgId)/event-entries/\(entryId)", token: token)
    }

    // MARK: - Dashboard

    static func getDashboard(orgId: String, token: String) async throws -> DashboardResponse {
        try await performRequest(method: "GET", path: "/api/v1/organizations/\(orgId)/dashboard", token: token)
    }

    // MARK: - Controls

    static func listControlChecklistItems(orgId: String, period: ControlPeriod, token: String) async throws -> [ControlChecklistItemResponse] {
        try await performRequest(method: "GET", path: "/api/v1/organizations/\(orgId)/controls/\(period.rawValue)/checklist-items", token: token)
    }

    static func addControlChecklistItem(orgId: String, period: ControlPeriod, label: String, token: String) async throws -> ControlChecklistItemResponse {
        let body = try encoder.encode(ControlChecklistItemCreateRequest(label: label))
        return try await performRequest(method: "POST", path: "/api/v1/organizations/\(orgId)/controls/\(period.rawValue)/checklist-items", bodyData: body, token: token, expectedStatus: 201)
    }

    static func deleteControlChecklistItem(orgId: String, period: ControlPeriod, itemId: String, token: String) async throws {
        try await performVoid(method: "DELETE", path: "/api/v1/organizations/\(orgId)/controls/\(period.rawValue)/checklist-items/\(itemId)", token: token)
    }

    static func getCurrentControl(orgId: String, period: ControlPeriod, token: String) async throws -> ControlRecordResponse {
        try await performRequest(method: "GET", path: "/api/v1/organizations/\(orgId)/controls/\(period.rawValue)/current", token: token)
    }

    static func upsertCurrentControl(orgId: String, period: ControlPeriod, body: ControlRecordUpsertRequest, token: String) async throws -> ControlRecordResponse {
        let bodyData = try encoder.encode(body)
        return try await performRequest(method: "PUT", path: "/api/v1/organizations/\(orgId)/controls/\(period.rawValue)/current", bodyData: bodyData, token: token)
    }

    static func listControlRecords(orgId: String, period: ControlPeriod, token: String) async throws -> [ControlRecordResponse] {
        try await performRequest(method: "GET", path: "/api/v1/organizations/\(orgId)/controls/\(period.rawValue)/records", token: token)
    }

    static func patchControlRecord(orgId: String, recordId: String, body: ControlRecordUpsertRequest, token: String) async throws -> ControlRecordResponse {
        let bodyData = try encoder.encode(body)
        return try await performRequest(method: "PATCH", path: "/api/v1/organizations/\(orgId)/control-records/\(recordId)", bodyData: bodyData, token: token)
    }

    static func deleteControlRecord(orgId: String, recordId: String, token: String) async throws {
        try await performVoid(method: "DELETE", path: "/api/v1/organizations/\(orgId)/control-records/\(recordId)", token: token)
    }
}
