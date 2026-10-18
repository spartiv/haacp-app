import { apiRequest } from './client'
import type {
  AuditEventPage,
  ControlChecklistItem,
  ControlChecklistItemCreate,
  ControlChecklistItemUpdate,
  ControlPeriod,
  ControlSheet,
  ItemCheckRequest,
} from './types'

const orgBase = (organizationId: string) => `/api/v1/organizations/${encodeURIComponent(organizationId)}`

export const controlKeys = {
  /** Everything about controls for one organization (sheets, checklists, audit). */
  all: (organizationId: string) => ['controls', organizationId] as const,
  checklist: (organizationId: string, period: ControlPeriod) => ['controls', organizationId, 'checklist', period] as const,
  sheet: (organizationId: string, period: ControlPeriod, date: string) =>
    ['controls', organizationId, 'sheet', period, date] as const,
  audit: (organizationId: string, recordId: string) => ['controls', organizationId, 'audit', recordId] as const,
  auditAll: (organizationId: string) => ['controls', organizationId, 'audit'] as const,
  /** The organization's current date, in its own timezone (from the server). */
  today: (organizationId: string) => ['controls', organizationId, 'today'] as const,
}

export function getSheet(
  organizationId: string,
  period: ControlPeriod,
  date: string | undefined,
  signal?: AbortSignal,
): Promise<ControlSheet> {
  // No date = the current period in the organization's timezone.
  const query = date === undefined ? '' : `?${new URLSearchParams({ date })}`
  return apiRequest<ControlSheet>(`${orgBase(organizationId)}/controls/${period}/sheet${query}`, { signal })
}

export function checkItem(
  organizationId: string,
  period: ControlPeriod,
  itemId: string,
  body: ItemCheckRequest,
): Promise<ControlSheet> {
  return apiRequest<ControlSheet>(
    `${orgBase(organizationId)}/controls/${period}/items/${encodeURIComponent(itemId)}/check`,
    { method: 'POST', body },
  )
}

export function submitRecord(organizationId: string, recordId: string): Promise<ControlSheet> {
  return apiRequest<ControlSheet>(`${orgBase(organizationId)}/control-records/${encodeURIComponent(recordId)}/submit`, {
    method: 'POST',
  })
}

export function listAuditEvents(
  organizationId: string,
  recordId: string,
  cursor: string | undefined,
  signal?: AbortSignal,
): Promise<AuditEventPage> {
  const query = new URLSearchParams({ limit: '50' })
  if (cursor !== undefined) query.set('cursor', cursor)
  return apiRequest<AuditEventPage>(
    `${orgBase(organizationId)}/control-records/${encodeURIComponent(recordId)}/audit-events?${query}`,
    { signal },
  )
}

// ---- Checklist configuration (owners / managers) ----

export function listChecklistItems(
  organizationId: string,
  period: ControlPeriod,
  signal?: AbortSignal,
): Promise<ControlChecklistItem[]> {
  return apiRequest<ControlChecklistItem[]>(`${orgBase(organizationId)}/controls/${period}/checklist-items`, { signal })
}

export function createChecklistItem(
  organizationId: string,
  period: ControlPeriod,
  body: ControlChecklistItemCreate,
): Promise<ControlChecklistItem> {
  return apiRequest<ControlChecklistItem>(`${orgBase(organizationId)}/controls/${period}/checklist-items`, {
    method: 'POST',
    body,
  })
}

export function updateChecklistItem(
  organizationId: string,
  period: ControlPeriod,
  itemId: string,
  body: ControlChecklistItemUpdate,
): Promise<ControlChecklistItem> {
  return apiRequest<ControlChecklistItem>(
    `${orgBase(organizationId)}/controls/${period}/checklist-items/${encodeURIComponent(itemId)}`,
    { method: 'PATCH', body },
  )
}

export function deleteChecklistItem(organizationId: string, period: ControlPeriod, itemId: string): Promise<void> {
  return apiRequest<void>(
    `${orgBase(organizationId)}/controls/${period}/checklist-items/${encodeURIComponent(itemId)}`,
    { method: 'DELETE' },
  )
}
