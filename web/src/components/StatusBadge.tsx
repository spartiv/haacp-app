import type { ControlItemStatus } from '../api/types'
import { uk } from '../i18n/uk'
import './StatusBadge.css'

/** Status is always text + border pattern + color (DESIGN.md §5), never color alone. */
export function StatusBadge({ status }: { status: ControlItemStatus }) {
  return <span className={`status-badge status-badge--${status}`}>{uk.status[status]}</span>
}
