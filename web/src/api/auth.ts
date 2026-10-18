import { apiRequest } from './client'
import type { AuthResponse, LoginRequest } from './types'

export function login(body: LoginRequest): Promise<AuthResponse> {
  return apiRequest<AuthResponse>('/api/v1/auth/login', { method: 'POST', body, auth: 'none' })
}

export function logout(refreshToken: string): Promise<void> {
  return apiRequest<void>('/api/v1/auth/logout', {
    method: 'POST',
    body: { refresh_token: refreshToken },
    auth: 'none',
  })
}
