import { useState } from 'react'
import type { Session } from '../../auth/session'
import { uk } from '../../i18n/uk'

const t = uk.journals

/** Owners and managers edit configuration (references, checklists); staff record day-to-day data. */
export function canManage(session: Session): boolean {
  return session.role === 'owner' || session.role === 'manager'
}

export const YES_NO = [
  { value: 'yes', label: t.yes },
  { value: 'no', label: t.no, bad: true },
] as const

/** Client-side paging for long registers: first N rows, then "show N more". */
export function useShowMore<T>(items: readonly T[] | undefined, step = 30) {
  const [limit, setLimit] = useState(step)
  const all = items ?? []
  return {
    visible: all.slice(0, limit),
    remaining: Math.max(0, all.length - limit),
    more: () => setLimit((current) => current + step),
  }
}

export const MIN_TEXT = 3 // matches the backend's minimum for corrective actions and reasons
