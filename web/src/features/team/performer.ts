// "Виконавець": who physically does the work on a shared kitchen device.
// The signed-in account is always recorded by the server as well; this only
// picks the person. The choice is remembered per device and organization, so
// a cook doing a round of checks picks their name once.
import { useQuery } from '@tanstack/react-query'
import { useCallback, useMemo, useSyncExternalStore } from 'react'
import { listMembers, memberKeys } from '../../api/members'
import type { Member } from '../../api/types'
import type { Session } from '../../auth/session'

const storageKey = (orgId: string) => `haccp.performer.v1.${orgId}`
const listeners = new Set<() => void>()

function read(orgId: string): string | null {
  try {
    return localStorage.getItem(storageKey(orgId))
  } catch {
    return null
  }
}

function write(orgId: string, userId: string | null): void {
  try {
    if (userId === null) localStorage.removeItem(storageKey(orgId))
    else localStorage.setItem(storageKey(orgId), userId)
  } catch {
    // Storage blocked: the choice simply isn't remembered.
  }
  for (const listener of listeners) listener()
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function useMembers(orgId: string) {
  return useQuery({
    queryKey: memberKeys.list(orgId),
    queryFn: ({ signal }) => listMembers(orgId, signal),
    staleTime: 5 * 60_000,
  })
}

/** Everyone who ever was a member, by user id: names past records. */
export function useMemberNames(orgId: string): Map<string, string> {
  const { data } = useMembers(orgId)
  return useMemo(() => new Map((data ?? []).map((m) => [m.user_id, m.full_name])), [data])
}

export interface PerformerChoice {
  /** The chosen person's user id (defaults to the signed-in user). */
  performerId: string
  setPerformer: (userId: string) => void
  /** Active members, for the picker. Empty while loading. */
  active: Member[]
}

export function usePerformer(session: Session): PerformerChoice {
  const orgId = session.organization_id
  const me = session.user.id
  const members = useMembers(orgId)
  const stored = useSyncExternalStore(subscribe, () => read(orgId))
  // The signed-in person first (the usual choice), then the team by name.
  const active = useMemo(
    () =>
      (members.data ?? [])
        .filter((m) => m.status === 'active')
        .sort((a, b) => Number(b.user_id === me) - Number(a.user_id === me)),
    [members.data, me],
  )
  // A remembered person who has since left falls back to the signed-in user.
  const performerId = stored !== null && active.some((m) => m.user_id === stored) ? stored : me
  const setPerformer = useCallback((userId: string) => write(orgId, userId === me ? null : userId), [orgId, me])
  return { performerId, setPerformer, active }
}
