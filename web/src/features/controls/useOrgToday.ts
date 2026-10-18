import { useQuery, useQueryClient } from '@tanstack/react-query'
import { controlKeys, getSheet } from '../../api/controls'

/**
 * The organization's current date, decided by the server in the organization's
 * timezone. The device clock can disagree (another timezone, around midnight),
 * and the server rejects "future" dates, so screens never compute today locally.
 * The response is today's sheet, which is also seeded into the sheet cache.
 */
export function useOrgToday(orgId: string) {
  const queryClient = useQueryClient()
  return useQuery({
    queryKey: controlKeys.today(orgId),
    queryFn: async ({ signal }) => {
      const sheet = await getSheet(orgId, 'daily', undefined, signal)
      queryClient.setQueryData(controlKeys.sheet(orgId, 'daily', sheet.period_date), sheet)
      return sheet.period_date
    },
    staleTime: 60_000, // re-checked every minute or on focus, so midnight rolls over
  })
}
