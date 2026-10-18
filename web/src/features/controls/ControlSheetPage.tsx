import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useCallback, useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { controlKeys, getSheet } from '../../api/controls'
import type { ControlPeriod, ControlSheet } from '../../api/types'
import type { Session } from '../../auth/session'
import { RecordStamp } from '../../components/RecordStamp'
import { errorCode, errorMessage, uk } from '../../i18n/uk'
import {
  formatMonth,
  formatSheetDate,
  formatTime,
  isIsoDate,
  isIsoMonth,
  monthStart,
  shiftIsoDate,
  shiftIsoMonth,
  toIsoMonth,
} from '../../lib/dates'
import { routes } from '../../routes'
import { canManage } from '../journals/helpers'
import { PerformerSelect } from '../team/PerformerSelect'
import { usePerformer } from '../team/performer'
import { AuditDrawer } from './AuditDrawer'
import { SheetItemRow } from './SheetItemRow'
import { SubmitBar } from './SubmitBar'
import { useOrgToday } from './useOrgToday'
import './controls.css'

const t = uk.controls

/** Daily or monthly control sheet: fill item by item, submit to lock, every change audited. */
export function ControlSheetPage({ session, period }: { session: Session; period: ControlPeriod }) {
  const orgId = session.organization_id
  const todayQuery = useOrgToday(orgId)
  const today = todayQuery.data

  if (today === undefined) {
    return (
      <div className="controls">
        <section className="sheet">
          {todayQuery.isError ? (
            <SheetError error={todayQuery.error} onRetry={() => void todayQuery.refetch()} />
          ) : (
            <p className="sheet-state caps" role="status">
              {t.loadingToday}
            </p>
          )}
        </section>
      </div>
    )
  }
  return <Sheet key={period} session={session} period={period} today={today} />
}

interface PeriodSelection {
  /** The date the sheet is filed under: the day, or the 1st of the month. */
  periodDate: string
  isCurrent: boolean
  shift: (step: number) => void
  goCurrent: () => void
  /** Native picker: <input type="date"> or <input type="month">. */
  input: { type: 'date' | 'month'; value: string; max: string; onChange: (value: string) => void }
}

/**
 * The selected day/month lives in the URL (?date=YYYY-MM-DD or ?month=YYYY-MM;
 * none = current), so the picker, the previous/next buttons, reloads and shared
 * links always agree. Future periods are clamped to the current one.
 */
function usePeriodSelection(period: ControlPeriod, today: string): PeriodSelection {
  const [searchParams, setSearchParams] = useSearchParams()
  const isDaily = period === 'daily'
  const param = isDaily ? 'date' : 'month'
  const current = isDaily ? today : toIsoMonth(today)
  const isValid = isDaily ? isIsoDate : isIsoMonth
  const requested = searchParams.get(param)
  // ISO dates and months compare correctly as strings.
  const value = isValid(requested) && requested <= current ? requested : current

  const set = useCallback(
    (next: string) => {
      if (!isValid(next)) return
      const clamped = next > current ? current : next
      setSearchParams(clamped === current ? {} : { [param]: clamped }, { replace: true })
    },
    [current, isValid, param, setSearchParams],
  )

  return {
    periodDate: isDaily ? value : monthStart(value),
    isCurrent: value === current,
    shift: (step) => set(isDaily ? shiftIsoDate(value, step) : shiftIsoMonth(value, step)),
    goCurrent: () => set(current),
    input: { type: isDaily ? 'date' : 'month', value, max: current, onChange: set },
  }
}

function sheetTitle(period: ControlPeriod, periodDate: string): { kicker: string; title: string; full: string } {
  if (period === 'daily') {
    const { weekday, date } = formatSheetDate(periodDate)
    return { kicker: t.kicker(weekday), title: date, full: `${weekday}, ${date}` }
  }
  const { month, year } = formatMonth(toIsoMonth(periodDate))
  return { kicker: t.monthly.kicker(year), title: `${month} ${year}`, full: `${month} ${year}` }
}

