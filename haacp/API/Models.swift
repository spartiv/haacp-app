import Foundation

// MARK: - Auth

struct UserResponse: Codable, Sendable {
    let id: String
    let email: String
    let fullName: String

    enum CodingKeys: String, CodingKey {
        case id, email
        case fullName = "full_name"
    }
}

struct TokenResponse: Codable, Sendable {
    let accessToken: String
    let refreshToken: String

    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
    }
}

struct AuthResponse: Codable, Sendable {
    let user: UserResponse
    let tokens: TokenResponse
    let organizationId: String?

    enum CodingKeys: String, CodingKey {
        case user, tokens
        case organizationId = "organization_id"
    }
}

// MARK: - Products

struct ProductResponse: Codable, Identifiable, Hashable, Sendable {
    let id: String
    let organizationId: String
    let name: String

    enum CodingKeys: String, CodingKey {
        case id, name
        case organizationId = "organization_id"
    }
}

// MARK: - Checklist

struct ChecklistItemResponse: Codable, Identifiable, Sendable {
    let id: String
    let productId: String
    let label: String
    let position: Int

    enum CodingKeys: String, CodingKey {
        case id, label, position
        case productId = "product_id"
    }
}

// MARK: - Batches

struct BatchAnswerInput: Encodable, Sendable {
    let checklistItemId: String
    let answer: Bool

    enum CodingKeys: String, CodingKey {
        case answer
        case checklistItemId = "checklist_item_id"
    }
}

struct BatchAnswerResponse: Codable, Hashable, Sendable {
    let checklistItemId: String
    let answer: Bool

    enum CodingKeys: String, CodingKey {
        case answer
        case checklistItemId = "checklist_item_id"
    }
}

struct BatchCreateRequest: Encodable, Sendable {
    let number: String
    let name: String?
    let productionDate: String
    let answers: [BatchAnswerInput]
    let deviationNote: String?
    let correctiveAction: String?

    enum CodingKeys: String, CodingKey {
        case number, name, answers
        case productionDate = "production_date"
        case deviationNote = "deviation_note"
        case correctiveAction = "corrective_action"
    }
}

struct BatchResponse: Codable, Identifiable, Hashable, Sendable {
    let id: String
    let productId: String
    let number: String
    let name: String?
    let productionDate: String
    let hasDeviation: Bool
    let deviationNote: String?
    let correctiveAction: String?
    let signatoryUserId: String
    let answers: [BatchAnswerResponse]

    enum CodingKeys: String, CodingKey {
        case id, number, name, answers
        case productId = "product_id"
        case productionDate = "production_date"
        case hasDeviation = "has_deviation"
        case deviationNote = "deviation_note"
        case correctiveAction = "corrective_action"
        case signatoryUserId = "signatory_user_id"
    }
}

// MARK: - Batch update

struct BatchUpdateRequest: Encodable, Sendable {
    let number: String?
    let name: String?
    let productionDate: String?
    let answers: [BatchAnswerInput]?
    let deviationNote: String?
    let correctiveAction: String?

    enum CodingKeys: String, CodingKey {
        case number, name, answers
        case productionDate = "production_date"
        case deviationNote = "deviation_note"
        case correctiveAction = "corrective_action"
    }
}

// MARK: - Equipment

enum EquipmentType: String, Codable, Sendable, CaseIterable {
    case production
    case refrigeration
    case measuring
    case other

    var displayName: String {
        switch self {
        case .production:    return "Виробниче"
        case .refrigeration: return "Холодильне"
        case .measuring:     return "Вимірювальне"
        case .other:         return "Інше"
        }
    }
}

struct EquipmentCreateRequest: Encodable, Sendable {
    let type: EquipmentType
    let name: String
    let frequency: String
    let amount: Int
    let affectsProductSafety: Bool

    enum CodingKeys: String, CodingKey {
        case type, name, frequency, amount
        case affectsProductSafety = "affects_product_safety"
    }
}

struct EquipmentUpdateRequest: Encodable, Sendable {
    let type: EquipmentType?
    let name: String?
    let frequency: String?
    let amount: Int?
    let affectsProductSafety: Bool?

    enum CodingKeys: String, CodingKey {
        case type, name, frequency, amount
        case affectsProductSafety = "affects_product_safety"
    }
}

struct EquipmentResponse: Codable, Identifiable, Sendable {
    let id: String
    let organizationId: String
    let type: EquipmentType
    let name: String
    let frequency: String
    let amount: Int
    let affectsProductSafety: Bool
    let attachmentId: String?

