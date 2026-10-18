import { useQuery } from '@tanstack/react-query'
import { dashboardKeys, getDashboard } from '../../api/dashboard'
import { controlKeys, getSheet } from '../../api/controls'

export { useLatestEventEntry, useMedicalChecks } from '../journals/queries'

/** Today's daily sheet. Same cache entry as the Daily Controls page, so both stay in sync. */
export function useTodaySheet(orgId: string, today: string) {
  return useQuery({
    queryKey: controlKeys.sheet(orgId, 'daily', today),
    queryFn: ({ signal }) => getSheet(orgId, 'daily', today, signal),
  })
}

export function useDashboardSummary(orgId: string) {
  return useQuery({
    queryKey: dashboardKeys.summary(orgId),
    queryFn: ({ signal }) => getDashboard(orgId, signal),
  })
}
