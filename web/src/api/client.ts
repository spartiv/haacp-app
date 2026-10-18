// Thin fetch wrapper: JSON in/out, bearer auth, one automatic token refresh on 401,
// and every failure normalized to ApiError (built from the backend's error envelope).
import { sessionStore } from '../auth/session'
import { isApiErrorEnvelope } from './errors'
import type { TokenResponse } from './types'

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly details: unknown[] | undefined

  constructor(status: number, code: string, message: string, details?: unknown[]) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

type Method = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

export interface RequestOptions {
  method?: Method
  body?: unknown
  signal?: AbortSignal
  /**
   * `session` (default): use the stored session token and refresh it on 401.
   * `none`: anonymous request (login, health).
   * A string: use exactly this access token, no refresh (e.g. verifying a fresh login).
   */
  auth?: 'session' | 'none' | { token: string }
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

async function send(path: string, options: RequestOptions, accessToken: string | null): Promise<Response> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  // FormData (file uploads) sets its own multipart Content-Type with the boundary.
  const isForm = options.body instanceof FormData
  if (options.body !== undefined && !isForm) headers['Content-Type'] = 'application/json'
  if (accessToken !== null) headers.Authorization = `Bearer ${accessToken}`

  let body: BodyInit | undefined
  if (options.body instanceof FormData) body = options.body
  else if (options.body !== undefined) body = JSON.stringify(options.body)

  try {
    return await fetch(`${BASE_URL}${path}`, {
      method: options.method ?? 'GET',
      headers,
      body,
      signal: options.signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    throw new ApiError(0, 'network_error', 'Cannot reach the server. Check the connection and try again.')
  }
}

async function toApiError(response: Response): Promise<ApiError> {
  let payload: unknown = null
  try {
    payload = await response.json()
  } catch {
    // Non-JSON body (e.g. dev proxy error page) — handled below.
  }
  if (isApiErrorEnvelope(payload)) {
    const { code, message, details } = payload.error
    return new ApiError(response.status, code, message, details)
  }
  if (response.status >= 500) {
    return new ApiError(response.status, 'server_unavailable', 'The server is not responding. Try again in a moment.')
  }
  return new ApiError(response.status, 'http_error', `Request failed with status ${response.status}.`)
}

// Single-flight: parallel 401s share one refresh call, because the backend
// rotates refresh tokens (a second refresh with the old token would fail).
let refreshInFlight: Promise<string | null> | null = null

function refreshAccessToken(): Promise<string | null> {
  refreshInFlight ??= (async (): Promise<string | null> => {
    const session = sessionStore.get()
    if (session === null) return null

    const response = await send('/api/v1/auth/refresh', { method: 'POST', body: { refresh_token: session.refresh_token } }, null)
    if (response.status === 401) {
      sessionStore.end('expired')
      return null
    }
    if (!response.ok) throw await toApiError(response)

    const tokens = (await response.json()) as TokenResponse
    sessionStore.updateTokens(tokens)
    return tokens.access_token
  })().finally(() => {
    refreshInFlight = null
  })
  return refreshInFlight
}

async function parseBody<T>(response: Response): Promise<T> {
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

/** Sends the request with the right credentials; returns only a successful response. */
async function authorizedResponse(path: string, options: RequestOptions): Promise<Response> {
  const auth = options.auth ?? 'session'

  if (auth === 'none' || typeof auth === 'object') {
    const response = await send(path, options, auth === 'none' ? null : auth.token)
    if (!response.ok) throw await toApiError(response)
    return response
  }

  const token = sessionStore.get()?.access_token ?? null
  if (token === null) throw new ApiError(401, 'unauthenticated', 'Sign in to continue.')

  let response = await send(path, options, token)
  if (response.status === 401) {
    const freshToken = await refreshAccessToken()
    if (freshToken === null) throw new ApiError(401, 'session_expired', 'Your session has expired. Sign in again.')
    response = await send(path, options, freshToken)
  }
  if (!response.ok) throw await toApiError(response)
  return response
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  return parseBody<T>(await authorizedResponse(path, options))
}

export interface DownloadedFile {
  blob: Blob
  filename: string | null
}

/** Binary download (attachments), with the same auth and token refresh as JSON calls. */
export async function apiDownload(path: string, signal?: AbortSignal): Promise<DownloadedFile> {
  const response = await authorizedResponse(path, { signal })
  return { blob: await response.blob(), filename: filenameFromDisposition(response.headers.get('Content-Disposition')) }
}

function filenameFromDisposition(header: string | null): string | null {
  if (header === null) return null
  const encoded = /filename\*=UTF-8''([^;]+)/i.exec(header)?.[1]
  if (encoded !== undefined) {
    try {
      return decodeURIComponent(encoded)
    } catch {
      // fall through to the plain form
    }
  }
  return /filename="([^"]+)"/i.exec(header)?.[1] ?? null
}
