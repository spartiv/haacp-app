// Which cadence tab each journal belongs to. The backend owns the journals and
// their rules; this only decides where the hub lists them.

export const JOURNAL_GROUPS = ['daily', 'periodic', 'planned', 'events', 'references'] as const
export type JournalGroup = (typeof JOURNAL_GROUPS)[number]

export function isJournalGroup(value: string | null): value is JournalGroup {
  return value !== null && (JOURNAL_GROUPS as readonly string[]).includes(value)
}

/** Built-in event log types by key. Unknown future keys fall back to "events". */
const EVENT_LOG_GROUP: Record<string, JournalGroup> = {
  water: 'periodic',
  filters: 'periodic',
  eq: 'periodic',
  disinfect: 'periodic',
  pests: 'periodic',
  deratization: 'periodic',
  glass: 'events',
  visitors: 'events',
  chemBriefing: 'events',
}

export function eventLogGroup(typeKey: string): JournalGroup {
  return EVENT_LOG_GROUP[typeKey] ?? 'events'
}

/** Event logs that record work on a piece of equipment: the form offers the equipment list. */
export const EQUIPMENT_LINKED_LOGS: ReadonlySet<string> = new Set(['filters', 'eq'])

/** Monograms for journals that are not event logs (event logs carry their own from the API). */
export const MONOGRAM = {
  daily: 'ЩК',
  monthly: 'МК',
  batches: 'КП',
  medical: 'МО',
  equipment: 'ОБ',
  chemicals: 'ХЗ',
} as const
