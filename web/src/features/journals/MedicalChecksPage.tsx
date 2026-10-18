import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { dashboardKeys } from '../../api/dashboard'
import { createMedicalCheck, deleteMedicalCheck, referenceKeys, updateMedicalCheck } from '../../api/references'
import type { MedicalCheck } from '../../api/types'
import type { Session } from '../../auth/session'
import { PanelState } from '../../components/PanelState'
import { uk } from '../../i18n/uk'
import { formatShortDate } from '../../lib/dates'
import { routes } from '../../routes'
import { medicalState } from './medical'
import { useMedicalChecks } from './queries'
import { canManage } from './helpers'
import { FormError, InlineDelete, JournalLayout, Section, Tag, WithToday } from './ui'

const t = uk.journals
const tm = t.medical

export function MedicalChecksPage({ session }: { session: Session }) {
  return (
    <JournalLayout backTo={routes.journalGroup('planned')} kicker={tm.kicker} title={t.name.medical}>
      <p className="jpage-intro">{tm.intro}</p>
      <WithToday orgId={session.organization_id}>{(today) => <MedicalChecks session={session} today={today} />}</WithToday>
    </JournalLayout>
  )
}

function useInvalidate(orgId: string) {
  const queryClient = useQueryClient()
  return () => {
    void queryClient.invalidateQueries({ queryKey: referenceKeys.medicalChecks(orgId) })
    // Overdue / due-soon checkups feed the dashboard's attention list.
    void queryClient.invalidateQueries({ queryKey: dashboardKeys.all(orgId) })
  }
}

function MedicalChecks({ session, today }: { session: Session; today: string }) {
  const orgId = session.organization_id
  const manager = canManage(session)
  const checks = useMedicalChecks(orgId)
  // Most urgent first; ISO dates sort correctly as strings.
  const sorted = [...(checks.data ?? [])].sort((a, b) => a.next_check_date.localeCompare(b.next_check_date))

  return (
    <>
      {manager && (
        <Section title={tm.add}>
          <MedicalForm orgId={orgId} today={today} />
        </Section>
      )}
      <Section title={t.name.medical} aside={checks.data && <span className="caps jsection__title">{checks.data.length}</span>}>
        {!manager && <p className="jsection__note">{t.managersOnly}</p>}
        {checks.data === undefined ? (
          <div className="jsection__pad">
            <PanelState error={checks.isError ? checks.error : undefined} onRetry={() => void checks.refetch()} />
          </div>
        ) : sorted.length === 0 ? (
          <p className="jsection__empty">{tm.none}</p>
        ) : (
          <ul className="register">
            {sorted.map((check) => (
              <MedicalRow key={check.id} orgId={orgId} check={check} today={today} manager={manager} />
            ))}
          </ul>
        )}
      </Section>
    </>
  )
}

interface MedicalFormProps {
  orgId: string
  today: string
  initial?: MedicalCheck
  onDone?: () => void
}

/** Add a new employee record, or (with `initial`) update the name / next checkup date. */
function MedicalForm({ orgId, today, initial, onDone }: MedicalFormProps) {
  const invalidate = useInvalidate(orgId)
  const [name, setName] = useState(initial?.employee_name ?? '')
  const [date, setDate] = useState(initial?.next_check_date ?? today)
  const valid = name.trim().length > 0 && date !== ''

  const mutation = useMutation({
    mutationFn: () => {
      const body = { employee_name: name.trim(), next_check_date: date }
      return initial ? updateMedicalCheck(orgId, initial.id, body) : createMedicalCheck(orgId, body)
    },
    onSuccess: () => {
      invalidate()
      if (!initial) {
        setName('')
        setDate(today)
      }
      onDone?.()
    },
  })

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (valid && !mutation.isPending) mutation.mutate()
  }

  return (
    <form className={initial ? 'jform jform--tight' : 'jform'} onSubmit={submit}>
      <label className="field">
        <span className="field__label caps">
          {tm.employee} <span className="req">*</span>
        </span>
        <input className="input" value={name} maxLength={200} onChange={(e) => setName(e.target.value)} placeholder={tm.employeePlaceholder} />
      </label>
      <label className="field">
        <span className="field__label caps">
          {tm.nextDate} <span className="req">*</span>
        </span>
        <input className="input" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
      </label>
      <div className="jform__actions">
        <button className="btn btn--primary caps" type="submit" disabled={!valid || mutation.isPending}>
          {mutation.isPending ? t.saving : initial ? t.save : `+ ${t.add}`}
        </button>
        {onDone && (
          <button className="btn btn--secondary caps" type="button" onClick={onDone} disabled={mutation.isPending}>
            {uk.common.cancel}
          </button>
        )}
      </div>
      <div className="jform__wide">
        <FormError error={mutation.error} />
      </div>
    </form>
  )
}

function MedicalRow({ orgId, check, today, manager }: { orgId: string; check: MedicalCheck; today: string; manager: boolean }) {
  const invalidate = useInvalidate(orgId)
  const [editing, setEditing] = useState(false)
  const remove = useMutation({ mutationFn: () => deleteMedicalCheck(orgId, check.id), onSuccess: invalidate })
  const state = medicalState(check.next_check_date, today)

  if (editing) {
    return (
      <li className="reg-row reg-row--editing">
        <MedicalForm orgId={orgId} today={today} initial={check} onDone={() => setEditing(false)} />
      </li>
    )
  }

  return (
    <li className={`reg-row${state.kind === 'overdue' ? ' reg-row--crit' : ''}`}>
      <p className="reg-row__date">{formatShortDate(check.next_check_date)}</p>
      <div className="reg-row__main">
        <p className="reg-row__title">{check.employee_name}</p>
        <p className="reg-row__meta caps">{tm.nextDate}</p>
      </div>
      <div className="reg-row__side">
        {state.kind === 'overdue' && <Tag tone="crit">{tm.overdue(state.days)}</Tag>}
        {state.kind === 'today' && <Tag tone="warn">{tm.dueToday}</Tag>}
        {state.kind === 'soon' && <Tag tone="warn">{tm.soon(state.days)}</Tag>}
        {state.kind === 'ok' && <Tag tone="muted">{tm.ok}</Tag>}
        {manager && (
          <span className="reg-row__tools">
            <button className="link-btn caps" type="button" onClick={() => setEditing(true)}>
              {t.edit}
            </button>
            <InlineDelete onConfirm={() => remove.mutate()} pending={remove.isPending} error={remove.error} />
          </span>
        )}
      </div>
    </li>
  )
}
