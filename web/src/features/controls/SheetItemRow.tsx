import { useMutation } from '@tanstack/react-query'
import { useId, useState, type FormEvent } from 'react'
import { ApiError } from '../../api/client'
import { checkItem } from '../../api/controls'
import type { ControlPeriod, ControlRecordStatus, ControlSheet, ItemCheckRequest, SheetItem } from '../../api/types'
import { PresetChips } from '../../components/PresetChips'
import { StatusBadge } from '../../components/StatusBadge'
import { errorMessage, uk } from '../../i18n/uk'
import { formatTime } from '../../lib/dates'
import { formatRange, formatReading, isWithinRange, parseReading, readingInputText } from '../../lib/readings'

const t = uk.controls

const MIN_TEXT = 3 // matches the backend's minimum for corrective actions and amendment reasons

type CheckStatus = 'pass' | 'deviation'

/** What the open editor will save: a Yes/No status, or a reading (the server judges it). */
type Pending = { kind: 'status'; status: CheckStatus } | { kind: 'reading'; value: number; status: CheckStatus }

interface SheetItemRowProps {
  orgId: string
  period: ControlPeriod
  periodDate: string
  item: SheetItem
  index: number
  recordStatus: ControlRecordStatus | null
  /** Who is doing the check on this device ("Виконавець"). */
  performerId: string
  onUpdated: (sheet: ControlSheet) => void
}