    enum CodingKeys: String, CodingKey {
        case id, type, name, frequency, amount
        case organizationId = "organization_id"
        case affectsProductSafety = "affects_product_safety"
        case attachmentId = "attachment_id"
    }
}

// MARK: - Controls

enum ControlPeriod: String, Codable, Sendable {
    case daily
    case monthly
}

struct ControlAnswerInput: Encodable, Sendable {
    let controlChecklistItemId: String
    let answer: Bool

    enum CodingKeys: String, CodingKey {
        case answer
        case controlChecklistItemId = "control_checklist_item_id"
    }
}

struct ControlAnswerResponse: Codable, Sendable {
    let controlChecklistItemId: String
    let answer: Bool

    enum CodingKeys: String, CodingKey {
        case answer
        case controlChecklistItemId = "control_checklist_item_id"
    }
}

struct ControlChecklistItemCreateRequest: Encodable, Sendable {
    let label: String
}

struct ControlChecklistItemUpdateRequest: Encodable, Sendable {
    let label: String
}

struct ControlChecklistItemResponse: Codable, Identifiable, Sendable {
    let id: String
    let period: ControlPeriod
    let label: String
    let position: Int
}

struct ControlRecordUpsertRequest: Encodable, Sendable {
    let answers: [ControlAnswerInput]
    let periodDate: String?
    let note: String?

    enum CodingKeys: String, CodingKey {
        case answers, note
        case periodDate = "period_date"
    }
}

struct ControlRecordResponse: Codable, Identifiable, Sendable {
    let id: String
    let period: ControlPeriod
    let periodDate: String
    let signatoryUserId: String
    let hasDeviation: Bool
    let note: String?
    let answers: [ControlAnswerResponse]

    enum CodingKeys: String, CodingKey {
        case id, period, answers, note
        case periodDate = "period_date"
        case signatoryUserId = "signatory_user_id"
        case hasDeviation = "has_deviation"
    }
}

// MARK: - Dashboard

struct ControlStatusResponse: Codable, Sendable {
    let filled: Bool
    let hasDeviation: Bool?

    enum CodingKeys: String, CodingKey {
        case filled
        case hasDeviation = "has_deviation"
    }
}

struct AttentionItemResponse: Codable, Sendable {
    let label: String
    let severity: String
    let days: Int
}

struct DashboardResponse: Codable, Sendable {
    let dailyControl: ControlStatusResponse
    let monthlyControl: ControlStatusResponse
    let batchesThisMonth: Int
    let attentionItems: [AttentionItemResponse]

    enum CodingKeys: String, CodingKey {
        case batchesThisMonth = "batches_this_month"
        case attentionItems = "attention_items"
        case dailyControl = "daily_control"
        case monthlyControl = "monthly_control"
    }
}

// MARK: - Waste types

struct WasteTypeCreateRequest: Encodable, Sendable {
    let name: String
    let disposalMethod: String

    enum CodingKeys: String, CodingKey {
        case name
        case disposalMethod = "disposal_method"
    }
}

struct WasteTypeUpdateRequest: Encodable, Sendable {
    let name: String?
    let disposalMethod: String?

    enum CodingKeys: String, CodingKey {
        case name
        case disposalMethod = "disposal_method"
    }
}

struct WasteTypeResponse: Codable, Identifiable, Sendable {
    let id: String
    let organizationId: String
    let name: String
    let disposalMethod: String

    enum CodingKeys: String, CodingKey {
        case id, name
        case organizationId  = "organization_id"
        case disposalMethod  = "disposal_method"
    }
}

// MARK: - Medical checks

struct MedicalCheckCreateRequest: Encodable, Sendable {
    let employeeName: String
    let nextCheckDate: String

    enum CodingKeys: String, CodingKey {
        case employeeName  = "employee_name"
        case nextCheckDate = "next_check_date"
    }
}

struct MedicalCheckUpdateRequest: Encodable, Sendable {
    let employeeName: String?
    let nextCheckDate: String?

    enum CodingKeys: String, CodingKey {
        case employeeName  = "employee_name"
        case nextCheckDate = "next_check_date"
    }
}

struct MedicalCheckResponse: Codable, Identifiable, Sendable {
    let id: String
    let organizationId: String
    let employeeName: String
    let nextCheckDate: String

