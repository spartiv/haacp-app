import type { ControlRecordStatus } from '../api/types'
import { uk } from '../i18n/uk'
import './RecordStamp.css'

/** Sheet lifecycle stamp: dotted = not started, dashed = draft, blue rotated = submitted (verified). */
export function RecordStamp({ status }: { status: ControlRecordStatus | null }) {
  const key = status ?? 'none'
  return <p className={`record-stamp record-stamp--${key} caps`}>{uk.record[key]}</p>
}
