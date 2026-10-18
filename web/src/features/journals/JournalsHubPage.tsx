import { useQuery } from '@tanstack/react-query'
import { useRef, type KeyboardEvent, type ReactNode } from 'react'
import { Link, useSearchParams } from 'react-router'
import { controlKeys, getSheet } from '../../api/controls'
import type { ControlPeriod, EventLogType } from '../../api/types'
import type { Session } from '../../auth/session'
import { PanelState } from '../../components/PanelState'
import { RecordStamp } from '../../components/RecordStamp'
import { uk } from '../../i18n/uk'
import { formatShortDate, monthStart, toIsoMonth } from '../../lib/dates'
import { routes } from '../../routes'
import { useDashboardSummary } from '../dashboard/queries'
import { eventLogGroup, isJournalGroup, JOURNAL_GROUPS, MONOGRAM, type JournalGroup } from './catalog'
import { medicalState } from './medical'
import {
  useChemicals,
  useEquipment,
  useEventEntries,
  useEventLogTypes,
  useMedicalChecks,
  useProducts,
} from './queries'
import { Tag, WithToday } from './ui'

const t = uk.journals

/** The journals register, one cadence tab at a time (?group=…), each row with its live status. */
export function JournalsHubPage({ session }: { session: Session }) {
  const orgId = session.organization_id
  const [searchParams, setSearchParams] = useSearchParams()
  const requested = searchParams.get('group')
  const group: JournalGroup = isJournalGroup(requested) ? requested : 'daily'
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([])

  const select = (next: JournalGroup) => setSearchParams(next === 'daily' ? {} : { group: next }, { replace: true })

  // Arrow keys move between tabs (WAI-ARIA tabs pattern).
  const onTabKey = (event: KeyboardEvent, index: number) => {
    const delta = event.key === 'ArrowRight' ? 1 : event.key === 'ArrowLeft' ? -1 : 0
    if (delta === 0) return
    event.preventDefault()
    const nextIndex = (index + delta + JOURNAL_GROUPS.length) % JOURNAL_GROUPS.length
    const next = JOURNAL_GROUPS[nextIndex]
    if (next === undefined) return
    select(next)
    tabRefs.current[nextIndex]?.focus()
  }

  return (
    <div className="jpage">
      <header className="jpage-head">
        <div>
          <p className="jpage-head__kicker caps">{t.kicker}</p>
          <h1 className="jpage-head__title">{t.title}</h1>
        </div>
      </header>

      <div className="hub-tabs" role="tablist" aria-label={t.groupsLabel}>
        {JOURNAL_GROUPS.map((key, index) => (
          <button
            key={key}
            ref={(node) => {
              tabRefs.current[index] = node
            }}
            id={`hub-tab-${key}`}
            className="hub-tab caps"
            type="button"
            role="tab"
            aria-selected={group === key}
            aria-controls="hub-panel"
            tabIndex={group === key ? 0 : -1}
            onClick={() => select(key)}
            onKeyDown={(event) => onTabKey(event, index)}
          >
            {t.group[key]}
          </button>
        ))}
      </div>

      <section className="jsection" id="hub-panel" role="tabpanel" aria-labelledby={`hub-tab-${group}`}>
        <p className="jsection__note">{t.groupHint[group]}</p>
        <WithToday orgId={orgId}>{(today) => <GroupRows orgId={orgId} group={group} today={today} />}</WithToday>
      </section>
    </div>
  )
}

function GroupRows({ orgId, group, today }: { orgId: string; group: JournalGroup; today: string }) {
  const types = useEventLogTypes(orgId)
  const needsEventLogs = group === 'periodic' || group === 'events'

  if (needsEventLogs && types.data === undefined) {
    return (
      <div className="jsection__pad">
        <PanelState error={types.isError ? types.error : undefined} onRetry={() => void types.refetch()} />
      </div>
    )
  }
  const logs = (types.data ?? []).filter((type) => eventLogGroup(type.key) === group)

  return (
    <ul className="hub-list">
      {group === 'daily' && <ControlRow orgId={orgId} period="daily" today={today} />}
      {group === 'periodic' && <ControlRow orgId={orgId} period="monthly" today={today} />}
      {group === 'planned' && <MedicalRow orgId={orgId} today={today} />}
      {group === 'events' && <BatchesRow orgId={orgId} />}
      {logs.map((type) => (
        <EventLogRow key={type.id} orgId={orgId} type={type} cadence={group === 'periodic' ? t.cadence.periodic : t.cadence.event} />
      ))}
      {group === 'references' && (
        <>
          <EquipmentRow orgId={orgId} />
          <ChemicalsRow orgId={orgId} />
        </>
      )}
    </ul>
  )
}

interface HubRowProps {
  to: string
  mono: string
  name: string
  cadence: string
  crit?: boolean
  children: ReactNode
}

function HubRow({ to, mono, name, cadence, crit = false, children }: HubRowProps) {
  return (
    <li>
      <Link to={to} className={`hub-row${crit ? ' hub-row--crit' : ''}`}>
        <span className="hub-row__mono" aria-hidden="true">
          {mono}
        </span>
        <span>
          <p className="hub-row__name">{name}</p>
          <p className="hub-row__cadence caps">{cadence}</p>
        </span>
        <span className="hub-row__status">{children}</span>
        <span className="hub-row__open caps">[ {t.open} ]</span>
      </Link>
    </li>
  )
}