    enum CodingKeys: String, CodingKey {
        case id
        case organizationId = "organization_id"
        case employeeName   = "employee_name"
        case nextCheckDate  = "next_check_date"
    }
}

// MARK: - Allergens

struct AllergenPresenceUpdateRequest: Encodable, Sendable {
    let present: Bool
}

struct AllergenStatusResponse: Codable, Identifiable, Sendable {
    let allergenId: String
    let name: String
    let position: Int
    let present: Bool

    var id: String { allergenId }

    enum CodingKeys: String, CodingKey {
        case allergenId = "allergen_id"
        case name, position, present
    }
}

// MARK: - Chemicals

enum ChemicalCategory: String, Codable, Sendable, CaseIterable {
    case cleaning
    case disinfecting

    var displayName: String {
        switch self {
        case .cleaning:     return "Мийний засіб"
        case .disinfecting: return "Дезінфікуючий засіб"
        }
    }
}

struct ChemicalCreateRequest: Encodable, Sendable {
    let name: String
    let category: ChemicalCategory
}

struct ChemicalUpdateRequest: Encodable, Sendable {
    let name: String?
    let category: ChemicalCategory?
}

struct ChemicalResponse: Codable, Identifiable, Sendable {
    let id: String
    let organizationId: String
    let name: String
    let category: ChemicalCategory
    let attachmentId: String?

    enum CodingKeys: String, CodingKey {
        case id, name, category
        case organizationId = "organization_id"
        case attachmentId   = "attachment_id"
    }
}

// MARK: - Event Log

enum EventLogSchema: String, Codable, Sendable {
    case standard
    case water
    case pests
}

struct EventLogTypeResponse: Codable, Identifiable, Sendable {
    let id: String
    let key: String
    let name: String
    let logSchema: EventLogSchema
    let iconLabel: String
    let position: Int

    enum CodingKeys: String, CodingKey {
        case id, key, name, position
        case logSchema = "log_schema"
        case iconLabel = "icon_label"
    }
}

struct EventPayload: Encodable, Sendable {
    let details: String?
    let params: [String]?
    let result: String?
    let detected: String?
    let actions: String?

    enum CodingKeys: String, CodingKey {
        case details, params, result, detected, actions
    }

    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        if let details  { try c.encode(details,  forKey: .details)  }
        if let params   { try c.encode(params,   forKey: .params)   }
        if let result   { try c.encode(result,   forKey: .result)   }
        if let detected { try c.encode(detected, forKey: .detected) }
        if let actions  { try c.encode(actions,  forKey: .actions)  }
    }

    static func standard(details: String) -> EventPayload {
        EventPayload(details: details, params: nil, result: nil, detected: nil, actions: nil)
    }
    static func water(params: [String], result: String) -> EventPayload {
        EventPayload(details: nil, params: params, result: result, detected: nil, actions: nil)
    }
    static func pests(detected: String, actions: String) -> EventPayload {
        EventPayload(details: nil, params: nil, result: nil, detected: detected, actions: actions)
    }
}

struct EventPayloadResponse: Decodable, Sendable {
    let details: String?
    let params: [String]?
    let result: String?
    let detected: String?
    let actions: String?
}

struct EventEntryCreateRequest: Encodable, Sendable {
    let entryDate: String
    let payload: EventPayload

    enum CodingKeys: String, CodingKey {
        case entryDate = "entry_date"
        case payload
    }
}

struct EventEntryResponse: Decodable, Identifiable, Sendable {
    let id: String
    let eventLogTypeId: String
    let entryDate: String
    let responsibleUserId: String
    let payload: EventPayloadResponse
    let hasDeviation: Bool

    enum CodingKeys: String, CodingKey {
        case id, payload
        case eventLogTypeId = "event_log_type_id"
        case entryDate = "entry_date"
        case responsibleUserId = "responsible_user_id"
        case hasDeviation = "has_deviation"
    }
}

// MARK: - Error envelope

struct APIErrorEnvelope: Decodable {
    struct Body: Decodable {
        let code: String
        let message: String
    }
    let error: Body
}

enum HaacpError: LocalizedError {
    case api(code: String, message: String)
    case unauthorized
    case unknown

    var errorDescription: String? {
        switch self {
        case .api(_, let msg): return msg
        case .unauthorized: return "Сесія закінчилась. Увійдіть знову."
        case .unknown: return "Невідома помилка"
        }
    }
}
