import type { ControlItemStatus } from '../api/types'
import './ProgressCells.css'

interface ProgressCellsProps {
  statuses: readonly { id: string; status: ControlItemStatus }[]
  size?: 'sm' | 'lg'
}

/** One cell per checklist item: dotted = pending, solid ink = pass, red hatch = deviation. */
export function ProgressCells({ statuses, size = 'sm' }: ProgressCellsProps) {
  return (
    <div className={`progress-cells progress-cells--${size}`} aria-hidden="true">
      {statuses.map(({ id, status }) => (
        <span key={id} className={`progress-cell progress-cell--${status}`} />
      ))}
    </div>
  )
}
