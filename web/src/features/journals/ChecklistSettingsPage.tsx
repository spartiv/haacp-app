import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useId, useState, type FormEvent } from 'react'
import { Link, Navigate, useParams } from 'react-router'
import {
  controlKeys,
  createChecklistItem,
  deleteChecklistItem,
  listChecklistItems,
  updateChecklistItem,
} from '../../api/controls'
import { dashboardKeys } from '../../api/dashboard'
import type { ControlChecklistItem, ControlItemType, ControlPeriod } from '../../api/types'
import type { Session } from '../../auth/session'
import { PanelState } from '../../components/PanelState'
import { uk } from '../../i18n/uk'
import { formatRange, parseReading, readingInputText } from '../../lib/readings'
import { routes } from '../../routes'
import { canManage } from './helpers'
import { Choice, FormError, InlineDelete, JournalLayout, Section, Tag } from './ui'

const t = uk.journals
const tc = t.checklist

const PERIODS: readonly ControlPeriod[] = ['daily', 'monthly']
const UNIT_SUGGESTIONS = ['°C', '%', 'pH', 'мг/л', 'хв']

function isPeriod(value: string | undefined): value is ControlPeriod {
  return value === 'daily' || value === 'monthly'
}

/** Owners and managers configure the daily / monthly checklist: Yes/No questions and measured readings with a safe range. */
export function ChecklistSettingsPage({ session }: { session: Session }) {
  const { period } = useParams()
  if (!isPeriod(period)) return <Navigate to={routes.journals} replace />
  return <ChecklistSettings key={period} session={session} period={period} />
}

function useInvalidate(orgId: string) {
  const queryClient = useQueryClient()
  return () => {
    // Items change what every sheet shows, and the dashboard's progress.
    void queryClient.invalidateQueries({ queryKey: controlKeys.all(orgId) })
    void queryClient.invalidateQueries({ queryKey: dashboardKeys.all(orgId) })
  }
}

function ChecklistSettings({ session, period }: { session: Session; period: ControlPeriod }) {
  const orgId = session.organization_id
  const manager = canManage(session)
  const name = t.name[period]
  const items = useQuery({
    queryKey: controlKeys.checklist(orgId, period),
    queryFn: ({ signal }) => listChecklistItems(orgId, period, signal),
  })

  return (
    <JournalLayout
      backTo={period === 'daily' ? routes.daily : routes.monthly}
      kicker={tc.kicker(name)}
      title={`${tc.title}: ${name.toLowerCase()}`}
      aside={
        <nav className="pick-chips" aria-label={tc.periods}>
          {PERIODS.map((p) => (
            <Link key={p} className="pick-chip pick-chip--link" to={routes.checklistSettings(p)} aria-current={p === period ? 'page' : undefined}>
              {t.name[p]}
            </Link>
          ))}
        </nav>
      }
    >
      <Section title={tc.items} aside={items.data && <span className="caps jsection__title">{items.data.length}</span>}>
        {!manager && <p className="jsection__note">{t.managersOnly}</p>}
        {items.data === undefined ? (
          <div className="jsection__pad">
            <PanelState error={items.isError ? items.error : undefined} onRetry={() => void items.refetch()} />
          </div>
        ) : items.data.length === 0 ? (
          <p className="jsection__empty">{tc.none}</p>
        ) : (
          <>
            <ol className="register">
              {items.data.map((item, index) => (
                <ItemRow key={item.id} orgId={orgId} period={period} item={item} index={index} manager={manager} />
              ))}
            </ol>
            {manager && <p className="jsection__note jsection__note--foot">{tc.removeNote}</p>}
          </>
        )}
      </Section>

      {manager && (
        <Section title={tc.add}>
          <ItemForm orgId={orgId} period={period} />
        </Section>
      )}
    </JournalLayout>
  )
}