function Sheet({ session, period, today }: { session: Session; period: ControlPeriod; today: string }) {
  const orgId = session.organization_id
  const manager = canManage(session)
  const performer = usePerformer(session)
  const selection = usePeriodSelection(period, today)
  const date = selection.periodDate
  const [auditOpen, setAuditOpen] = useState(false)
  const queryClient = useQueryClient()
  const sheetKey = controlKeys.sheet(orgId, period, date)
  const isDaily = period === 'daily'
  const nav = isDaily
    ? { label: t.dayNav, prev: t.prevDay, next: t.nextDay, current: t.today, pick: t.pickDate }
    : { label: t.monthly.nav, prev: t.monthly.prev, next: t.monthly.next, current: t.monthly.current, pick: t.monthly.pick }

  const sheetQuery = useQuery({
    queryKey: sheetKey,
    queryFn: ({ signal }) => getSheet(orgId, period, date, signal),
  })

  // Every mutation returns the full updated sheet: write it straight into the cache.
  const handleSheetUpdated = useCallback(
    (sheet: ControlSheet) => {
      queryClient.setQueryData(controlKeys.sheet(orgId, period, sheet.period_date), sheet)
      void queryClient.invalidateQueries({ queryKey: controlKeys.auditAll(orgId) })
      // The dashboard summary depends on sheet state too.
      void queryClient.invalidateQueries({ queryKey: ['dashboard', orgId] })
    },
    [orgId, period, queryClient],
  )

  const heading = sheetTitle(period, date)
  const sheet = sheetQuery.data

  return (
    <div className="controls">
      {!isDaily && (
        <Link className="jpage-back caps controls__back" to={routes.journalGroup('periodic')}>
          {uk.journals.back}
        </Link>
      )}
      <nav className="date-nav caps" aria-label={nav.label}>
        <button className="date-nav__btn caps" type="button" onClick={() => selection.shift(-1)}>
          {nav.prev}
        </button>
        <label className="date-nav__picker">
          <span className="date-nav__picker-label caps">{nav.pick}</span>
          <input
            className="date-nav__input"
            type={selection.input.type}
            value={selection.input.value}
            max={selection.input.max}
            required
            onChange={(event) => selection.input.onChange(event.target.value)}
          />
        </label>
        <button
          className="date-nav__btn caps"
          type="button"
          onClick={() => selection.shift(1)}
          disabled={selection.isCurrent}
        >
          {nav.next}
        </button>
        {!selection.isCurrent && (
          <button className="date-nav__btn caps" type="button" onClick={selection.goCurrent}>
            {nav.current}
          </button>
        )}
      </nav>

      <section className="sheet" aria-labelledby="sheet-title">
        <header className="sheet-head">
          <div>
            <p className="sheet-head__kicker caps">{heading.kicker}</p>
            <h1 className="sheet-head__title caps" id="sheet-title">
              {heading.title}
            </h1>
          </div>
          {sheet && (
            <div className="sheet-head__side">
              {manager && (
                <Link className="btn btn--secondary btn--link caps" to={routes.checklistSettings(period)}>
                  {t.settings}
                </Link>
              )}
              <RecordStamp status={sheet.status} />
              <button
                className="btn btn--secondary caps"
                type="button"
                onClick={() => setAuditOpen(true)}
                disabled={sheet.record_id === null}
                title={sheet.record_id === null ? t.nothingRecorded : undefined}
              >
                {t.auditHistory}
              </button>
            </div>
          )}
        </header>

        {sheetQuery.isPending ? (
          <p className="sheet-state caps" role="status">
            {t.loadingSheet}
          </p>
        ) : sheetQuery.isError ? (
          <SheetError error={sheetQuery.error} onRetry={() => void sheetQuery.refetch()} />
        ) : sheet && sheet.items.length === 0 ? (
          <div className="sheet-state">
            <p className="caps">{t.noChecks}</p>
            <p>{isDaily ? t.noChecksHint : t.monthly.noChecksHint}</p>
            {manager && (
              <Link className="btn btn--primary btn--link caps" to={routes.checklistSettings(period)}>
                {t.settings}
              </Link>
            )}
          </div>
        ) : sheet ? (
          <>
            {sheet.status === 'submitted' && (
              <p className="sheet-notice">
                {t.submittedNotice(
                  sheet.submitted_by?.full_name ?? null,
                  sheet.submitted_at ? formatTime(sheet.submitted_at) : null,
                )}
              </p>
            )}
            {performer.active.length > 1 && (
              <div className="sheet-performer">
                <PerformerSelect session={session} choice={performer} />
              </div>
            )}
            <ol className="sheet-items" key={sheet.period_date}>
              {sheet.items.map((item, index) => (
                <SheetItemRow
                  key={item.control_checklist_item_id}
                  orgId={orgId}
                  period={period}
                  periodDate={sheet.period_date}
                  item={item}
                  index={index}
                  recordStatus={sheet.status}
                  performerId={performer.performerId}
                  onUpdated={handleSheetUpdated}
                />
              ))}
            </ol>
          </>
        ) : null}
      </section>

      {sheet && sheet.items.length > 0 && <SubmitBar orgId={orgId} sheet={sheet} onUpdated={handleSheetUpdated} />}

      {auditOpen && sheet?.record_id && (
        <AuditDrawer
          orgId={orgId}
          recordId={sheet.record_id}
          title={heading.full}
          onClose={() => setAuditOpen(false)}
        />
      )}
    </div>
  )
}

function SheetError({ error, onRetry }: { error: Error; onRetry: () => void }) {
  return (
    <div className="sheet-error" role="alert">
      <p className="sheet-error__label caps">{uk.common.error}</p>
      <p>{t.sheetLoadFailed} {errorMessage(error)}</p>
      <p className="sheet-error__code caps">
        {uk.common.code}: {errorCode(error)}
      </p>
      <button className="btn btn--primary caps" type="button" onClick={onRetry}>
        {uk.common.retry}
      </button>
    </div>
  )
}
