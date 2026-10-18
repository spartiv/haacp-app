import { orgBase } from './base'
import { apiRequest } from './client'
import type { Member } from './types'

export const memberKeys = {
  list: (organizationId: string) => ['members', organizationId] as const,
}

/** Active members first, then removed ones (still needed to name past records). */
export function listMembers(organizationId: string, signal?: AbortSignal): Promise<Member[]> {
  return apiRequest<Member[]>(`${orgBase(organizationId)}/members`, { signal })
}
