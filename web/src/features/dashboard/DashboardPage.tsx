import type { Session } from '../../auth/session'
import { useOrgToday } from '../controls/useOrgToday'
import { JournalCards } from './JournalCards'
import { PanelState } from '../../components/PanelState'
import { TodayPanel } from './TodayPanel'
import './dashboard.css'

export function DashboardPage({ session }: { session: Session }) {
  const orgId = session.organization_id
  const todayQuery = useOrgToday(orgId)
  const today = todayQuery.data

  return (
    <div className="dash">
      {today === undefined ? (
        <section className="today">
          <PanelState
            error={todayQuery.isError ? todayQuery.error : undefined}
            onRetry={() => void todayQuery.refetch()}
          />
        </section>
      ) : (
        <>
          <TodayPanel orgId={orgId} today={today} />
          <JournalCards orgId={orgId} today={today} />
        </>
      )}
    </div>
  )
}
