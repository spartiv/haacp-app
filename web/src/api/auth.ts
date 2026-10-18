import { apiRequest } from './client'
import type { AuthResponse, LoginRequest, SignupRequest } from './types'

export function login(body: LoginRequest): Promise<AuthResponse> {
  return apiRequest<AuthResponse>('/api/v1/auth/login', { method: 'POST', body, auth: 'none' })
}

/** Creates the account and a new venue with this person as its owner. */
export function signup(body: SignupRequest): Promise<AuthResponse> {
  return apiRequest<AuthResponse>('/api/v1/auth/signup', { method: 'POST', body, auth: 'none' })
}

export function logout(refreshToken: string): Promise<void> {
  return apiRequest<void>('/api/v1/auth/logout', {
    method: 'POST',
    body: { refresh_token: refreshToken },
    auth: 'none',
  })
}
