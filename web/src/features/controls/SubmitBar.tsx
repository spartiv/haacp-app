import { useMutation } from '@tanstack/react-query'
import { submitRecord } from '../../api/controls'
import type { ControlSheet } from '../../api/types'
import { ProgressCells } from '../../components/ProgressCells'
import { errorMessage, uk } from '../../i18n/uk'
import { formatTime } from '../../lib/dates'

const t = uk.controls

interface SubmitBarProps {
  orgId: string
  sheet: ControlSheet
  onUpdated: (sheet: ControlSheet) => void
}

export function SubmitBar({ orgId, sheet, onUpdated }: SubmitBarProps) {
  const total = sheet.items.length
  const checked = sheet.items.filter((item) => item.status !== 'pending').length
  const deviations = sheet.items.filter((item) => item.status === 'deviation').length
  const complete = total > 0 && checked === total

  const mutation = useMutation({
    mutationFn: (recordId: string) => submitRecord(orgId, recordId),
    onSuccess: onUpdated,
  })

  const submitted = sheet.status === 'submitted'

  return (
    <div className={`submit-bar${submitted ? ' submit-bar--done' : ''}`}>
      <div className="submit-bar__progress">
        <p className="submit-bar__count caps" aria-live="polite">
          <strong>
            {checked} / {total}
          </strong>{' '}
          {t.checked(total)}
          {deviations > 0 && <span className="submit-bar__dev">{t.deviations(deviations)}</span>}
        </p>
        <ProgressCells
          statuses={sheet.items.map((item) => ({ id: item.control_checklist_item_id, status: item.status }))}
        />
      </div>

      {submitted ? (
        <p className="submit-bar__done caps">
          {uk.record.submitted}
          {sheet.submitted_by && <span> {sheet.submitted_by.full_name}</span>}
          {sheet.submitted_at && <span> / {formatTime(sheet.submitted_at)}</span>}
        </p>
      ) : (
        <div className="submit-bar__action">
          {mutation.isError && (
            <p className="submit-bar__error" role="alert">
              {mutation.error ? errorMessage(mutation.error) : t.submitFailed}
            </p>
          )}
          {!complete && <p className="submit-bar__hint">{t.checkAll}</p>}
          <button
            className="btn btn--primary btn--wide caps"
            type="button"
            disabled={!complete || sheet.record_id === null || mutation.isPending}
            onClick={() => sheet.record_id && mutation.mutate(sheet.record_id)}
          >
            {mutation.isPending ? t.submitting : t.submit}
          </button>
        </div>
      )}
    </div>
  )
}
