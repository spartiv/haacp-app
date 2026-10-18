import { orgBase, seg } from './base'
import { apiRequest } from './client'
import type { EventEntry, EventEntryCreate, EventLogType } from './types'

export const eventLogKeys = {
  all: (organizationId: string) => ['event-logs', organizationId] as const,
  types: (organizationId: string) => ['event-logs', organizationId, 'types'] as const,
  entries: (organizationId: string, typeId: string) => ['event-logs', organizationId, 'entries', typeId] as const,
}

export function listEventLogTypes(organizationId: string, signal?: AbortSignal): Promise<EventLogType[]> {
  return apiRequest<EventLogType[]>(`${orgBase(organizationId)}/event-log-types`, { signal })
}

/** Newest first (sorted by entry date on the server). */
export function listEventEntries(organizationId: string, typeId: string, signal?: AbortSignal): Promise<EventEntry[]> {
  return apiRequest<EventEntry[]>(`${orgBase(organizationId)}/event-log-types/${seg(typeId)}/entries`, { signal })
}

export function createEventEntry(organizationId: string, typeId: string, body: EventEntryCreate): Promise<EventEntry> {
  return apiRequest<EventEntry>(`${orgBase(organizationId)}/event-log-types/${seg(typeId)}/entries`, {
    method: 'POST',
    body,
  })
}

export function deleteEventEntry(organizationId: string, entryId: string): Promise<void> {
  return apiRequest<void>(`${orgBase(organizationId)}/event-entries/${seg(entryId)}`, { method: 'DELETE' })
}