const Muted = ({ children }: { children: ReactNode }) => <p className="hub-row__muted">{children}</p>
const Loading = () => <Muted>…</Muted>
const Failed = () => <Muted>{t.loadFailed}</Muted>

function ControlRow({ orgId, period, today }: { orgId: string; period: ControlPeriod; today: string }) {
  const date = period === 'daily' ? today : monthStart(toIsoMonth(today))
  const { data: sheet, isError } = useQuery({
    queryKey: controlKeys.sheet(orgId, period, date),
    queryFn: ({ signal }) => getSheet(orgId, period, date, signal),
  })
  const total = sheet?.items.length ?? 0
  const checked = sheet?.items.filter((item) => item.status !== 'pending').length ?? 0
  const deviations = sheet?.items.filter((item) => item.status === 'deviation').length ?? 0

  return (
    <HubRow
      to={period === 'daily' ? routes.daily : routes.monthly}
      mono={MONOGRAM[period]}
      name={t.name[period]}
      cadence={period === 'daily' ? t.cadence.daily : t.cadence.monthly}
      crit={deviations > 0}
    >
      {isError ? (
        <Failed />
      ) : !sheet ? (
        <Loading />
      ) : total === 0 ? (
        <Muted>{t.noChecklist}</Muted>
      ) : (
        <>
          <RecordStamp status={sheet.status} />
          <p>{t.checked(checked, total)}</p>
          {deviations > 0 && <Tag tone="crit">{uk.dashboard.deviationsCount(deviations)}</Tag>}
        </>
      )}
    </HubRow>
  )
}

function EventLogRow({ orgId, type, cadence }: { orgId: string; type: EventLogType; cadence: string }) {
  const { data, isError } = useEventEntries(orgId, type.id)
  const latest = data?.[0]
  return (
    <HubRow to={routes.eventLog(type.key)} mono={type.icon_label} name={type.name} cadence={cadence} crit={latest?.has_deviation === true}>
      {isError ? (
        <Failed />
      ) : data === undefined ? (
        <Loading />
      ) : latest === undefined ? (
        <Muted>{t.noEntries}</Muted>
      ) : (
        <>
          <p>{t.lastEntry(formatShortDate(latest.entry_date))}</p>
          {latest.has_deviation && <Tag tone="crit">{t.lastDeviation}</Tag>}
        </>
      )}
    </HubRow>
  )
}

function BatchesRow({ orgId }: { orgId: string }) {
  const summary = useDashboardSummary(orgId)
  const products = useProducts(orgId)
  return (
    <HubRow to={routes.batches} mono={MONOGRAM.batches} name={t.name.batches} cadence={t.cadence.event}>
      {summary.isError || products.isError ? (
        <Failed />
      ) : !summary.data || !products.data ? (
        <Loading />
      ) : (
        <>
          <p>{uk.dashboard.batchesThisMonth(summary.data.batches_this_month)}</p>
          <Muted>{t.products(products.data.length)}</Muted>
        </>
      )}
    </HubRow>
  )
}

function MedicalRow({ orgId, today }: { orgId: string; today: string }) {
  const { data, isError } = useMedicalChecks(orgId)
  const states = (data ?? []).map((check) => medicalState(check.next_check_date, today))
  const overdue = states.filter((state) => state.kind === 'overdue').length
  const soon = states.filter((state) => state.kind === 'soon' || state.kind === 'today').length
  return (
    <HubRow to={routes.medical} mono={MONOGRAM.medical} name={t.name.medical} cadence={t.cadence.planned} crit={overdue > 0}>
      {isError ? (
        <Failed />
      ) : data === undefined ? (
        <Loading />
      ) : data.length === 0 ? (
        <Muted>{uk.dashboard.medicalNone}</Muted>
      ) : (
        <>
          {overdue > 0 && <Tag tone="crit">{uk.dashboard.medicalOverdue(overdue)}</Tag>}
          {soon > 0 && <Tag tone="warn">{uk.dashboard.medicalSoon(soon)}</Tag>}
          {overdue === 0 && soon === 0 && <p>{uk.dashboard.medicalOk}</p>}
        </>
      )}
    </HubRow>
  )
}

function EquipmentRow({ orgId }: { orgId: string }) {
  const { data, isError } = useEquipment(orgId)
  const missing = (data ?? []).filter((item) => item.affects_product_safety && item.attachment_id === null).length
  return (
    <HubRow to={routes.equipment} mono={MONOGRAM.equipment} name={t.name.equipment} cadence={t.cadence.reference}>
      {isError ? (
        <Failed />
      ) : data === undefined ? (
        <Loading />
      ) : data.length === 0 ? (
        <Muted>{t.equipment.none}</Muted>
      ) : (
        <>
          <p>{t.equipmentCount(data.length)}</p>
          {missing > 0 && <Tag tone="warn">{t.missingDocs(missing)}</Tag>}
        </>
      )}
    </HubRow>
  )
}

function ChemicalsRow({ orgId }: { orgId: string }) {
  const { data, isError } = useChemicals(orgId)
  return (
    <HubRow to={routes.chemicals} mono={MONOGRAM.chemicals} name={t.name.chemicals} cadence={t.cadence.reference}>
      {isError ? <Failed /> : data === undefined ? <Loading /> : data.length === 0 ? <Muted>{t.chemicals.none}</Muted> : <p>{t.chemicalsCount(data.length)}</p>}
    </HubRow>
  )
}
