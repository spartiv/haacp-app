import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useId, useState, type FormEvent } from 'react'
import { useParams } from 'react-router'
import { dashboardKeys } from '../../api/dashboard'
import { createEventEntry, deleteEventEntry, eventLogKeys } from '../../api/eventLogs'
import type { EventEntry, EventLogType } from '../../api/types'
import type { Session } from '../../auth/session'
import { PanelState } from '../../components/PanelState'
import { StatusBadge } from '../../components/StatusBadge'
import { uk } from '../../i18n/uk'
import { formatShortDate } from '../../lib/dates'
import { routes } from '../../routes'
import { EQUIPMENT_LINKED_LOGS, eventLogGroup } from './catalog'
import { useEquipment, useEventEntries, useEventLogTypes } from './queries'
import { PerformerSelect } from '../team/PerformerSelect'
import { useMemberNames, usePerformer } from '../team/performer'
import { MIN_TEXT, useShowMore, YES_NO } from './helpers'
import { Choice, FormError, InlineDelete, JournalLayout, PeopleLine, Section, ShowMore, Tag, WithToday } from './ui'

const t = uk.journals
const te = t.event

/** Fixed set accepted by the backend for water tests. */
const WATER_PARAMS = ['pH', 'Хлор', 'Мутність', 'Мікробіологія', 'Твердість'] as const

// Payload shapes per log schema (validated again on the server).
type StandardPayload = { details: string }
type WaterPayload = { params: string[]; result: 'ok' | 'deviation' }
type PestsPayload = { detected: 'yes' | 'no'; actions: string }

export function EventLogPage({ session }: { session: Session }) {
  const orgId = session.organization_id
  const { typeKey = '' } = useParams()
  const types = useEventLogTypes(orgId)
  const type = types.data?.find((candidate) => candidate.key === typeKey)
  const group = eventLogGroup(typeKey)
  const cadence = group === 'periodic' ? t.cadence.periodic : t.cadence.event

  return (
    <JournalLayout backTo={routes.journalGroup(group)} kicker={te.kicker(cadence)} title={type?.name ?? t.title}>
      {types.data === undefined ? (
        <div className="jsection">
          <div className="jsection__pad">
            <PanelState error={types.isError ? types.error : undefined} onRetry={() => void types.refetch()} />
          </div>
        </div>
      ) : type === undefined ? (
        <div className="jsection">
          <p className="jsection__empty">{t.notFound}</p>
        </div>
      ) : (
        <WithToday orgId={orgId}>{(today) => <EventLog session={session} type={type} today={today} />}</WithToday>
      )}
    </JournalLayout>
  )
}

function EventLog({ session, type, today }: { session: Session; type: EventLogType; today: string }) {
  const orgId = session.organization_id
  const entries = useEventEntries(orgId, type.id)
  const names = useMemberNames(orgId)
  const { visible, remaining, more } = useShowMore(entries.data)

  return (
    <>
      <Section title={t.newEntry}>
        <EntryForm session={session} type={type} today={today} />
      </Section>

      <Section title={t.entries} aside={entries.data && <span className="caps jsection__title">{entries.data.length}</span>}>
        {entries.data === undefined ? (
          <div className="jsection__pad">
            <PanelState error={entries.isError ? entries.error : undefined} onRetry={() => void entries.refetch()} />
          </div>
        ) : entries.data.length === 0 ? (
          <p className="jsection__empty">{t.noEntries}.</p>
        ) : (
          <>
            <ul className="register">
              {visible.map((entry) => (
                <EntryRow key={entry.id} orgId={orgId} type={type} entry={entry} names={names} />
              ))}
            </ul>
            <ShowMore remaining={remaining} onMore={more} />
          </>
        )}
      </Section>
    </>
  )
}

