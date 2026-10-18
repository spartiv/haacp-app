import { Link } from 'react-router'
import type { AttentionItem } from '../../api/types'
import { ProgressCells } from '../../components/ProgressCells'
import { RecordStamp } from '../../components/RecordStamp'
import { uk } from '../../i18n/uk'
import { formatSheetDate } from '../../lib/dates'
import { routes } from '../../routes'
import { PanelState } from '../../components/PanelState'
import { useDashboardSummary, useTodaySheet } from './queries'
import { recommendedAction } from './recommendedAction'

const t = uk.dashboard

/** "Швидкий статус за день": live progress of today's sheet + the one next step + open warnings. */
export function TodayPanel({ orgId, today }: { orgId: string; today: string }) {
  const sheetQuery = useTodaySheet(orgId, today)
  const summaryQuery = useDashboardSummary(orgId)
  const { weekday, date } = formatSheetDate(today)
  const sheet = sheetQuery.data

  return (
    <section className="today" aria-labelledby="today-title">
      <header className="today__head">
        <div>
          <p className="today__kicker caps">
            {t.todayKicker} / {weekday}
          </p>
          <h1 className="today__title caps" id="today-title">
            {date}
          </h1>
        </div>
        {sheet && sheet.items.length > 0 && <RecordStamp status={sheet.status} />}
      </header>

      {sheetQuery.isError ? (
        <PanelState error={sheetQuery.error} onRetry={() => void sheetQuery.refetch()} />
      ) : !sheet ? (
        <PanelState />
      ) : (
        <TodayProgress sheet={sheet} />
      )}

      <div className="today__attention">
        <h2 className="today__label caps">{t.attention}</h2>
        {summaryQuery.isError ? (
          <PanelState error={summaryQuery.error} onRetry={() => void summaryQuery.refetch()} />
        ) : !summaryQuery.data ? (
          <PanelState />
        ) : summaryQuery.data.attention_items.length === 0 ? (
          <p className="today__empty">{t.attentionEmpty}</p>
        ) : (
          <ul className="attention-list">
            {summaryQuery.data.attention_items.map((item, index) => (
              <AttentionRow key={`${index}-${item.label}`} item={item} />
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}

function TodayProgress({ sheet }: { sheet: NonNullable<ReturnType<typeof useTodaySheet>['data']> }) {
  const total = sheet.items.length
  const checked = sheet.items.filter((item) => item.status !== 'pending').length
  const deviations = sheet.items.filter((item) => item.status === 'deviation').length
  const action = recommendedAction(sheet)

  return (
    <div className="today__body">
      <div className="today__progress">
        {total === 0 ? (
          <p className="today__empty">{t.noChecklist}</p>
        ) : (
          <>
            <p className="today__count" aria-live="polite">
              {t.checksFilled(checked, total)}
            </p>
            <ProgressCells
              size="lg"
              statuses={sheet.items.map((item) => ({ id: item.control_checklist_item_id, status: item.status }))}
            />
            <p className={`today__dev caps${deviations > 0 ? ' today__dev--crit' : ''}`}>
              {deviations > 0 ? `[ ${t.deviationsCount(deviations)} ]` : t.noDeviations}
            </p>
          </>
        )}
      </div>

      <div className="today__action">
        <p className="today__label caps">{t.recommended}</p>
        {action.opensSheet ? (
          <Link
            to={routes.daily}
            className={`btn ${action.urgent ? 'btn--primary' : 'btn--secondary'} btn--wide btn--link caps`}
          >
            {`[\u00A0${action.label}\u00A0]`}
          </Link>
        ) : (
          <p className="today__done caps">{action.label}</p>
        )}
      </div>
    </div>
  )
}

function AttentionRow({ item }: { item: AttentionItem }) {
  return (
    <li className={`attention-row attention-row--${item.severity}`}>
      <span className="attention-row__sev caps">{t.severity[item.severity] ?? item.severity}</span>
      <span className="attention-row__label">{item.label}</span>
    </li>
  )
}
