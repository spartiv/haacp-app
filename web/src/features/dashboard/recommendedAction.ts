import type { ControlSheet } from '../../api/types'
import { uk } from '../../i18n/uk'

const t = uk.dashboard.action

export interface RecommendedAction {
  label: string
  /** Whether the action opens the daily sheet; false = informational, no button. */
  opensSheet: boolean
  /** Primary (ink) vs. secondary (outline): the CTA is loud only when work is due. */
  urgent: boolean
}

/** The single next step for today, derived from the live daily sheet. */
export function recommendedAction(sheet: ControlSheet): RecommendedAction {
  const total = sheet.items.length
  const checked = sheet.items.filter((item) => item.status !== 'pending').length
  const deviations = sheet.items.filter((item) => item.status === 'deviation').length

  if (total === 0) return { label: t.setup, opensSheet: false, urgent: false }
  if (sheet.status === null) return { label: t.start, opensSheet: true, urgent: true }
  if (sheet.status === 'draft') {
    return checked < total
      ? { label: t.continue(checked, total), opensSheet: true, urgent: true }
      : { label: t.submit, opensSheet: true, urgent: true }
  }
  if (deviations > 0) return { label: t.reviewDeviations, opensSheet: true, urgent: false }
  return { label: t.allDone, opensSheet: false, urgent: false }
}
