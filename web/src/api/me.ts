import { apiRequest } from './client'
import type { MyOrganization } from './types'

export const meKeys = {
  organizations: ['me', 'organizations'] as const,
}

/**
 * Active memberships, sorted by name. Pass a token right after login (before a
 * session exists); omit it to use the current session.
 */
export function listMyOrganizations(accessToken?: string, signal?: AbortSignal): Promise<MyOrganization[]> {
  return apiRequest<MyOrganization[]>('/api/v1/me/organizations', {
    auth: accessToken === undefined ? 'session' : { token: accessToken },
    signal,
  })
}