export function SheetItemRow(props: SheetItemRowProps) {
  const { orgId, period, periodDate, item, index, recordStatus, performerId, onUpdated } = props
  const submitted = recordStatus === 'submitted'
  const numeric = item.item_type === 'numeric'
  // Non-null while the editor (corrective action / amendment reason) is open.
  const [pending, setPending] = useState<Pending | null>(null)
  const [correctiveAction, setCorrectiveAction] = useState('')
  const [amendmentReason, setAmendmentReason] = useState('')
  // Typed reading; null = show the saved value.
  const [draft, setDraft] = useState<string | null>(null)
  const [inputError, setInputError] = useState<string | null>(null)
  const fieldId = useId()

  const mutation = useMutation({
    mutationFn: (body: ItemCheckRequest) =>
      checkItem(orgId, period, item.control_checklist_item_id, {
        ...body,
        period_date: periodDate,
        performed_by_user_id: performerId,
      }),
    onSuccess: (sheet) => {
      setPending(null)
      setAmendmentReason('')
      setDraft(null)
      onUpdated(sheet)
    },
    onError: (error, body) => {
      // The range changed since the sheet loaded: the server says it's a deviation.
      if (error instanceof ApiError && error.code === 'corrective_action_required' && typeof body.value === 'number') {
        openEditor({ kind: 'reading', value: body.value, status: 'deviation' })
      }
    },
  })

  const openEditor = (next: Pending) => {
    setPending(next)
    setCorrectiveAction(next.status === 'deviation' ? (item.corrective_action ?? '') : '')
  }

  const choose = (status: CheckStatus) => {
    mutation.reset()
    // Draft + PASS: one tap, saved immediately (fast on the shop floor).
    if (!submitted && status === 'pass') {
      setPending(null)
      if (item.status !== 'pass' || item.performed_by?.id !== performerId) mutation.mutate({ status: 'pass' })
      return
    }
    // Deviation (always) and any change after submission: open the editor.
    openEditor({ kind: 'status', status })
  }

  const record = (event: FormEvent) => {
    event.preventDefault()
    mutation.reset()
    const value = parseReading(draft ?? readingInputText(item.value))
    if (value === null) {
      setInputError(t.reading.invalid)
      return
    }
    setInputError(null)
    const within = isWithinRange(value, item.min_value, item.max_value)
    if (!submitted && within) {
      setPending(null)
      if (value !== item.value || item.status !== 'pass' || item.performed_by?.id !== performerId) mutation.mutate({ value })
      return
    }
    // Out of range needs a corrective action; after submission any change needs a reason.
    openEditor({ kind: 'reading', value, status: within ? 'pass' : 'deviation' })
  }

  const cancel = () => {
    setPending(null)
    setAmendmentReason('')
    mutation.reset()
  }

  const isDeviation = pending?.status === 'deviation'
  const actionValid = !isDeviation || correctiveAction.trim().length >= MIN_TEXT
  const reasonValid = !submitted || amendmentReason.trim().length >= MIN_TEXT
  const canSave = pending !== null && actionValid && reasonValid && !mutation.isPending

  const save = () => {
    if (!canSave || pending === null) return
    mutation.mutate({
      ...(pending.kind === 'reading' ? { value: pending.value } : { status: pending.status }),
      corrective_action: isDeviation ? correctiveAction : null,
      amendment_reason: submitted ? amendmentReason : null,
    })
  }

  const shownStatus: CheckStatus | null =
    pending?.kind === 'status' ? pending.status : item.status === 'pending' ? null : item.status
  const number = String(index + 1).padStart(2, '0')
  const labelId = `${fieldId}-label`
  const range = numeric ? formatRange(item.min_value, item.max_value, item.unit) : ''

  return (
    <li className={`sheet-item sheet-item--${item.status}${pending ? ' sheet-item--editing' : ''}`}>
      <div className="sheet-item__main">
        <span className="sheet-item__num" aria-hidden="true">
          {number}
        </span>
        <div className="sheet-item__body">
          <p className="sheet-item__label" id={labelId}>
            {item.label}
          </p>
          {numeric && <p className="sheet-item__range caps">{t.reading.range(range)}</p>}
          <p className="sheet-item__meta caps">
            {item.checked_by && item.checked_at ? (
              <>
                {t.checkedBy((item.performed_by ?? item.checked_by).full_name, formatTime(item.checked_at))}
                {item.performed_by && item.performed_by.id !== item.checked_by.id && (
                  <span className="sheet-item__via"> / {uk.performer.via(item.checked_by.full_name)}</span>
                )}
              </>
            ) : (
              t.notChecked
            )}
          </p>
          {item.status === 'deviation' && item.corrective_action && pending === null && (
            <p className="sheet-item__action">
              <span className="caps">{t.correctiveAction}:</span> {item.corrective_action}
            </p>
          )}
        </div>

        <div className="sheet-item__controls">
          <StatusBadge status={item.status} />
          {numeric ? (
            <form className="reading" onSubmit={record} noValidate>
              {item.value !== null && (
                <p className={`reading__value${item.status === 'deviation' ? ' reading__value--bad' : ''}`}>
                  {formatReading(item.value, item.unit)}
                </p>
              )}
              <div className="reading__entry">
                <input
                  className="reading__input"
                  type="text"
                  inputMode="decimal"
                  autoComplete="off"
                  aria-labelledby={labelId}
                  aria-describedby={inputError ? `${fieldId}-reading-error` : undefined}
                  aria-invalid={inputError !== null}
                  placeholder={t.reading.placeholder}
                  value={draft ?? readingInputText(item.value)}
                  onChange={(e) => {
                    setDraft(e.target.value)
                    setInputError(null)
                  }}
                  disabled={mutation.isPending}
                />
                <span className="reading__unit">{item.unit}</span>
                <button className="toggle caps" type="submit" disabled={mutation.isPending}>
                  {t.reading.record}
                </button>
              </div>
              {inputError && (
                <p className="reading__error" id={`${fieldId}-reading-error`} role="alert">
                  {inputError}
                </p>
              )}
            </form>
          ) : (
            <div className="toggle-group" role="group" aria-labelledby={labelId}>
              {(['pass', 'deviation'] as const).map((status) => (
                <button
                  key={status}
                  type="button"
                  className={`toggle caps${shownStatus === status ? ' toggle--on' : ''}`}
                  aria-pressed={shownStatus === status}
                  disabled={mutation.isPending}
                  onClick={() => choose(status)}
                >
                  {uk.status[status]}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {pending !== null && (
        <form
          className="item-editor"
          onSubmit={(event) => {
            event.preventDefault()
            save()
          }}
        >
          {pending.kind === 'reading' && (
            <p className={`item-editor__notice caps${isDeviation ? ' item-editor__notice--crit' : ''}`}>
              {isDeviation
                ? t.reading.outOfRange(formatReading(pending.value, item.unit), range)
                : t.reading.newValue(formatReading(pending.value, item.unit))}
            </p>
          )}
          {submitted && <p className="item-editor__notice caps">{t.amendmentNotice}</p>}

          {isDeviation && (
            <div className="item-editor__field">
              <label className="item-editor__label caps" htmlFor={`${fieldId}-action`}>
                {t.correctiveAction} <span className="req">{t.required}</span>
              </label>
              <textarea
                id={`${fieldId}-action`}
                className="item-editor__input"
                rows={3}
                maxLength={2000}
                required
                autoFocus
                value={correctiveAction}
                onChange={(e) => setCorrectiveAction(e.target.value)}
                placeholder={t.actionPlaceholder}
              />
              <PresetChips value={correctiveAction} onChange={setCorrectiveAction} />
            </div>
          )}

          {submitted && (
            <div className="item-editor__field">
              <label className="item-editor__label caps" htmlFor={`${fieldId}-reason`}>
                {t.amendmentReason} <span className="req">{t.required}</span>
              </label>
              <textarea
                id={`${fieldId}-reason`}
                className="item-editor__input"
                rows={2}
                maxLength={1000}
                required
                autoFocus={!isDeviation}
                value={amendmentReason}
                onChange={(e) => setAmendmentReason(e.target.value)}
                placeholder={t.reasonPlaceholder}
              />
            </div>
          )}

          <div className="item-editor__actions">
            <button className="btn btn--primary caps" type="submit" disabled={!canSave}>
              {mutation.isPending ? t.saving : submitted ? t.saveAmendment : isDeviation ? t.saveDeviation : t.save}
            </button>
            <button className="btn btn--secondary caps" type="button" onClick={cancel} disabled={mutation.isPending}>
              {uk.common.cancel}
            </button>
          </div>
        </form>
      )}

      {mutation.isError && !(pending !== null && mutation.error instanceof ApiError && mutation.error.code === 'corrective_action_required') && (
        <p className="item-error" role="alert">
          {mutation.error ? errorMessage(mutation.error) : t.saveFailed}
        </p>
      )}
    </li>
  )
}
