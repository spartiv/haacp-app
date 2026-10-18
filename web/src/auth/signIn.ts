import { login, logout } from '../api/auth'
import { ApiError } from '../api/client'
import { listMyOrganizations } from '../api/me'
import type { AuthResponse, MyOrganization } from '../api/types'
import { queryClient } from '../lib/queryClient'
import { rememberLogin, sessionStore } from './session'

export interface Credentials {
  email: string
  password: string
}

/** Logged in, but the account belongs to several organizations: the user must pick one. */
export interface PendingSignIn {
  email: string
  auth: AuthResponse
  organizations: MyOrganization[]
}

/**
 * Logs in and resolves the organization automatically:
 * one membership → session starts; several → returns them for the picker;
 * none → throws `no_organizations` (and revokes the fresh tokens).
 */
export async function signIn(credentials: Credentials): Promise<PendingSignIn | null> {
  const auth = await login(credentials)

  let organizations: MyOrganization[]
  try {
    organizations = await listMyOrganizations(auth.tokens.access_token)
  } catch (error) {
    discardTokens(auth)
    throw error
  }

  const [only] = organizations
  if (only === undefined) {
    discardTokens(auth)
    throw new ApiError(403, 'no_organizations', 'This account is not a member of any organization.')
  }
  if (organizations.length === 1) {
    completeSignIn({ email: credentials.email, auth, organizations }, only)
    return null
  }
  return { email: credentials.email, auth, organizations }
}

export function completeSignIn(pending: PendingSignIn, organization: MyOrganization): void {
  // Never show one account's cached data to the next one on a shared device.
  queryClient.clear()
  rememberLogin({ email: pending.email, organization_id: organization.organization_id })
  sessionStore.start({
    access_token: pending.auth.tokens.access_token,
    refresh_token: pending.auth.tokens.refresh_token,
    organization_id: organization.organization_id,
    organization_name: organization.name,
    role: organization.role,
    user: pending.auth.user,
  })
}

/** Abandons a pending sign-in (user went back from the picker). */
export function cancelSignIn(pending: PendingSignIn): void {
  discardTokens(pending.auth)
}

// Don't leave a valid refresh token around for a session that never started.
function discardTokens(auth: AuthResponse): void {
  logout(auth.tokens.refresh_token).catch(() => undefined)
}

export async function signOut(): Promise<void> {
  const session = sessionStore.get()
  sessionStore.end('signed_out')
  queryClient.clear()
  if (session !== null) await logout(session.refresh_token).catch(() => undefined)
}
