import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { RecordStamp } from '../../components/RecordStamp'
import { uk } from '../../i18n/uk'
import { formatShortDate, shiftIsoDate } from '../../lib/dates'
import { routes } from '../../routes'
import { MEDICAL_WARNING_DAYS } from './constants'
import { useDashboardSummary, useLatestEventEntry, useMedicalChecks, useTodaySheet } from './queries'

const t = uk.dashboard

export function JournalCards({ orgId, today }: { orgId: string; today: string }) {
  return (
    <section aria-labelledby="journals-title">
      <h2 className="dash-section-title caps" id="journals-title">
        {t.journals}
      </h2>
      <div className="journal-grid">
        <DailyCard orgId={orgId} today={today} />
        <BatchesCard orgId={orgId} />
        <GlassCard orgId={orgId} />
        <MedicalCard orgId={orgId} today={today} />
      </div>
    </section>
  )
}

interface JournalCardProps {
  title: string
  to: string
  tone?: 'ink' | 'crit'
  children: ReactNode
}

/** One journal's live summary, linking to its screen. */
function JournalCard({ title, to, tone = 'ink', children }: JournalCardProps) {
  return (
    <article className={`journal-card${tone === 'crit' ? ' journal-card--crit' : ''}`}>
      <h3 className="journal-card__title">{title}</h3>
      <div className="journal-card__body">{children}</div>
      <div className="journal-card__foot">
        <Link to={to} className="btn btn--secondary btn--wide btn--link caps">
          [ {t.open} ]
        </Link>
      </div>
    </article>
  )
}

const Muted = ({ children }: { children: ReactNode }) => <p className="journal-card__muted">{children}</p>

function DailyCard({ orgId, today }: { orgId: string; today: string }) {
  const { data: sheet, isError } = useTodaySheet(orgId, today)
  const total = sheet?.items.length ?? 0
  const checked = sheet?.items.filter((item) => item.status !== 'pending').length ?? 0
  const deviations = sheet?.items.filter((item) => item.status === 'deviation').length ?? 0

  return (
    <JournalCard title={t.journal.daily} to={routes.daily} tone={deviations > 0 ? 'crit' : 'ink'}>
      {isError ? (
        <Muted>{t.loadFailed}</Muted>
      ) : !sheet ? (
        <Muted>…</Muted>
      ) : total === 0 ? (
        <Muted>{t.noChecklist}</Muted>
      ) : (
        <>
          <p className="journal-card__metric">
            {checked} / {total}
          </p>
          <RecordStamp status={sheet.status} />
          {deviations > 0 && <p className="journal-card__crit caps">[ {t.deviationsCount(deviations)} ]</p>}
        </>
      )}
    </JournalCard>
  )
}

function BatchesCard({ orgId }: { orgId: string }) {
  const { data, isError } = useDashboardSummary(orgId)
  return (
    <JournalCard title={t.journal.batches} to={routes.batches}>
      {isError ? (
        <Muted>{t.loadFailed}</Muted>
      ) : !data ? (
        <Muted>…</Muted>
      ) : (
        <>
          <p className="journal-card__metric">{data.batches_this_month}</p>
          <Muted>{t.batchesThisMonth(data.batches_this_month)}</Muted>
        </>
      )}
    </JournalCard>
  )
}

function GlassCard({ orgId }: { orgId: string }) {
  const { entry, isPending, isError } = useLatestEventEntry(orgId, 'glass')
  const deviation = entry?.has_deviation === true
  return (
    <JournalCard title={t.journal.glass} to={routes.eventLog('glass')} tone={deviation ? 'crit' : 'ink'}>
      {isError ? (
        <Muted>{t.loadFailed}</Muted>
      ) : isPending ? (
        <Muted>…</Muted>
      ) : entry === null ? (
        <Muted>{t.glassNone}</Muted>
      ) : (
        <>
          <p className="journal-card__metric journal-card__metric--date">{formatShortDate(entry.entry_date)}</p>
          <Muted>{t.glassLast}</Muted>
          {deviation && <p className="journal-card__crit caps">[ {t.glassDeviation} ]</p>}
        </>
      )}
    </JournalCard>
  )
}

function MedicalCard({ orgId, today }: { orgId: string; today: string }) {
  const checks = useMedicalChecks(orgId)
  const maintenance = useLatestEventEntry(orgId, 'eq')
  const warnUntil = shiftIsoDate(today, MEDICAL_WARNING_DAYS)
  // ISO dates compare correctly as strings.
  const overdue = checks.data?.filter((check) => check.next_check_date < today).length ?? 0
  const soon =
    checks.data?.filter((check) => check.next_check_date >= today && check.next_check_date <= warnUntil).length ?? 0

  return (
    <JournalCard title={t.journal.medical} to={routes.medical} tone={overdue > 0 ? 'crit' : 'ink'}>
      {checks.isError ? (
        <Muted>{t.loadFailed}</Muted>
      ) : !checks.data ? (
        <Muted>…</Muted>
      ) : checks.data.length === 0 ? (
        <Muted>{t.medicalNone}</Muted>
      ) : (
        <>
          {overdue > 0 ? (
            <p className="journal-card__crit caps">[ {t.medicalOverdue(overdue)} ]</p>
          ) : (
            soon === 0 && <Muted>{t.medicalOk}</Muted>
          )}
          {soon > 0 && <p className="journal-card__warn caps">{t.medicalSoon(soon)}</p>}
        </>
      )}
      {!maintenance.isPending && !maintenance.isError && (
        <Muted>
          {maintenance.entry ? t.maintenanceLast(formatShortDate(maintenance.entry.entry_date)) : t.maintenanceNone}
        </Muted>
      )}
    </JournalCard>
  )
}