function EntryForm({ session, type, today }: { session: Session; type: EventLogType; today: string }) {
  const orgId = session.organization_id
  const performer = usePerformer(session)
  const id = useId()
  const queryClient = useQueryClient()
  const [date, setDate] = useState(today)
  const [details, setDetails] = useState('')
  const [equipment, setEquipment] = useState('')
  const [params, setParams] = useState<string[]>([])
  const [result, setResult] = useState<'ok' | 'deviation' | null>(null)
  const [detected, setDetected] = useState<'yes' | 'no' | null>(null)
  const [actions, setActions] = useState('')
  const [touched, setTouched] = useState(false)
  const [savedAt, setSavedAt] = useState<number | null>(null)

  const linksEquipment = type.log_schema === 'standard' && EQUIPMENT_LINKED_LOGS.has(type.key)
  const equipmentList = useEquipment(orgId)

  const problem = validate()
  function validate(): string | null {
    if (type.log_schema === 'standard') return details.trim().length >= MIN_TEXT ? null : te.needDetails
    if (type.log_schema === 'water') {
      if (params.length === 0) return te.needParams
      return result === null ? te.needResult : null
    }
    if (detected === null) return te.needDetected
    return detected === 'yes' && actions.trim().length < MIN_TEXT ? te.needActions : null
  }

  const mutation = useMutation({
    mutationFn: () =>
      createEventEntry(orgId, type.id, {
        entry_date: date,
        payload: buildPayload(),
        performed_by_user_id: performer.performerId,
      }),
    onSuccess: () => {
      setDetails('')
      setEquipment('')
      setParams([])
      setResult(null)
      setDetected(null)
      setActions('')
      setTouched(false)
      setSavedAt(Date.now())
      void queryClient.invalidateQueries({ queryKey: eventLogKeys.entries(orgId, type.id) })
      void queryClient.invalidateQueries({ queryKey: dashboardKeys.all(orgId) })
    },
  })

  function buildPayload(): StandardPayload | WaterPayload | PestsPayload {
    if (type.log_schema === 'water') return { params, result: result ?? 'ok' }
    if (type.log_schema === 'pests') return { detected: detected ?? 'no', actions: actions.trim() }
    const text = details.trim()
    return { details: equipment ? `${te.equipment}: ${equipment}. ${text}` : text }
  }

  const submit = (event: FormEvent) => {
    event.preventDefault()
    setTouched(true)
    setSavedAt(null)
    if (problem === null && !mutation.isPending) mutation.mutate()
  }

  const toggleParam = (param: string) =>
    setParams((current) => (current.includes(param) ? current.filter((p) => p !== param) : [...current, param]))

  return (
    <form className="jform" onSubmit={submit} noValidate>
      <PerformerSelect session={session} choice={performer} wide />
      <label className="field">
        <span className="field__label caps">
          {t.date} <span className="req">*</span>
        </span>
        <input className="input" type="date" value={date} max={today} required onChange={(e) => e.target.value && setDate(e.target.value)} />
      </label>

      {linksEquipment && (
        <label className="field">
          <span className="field__label caps">{te.equipment}</span>
          <select className="input" value={equipment} onChange={(e) => setEquipment(e.target.value)}>
            <option value="">{te.equipmentNone}</option>
            {(equipmentList.data ?? []).map((item) => (
              <option key={item.id} value={item.name}>
                {item.name}
              </option>
            ))}
          </select>
        </label>
      )}

      {type.log_schema === 'standard' && (
        <label className="field jform__wide">
          <span className="field__label caps">
            {te.details} <span className="req">*</span>
          </span>
          <textarea
            className="input"
            rows={3}
            maxLength={2000}
            value={details}
            onChange={(e) => setDetails(e.target.value)}
            placeholder={te.detailsPlaceholder[type.key] ?? te.detailsPlaceholder.default}
          />
        </label>
      )}

      {type.log_schema === 'water' && (
        <>
          <div className="field jform__wide">
            <span className="field__label caps" id={`${id}-params`}>
              {te.waterParams} <span className="req">*</span>
            </span>
            <div className="pick-chips" role="group" aria-labelledby={`${id}-params`}>
              {WATER_PARAMS.map((param) => (
                <button
                  key={param}
                  type="button"
                  className="pick-chip"
                  aria-pressed={params.includes(param)}
                  onClick={() => toggleParam(param)}
                >
                  {params.includes(param) ? '✓ ' : '+ '}
                  {param}
                </button>
              ))}
            </div>
            <p className="field__hint">{te.waterParamsHint}</p>
          </div>
          <div className="field">
            <span className="field__label caps" id={`${id}-result`}>
              {te.waterResult} <span className="req">*</span>
            </span>
            <Choice
              value={result}
              labelledBy={`${id}-result`}
              onChange={setResult}
              options={[
                { value: 'ok', label: uk.status.pass },
                { value: 'deviation', label: uk.status.deviation, bad: true },
              ]}
            />
          </div>
        </>
      )}

      {type.log_schema === 'pests' && (
        <>
          <div className="field">
            <span className="field__label caps" id={`${id}-detected`}>
              {te.pestsDetected} <span className="req">*</span>
            </span>
            {/* Inverted rule: "Так" (pests found) is the deviation. */}
            <Choice
              value={detected}
              labelledBy={`${id}-detected`}
              onChange={setDetected}
              options={[
                { value: 'no', label: YES_NO[1].label },
                { value: 'yes', label: YES_NO[0].label, bad: true },
              ]}
            />
          </div>
          <label className="field jform__wide">
            <span className="field__label caps">
              {te.pestsActions} {detected === 'yes' && <span className="req">{uk.controls.required}</span>}
            </span>
            <textarea
              className="input"
              rows={3}
              maxLength={2000}
              value={actions}
              onChange={(e) => setActions(e.target.value)}
              placeholder={te.pestsActionsPlaceholder}
            />
          </label>
        </>
      )}

      <div className="jform__actions">
        <button className="btn btn--primary caps" type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? t.saving : t.save}
        </button>
        {savedAt !== null && !mutation.isPending && (
          <p className="jform__saved caps" role="status">
            {t.entrySaved}
          </p>
        )}
      </div>
      {touched && problem !== null && (
        <p className="form-error jform__wide" role="alert">
          {problem}
        </p>
      )}
      <div className="jform__wide">
        <FormError error={mutation.error} />
      </div>
    </form>
  )
}

