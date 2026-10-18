import { daysBetween } from '../../lib/dates'
import { MEDICAL_WARNING_DAYS } from '../dashboard/constants'

export type MedicalState =
  | { kind: 'overdue'; days: number }
  | { kind: 'today' }
  | { kind: 'soon'; days: number }
  | { kind: 'ok' }

/** Same thresholds as the backend's dashboard attention items (overdue, within 14 days). */
export function medicalState(nextCheckDate: string, today: string): MedicalState {
  const days = daysBetween(today, nextCheckDate)
  if (days < 0) return { kind: 'overdue', days: -days }
  if (days === 0) return { kind: 'today' }
  if (days <= MEDICAL_WARNING_DAYS) return { kind: 'soon', days }
  return { kind: 'ok' }
}
