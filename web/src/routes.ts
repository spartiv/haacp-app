import type { JournalGroup } from './features/journals/catalog'

export const routes = {
  dashboard: '/',
  daily: '/controls/daily',
  journals: '/journals',
  monthly: '/journals/monthly',
  eventLog: (typeKey: string) => `/journals/events/${encodeURIComponent(typeKey)}`,
  batches: '/journals/batches',
  medical: '/journals/medical',
  equipment: '/journals/equipment',
  chemicals: '/journals/chemicals',
  checklistSettings: (period: 'daily' | 'monthly') => `/journals/checklists/${period}`,
  /** The hub, opened on one cadence tab. */
  journalGroup: (group: JournalGroup) => `/journals?group=${group}`,
} as const

/** Route patterns for <Route path>. */
export const routePatterns = {
  eventLog: '/journals/events/:typeKey',
  checklistSettings: '/journals/checklists/:period',
} as const
