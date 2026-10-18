// Readable aliases over the generated OpenAPI types.
// Do not edit schema.gen.ts by hand — run `npm run gen:api` after the backend changes.
// Field names stay snake_case to match the API exactly.
import type { components, paths } from './schema.gen'

type Schemas = components['schemas']

export type { components, paths }

// Auth
export type AuthResponse = Schemas['AuthResponse']
export type TokenResponse = Schemas['TokenResponse']
export type LoginRequest = Schemas['LoginRequest']
export type SignupRequest = Schemas['SignupRequest']
export type UserResponse = Schemas['UserResponse']

// Me
export type MyOrganization = Schemas['MyOrganizationResponse']

// Dashboard
export type DashboardResponse = Schemas['DashboardResponse']
export type AttentionItem = Schemas['AttentionItemResponse']

// Event logs (glass breakage, maintenance, ...)
export type EventLogType = Schemas['EventLogTypeResponse']
export type EventEntry = Schemas['EventEntryResponse']
export type MedicalCheck = Schemas['MedicalCheckResponse']

// Daily / monthly controls
export type ControlPeriod = Schemas['ControlPeriod']
export type ControlChecklistItem = Schemas['ControlChecklistItemResponse']
export type ControlItemType = Schemas['ControlItemType']
export type ControlChecklistItemCreate = Schemas['ControlChecklistItemCreateRequest']
export type ControlChecklistItemUpdate = Schemas['ControlChecklistItemUpdateRequest']
export type ControlRecord = Schemas['ControlRecordResponse']
export type ControlAnswer = Schemas['ControlAnswerResponse']
export type ControlAnswerInput = Schemas['ControlAnswerInput']
export type ControlRecordUpsert = Schemas['ControlRecordUpsertRequest']
export type ControlRecordHistory = Schemas['ControlRecordHistoryResponse']
export type ControlStatus = Schemas['ControlStatusResponse']

// Per-item sheet workflow + audit log
export type ControlItemStatus = Schemas['ControlItemStatus']
export type ControlRecordStatus = Schemas['ControlRecordStatus']
export type ControlAuditEventType = Schemas['ControlAuditEventType']
export type ControlSheet = Schemas['ControlSheetResponse']
export type SheetItem = Schemas['SheetItemResponse']
export type ItemCheckRequest = Schemas['ItemCheckRequest']
export type AuditEvent = Schemas['AuditEventResponse']
export type AuditEventPage = Schemas['AuditEventPageResponse']
export type UserRef = Schemas['UserRefResponse']

// Event log entries: create body (payload shape depends on the type's log_schema)
export type EventLogSchema = Schemas['EventLogSchema']
export type EventEntryCreate = Schemas['EventEntryCreateRequest']

// Batches (per product)
export type Product = Schemas['ProductResponse']
export type ProductChecklistItem = Schemas['ChecklistItemResponse']
export type Batch = Schemas['BatchResponse']
export type BatchCreate = Schemas['BatchCreateRequest']

// References
export type Equipment = Schemas['EquipmentResponse']
export type EquipmentType = Schemas['EquipmentType']
export type EquipmentCreate = Schemas['EquipmentCreateRequest']
export type EquipmentUpdate = Schemas['EquipmentUpdateRequest']
export type Chemical = Schemas['ChemicalResponse']
export type ChemicalCategory = Schemas['ChemicalCategory']
export type ChemicalCreate = Schemas['ChemicalCreateRequest']
export type ChemicalUpdate = Schemas['ChemicalUpdateRequest']
export type MedicalCheckCreate = Schemas['MedicalCheckCreateRequest']
export type MedicalCheckUpdate = Schemas['MedicalCheckUpdateRequest']
export type Attachment = Schemas['AttachmentResponse']

// Team
export type Member = Schemas['MemberResponse']
