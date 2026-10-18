// Session persisted in localStorage, exposed as a tiny external store so both
// React (useSession) and the API client (sessionStore.get) read the same value.
import { useSyncExternalStore } from 'react'
import type { TokenResponse, UserResponse } from '../api/types'

export interface Session {
  access_token: string
  refresh_token: string
  organization_id: string
  organization_name: string
  role: string
  user: UserResponse
}

/** Why the last session ended, so the login screen can explain it. */
export type SessionEndReason = 'signed_out' | 'expired' | 'access_revoked'

/** Non-secret values pre-filled on the login form next time. */
export interface RememberedLogin {
  email: string
  /** Last organization used: pre-selected in the picker for multi-org accounts. */
  organization_id: string | null
}

// v2: sessions now carry the organization name and role. Older v1 sessions are
// ignored, so those users sign in once more.
const SESSION_KEY = 'haccp.session.v2'
const REMEMBER_KEY = 'haccp.login.remember.v1'
// Written just before the session is cleared, so other tabs can show why.
const END_REASON_KEY = 'haccp.session.end-reason.v1'

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isSession(value: unknown): value is Session {
  if (!isRecord(value) || !isRecord(value.user)) return false
  return (
    typeof value.access_token === 'string' &&
    typeof value.refresh_token === 'string' &&
    typeof value.organization_id === 'string' &&
    typeof value.organization_name === 'string' &&
    typeof value.role === 'string' &&
    typeof value.user.id === 'string' &&
    typeof value.user.email === 'string' &&
    typeof value.user.full_name === 'string'
  )
}

function readJson(key: string): unknown {
  try {
    const raw = localStorage.getItem(key)
    return raw === null ? null : (JSON.parse(raw) as unknown)
  } catch {
    return null
  }
}

function writeJson(key: string, value: unknown): void {
  try {
    if (value === null) localStorage.removeItem(key)
    else localStorage.setItem(key, JSON.stringify(value))
  } catch {
    // Storage blocked (private mode, quota): the session still works for this tab.
  }
}

function readSession(): Session | null {
  const value = readJson(SESSION_KEY)
  return isSession(value) ? value : null
}

let current: Session | null = readSession()
let endReason: SessionEndReason | null = null
const listeners = new Set<() => void>()

function emit(): void {
  for (const listener of listeners) listener()
}

export const sessionStore = {
  get(): Session | null {
    return current
  },

  get endReason(): SessionEndReason | null {
    return endReason
  },

  subscribe(listener: () => void): () => void {
    listeners.add(listener)
    return () => listeners.delete(listener)
  },

  start(session: Session): void {
    current = session
    endReason = null
    writeJson(SESSION_KEY, session)
    emit()
  },

  updateTokens(tokens: TokenResponse): void {
    if (current === null) return
    current = { ...current, access_token: tokens.access_token, refresh_token: tokens.refresh_token }
    writeJson(SESSION_KEY, current)
    emit()
  },

  /** Keeps the organization's name/role current (they can change on the server). */
  updateOrganization(organization: { name: string; role: string }): void {
    if (current === null) return
    if (current.organization_name === organization.name && current.role === organization.role) return
    current = { ...current, organization_name: organization.name, role: organization.role }
    writeJson(SESSION_KEY, current)
    emit()
  },

  end(reason: SessionEndReason): void {
    current = null
    endReason = reason
    writeJson(END_REASON_KEY, reason)
    writeJson(SESSION_KEY, null)
    emit()
  },
}

// Keep tabs in sync: signing in/out (or a token refresh) in one tab applies to all.
if (typeof window !== 'undefined') {
  window.addEventListener('storage', (event) => {
    if (event.key !== SESSION_KEY && event.key !== null) return
    const previous = current
    current = readSession()
    if (previous !== null && current === null) endReason = readEndReason()
    emit()
  })
}

function readEndReason(): SessionEndReason | null {
  const value = readJson(END_REASON_KEY)
  return value === 'signed_out' || value === 'expired' || value === 'access_revoked' ? value : null
}

export function useSession(): Session | null {
  return useSyncExternalStore(sessionStore.subscribe, sessionStore.get)
}

export function readRememberedLogin(): RememberedLogin | null {
  const value = readJson(REMEMBER_KEY)
  if (!isRecord(value)) return null
  const { email, organization_id } = value
  if (typeof email !== 'string') return null
  return { email, organization_id: typeof organization_id === 'string' ? organization_id : null }
}

export function rememberLogin(login: RememberedLogin): void {
  writeJson(REMEMBER_KEY, login)
}