function ItemRow(props: { orgId: string; period: ControlPeriod; item: ControlChecklistItem; index: number; manager: boolean }) {
  const { orgId, period, item, index, manager } = props
  const invalidate = useInvalidate(orgId)
  const [editing, setEditing] = useState(false)
  const remove = useMutation({ mutationFn: () => deleteChecklistItem(orgId, period, item.id), onSuccess: invalidate })
  const numeric = item.item_type === 'numeric'

  if (editing) {
    return (
      <li className="reg-row reg-row--editing">
        <ItemForm orgId={orgId} period={period} initial={item} onDone={() => setEditing(false)} />
      </li>
    )
  }

  return (
    <li className="reg-row">
      <p className="reg-row__date">{String(index + 1).padStart(2, '0')}</p>
      <div className="reg-row__main">
        <p className="reg-row__title">{item.label}</p>
        {numeric && (
          <p className="reg-row__meta caps">{uk.controls.reading.range(formatRange(item.min_value, item.max_value, item.unit))}</p>
        )}
      </div>
      <div className="reg-row__side">
        <Tag tone={numeric ? 'ink' : 'muted'}>{tc.types[item.item_type]}</Tag>
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

interface ItemFormProps {
  orgId: string
  period: ControlPeriod
  initial?: ControlChecklistItem
  onDone?: () => void
}

/** Add a new item, or (with `initial`) edit its label and range. The type is fixed after creation. */
function ItemForm({ orgId, period, initial, onDone }: ItemFormProps) {
  const id = useId()
  const invalidate = useInvalidate(orgId)
  const [label, setLabel] = useState(initial?.label ?? '')
  const [type, setType] = useState<ControlItemType>(initial?.item_type ?? 'bool')
  const [unit, setUnit] = useState(initial?.unit ?? '°C')
  const [min, setMin] = useState(readingInputText(initial?.min_value ?? null))
  const [max, setMax] = useState(readingInputText(initial?.max_value ?? null))
  const [touched, setTouched] = useState(false)
  const numeric = type === 'numeric'

  const minValue = min.trim() === '' ? null : parseReading(min)
  const maxValue = max.trim() === '' ? null : parseReading(max)
  const problem = (() => {
    if (!label.trim()) return tc.needLabel
    if (!numeric) return null
    if (!unit.trim()) return tc.needUnit
    if ((min.trim() !== '' && minValue === null) || (max.trim() !== '' && maxValue === null)) return tc.badNumber
    if (minValue === null && maxValue === null) return tc.needBound
    if (minValue !== null && maxValue !== null && minValue > maxValue) return tc.minAboveMax
    return null
  })()

  const mutation = useMutation({
    mutationFn: () => {
      const range = numeric ? { unit: unit.trim(), min_value: minValue, max_value: maxValue } : {}
      return initial
        ? updateChecklistItem(orgId, period, initial.id, { label: label.trim(), ...range })
        : createChecklistItem(orgId, period, { label: label.trim(), item_type: type, ...range })
    },
    onSuccess: () => {
      invalidate()
      if (!initial) {
        setLabel('')
        setMin('')
        setMax('')
        setTouched(false)
      }
      onDone?.()
    },
  })

  const submit = (event: FormEvent) => {
    event.preventDefault()
    setTouched(true)
    if (problem === null && !mutation.isPending) mutation.mutate()
  }

  return (
    <form className={initial ? 'jform jform--tight' : 'jform'} onSubmit={submit} noValidate>
      <label className="field jform__wide">
        <span className="field__label caps">
          {tc.label} <span className="req">*</span>
        </span>
        <input className="input" value={label} maxLength={500} onChange={(e) => setLabel(e.target.value)} placeholder={tc.labelPlaceholder} />
      </label>

      <div className="field jform__wide">
        <span className="field__label caps" id={`${id}-type`}>
          {tc.type}
        </span>
        {initial ? (
          <p className="field__hint">
            <Tag tone={numeric ? 'ink' : 'muted'}>{tc.types[type]}</Tag> {tc.typeFixed}
          </p>
        ) : (
          <>
            <Choice
              value={type}
              labelledBy={`${id}-type`}
              onChange={setType}
              options={[
                { value: 'bool', label: tc.types.bool ?? 'bool' },
                { value: 'numeric', label: tc.types.numeric ?? 'numeric' },
              ]}
            />
            <p className="field__hint">{tc.typeHint[type]}</p>
          </>
        )}
      </div>

      {numeric && (
        <>
          <label className="field">
            <span className="field__label caps">
              {tc.unit} <span className="req">*</span>
            </span>
            <input className="input" value={unit} maxLength={20} list={`${id}-units`} onChange={(e) => setUnit(e.target.value)} placeholder={tc.unitPlaceholder} />
            <datalist id={`${id}-units`}>
              {UNIT_SUGGESTIONS.map((suggestion) => (
                <option key={suggestion} value={suggestion} />
              ))}
            </datalist>
          </label>
          <label className="field">
            <span className="field__label caps">{tc.min}</span>
            <input className="input" inputMode="decimal" value={min} onChange={(e) => setMin(e.target.value)} placeholder="0" />
          </label>
          <label className="field">
            <span className="field__label caps">{tc.max}</span>
            <input className="input" inputMode="decimal" value={max} onChange={(e) => setMax(e.target.value)} placeholder="4" />
          </label>
          <p className="field__hint jform__wide">
            {tc.boundsHint}
            {initial && ` ${tc.rangeChangeNote}`}
          </p>
        </>
      )}

      <div className="jform__actions">
        <button className="btn btn--primary caps" type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? t.saving : initial ? t.save : `+ ${tc.add}`}
        </button>
        {onDone && (
          <button className="btn btn--secondary caps" type="button" onClick={onDone} disabled={mutation.isPending}>
            {uk.common.cancel}
          </button>
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