function EntryRow(props: { orgId: string; type: EventLogType; entry: EventEntry; names: Map<string, string> }) {
  const { orgId, type, entry, names } = props
  const queryClient = useQueryClient()
  const remove = useMutation({
    mutationFn: () => deleteEventEntry(orgId, entry.id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: eventLogKeys.entries(orgId, type.id) })
      void queryClient.invalidateQueries({ queryKey: dashboardKeys.all(orgId) })
    },
  })
  const payload = entry.payload as Partial<StandardPayload & WaterPayload & PestsPayload>

  return (
    <li className={`reg-row${entry.has_deviation ? ' reg-row--crit' : ''}`}>
      <p className="reg-row__date">{formatShortDate(entry.entry_date)}</p>
      <div className="reg-row__main">
        {type.log_schema === 'standard' && <p className="reg-row__text">{payload.details || '—'}</p>}
        {type.log_schema === 'water' && <p className="reg-row__text">{(payload.params ?? []).join(', ') || '—'}</p>}
        {type.log_schema === 'pests' && (
          <>
            <p className="reg-row__title">{te.detected(payload.detected === 'yes')}</p>
            {payload.actions && <p className="reg-row__action">{payload.actions}</p>}
          </>
        )}
        <PeopleLine names={names} performedBy={entry.performed_by_user_id} savedBy={entry.responsible_user_id} />
      </div>
      <div className="reg-row__side">
        {type.log_schema === 'standard' ? (
          <Tag tone="ink">{t.recorded}</Tag>
        ) : (
          <StatusBadge status={entry.has_deviation ? 'deviation' : 'pass'} />
        )}
        <InlineDelete onConfirm={() => remove.mutate()} pending={remove.isPending} error={remove.error} />
      </div>
    </li>
  )
}
