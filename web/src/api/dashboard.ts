import { orgBase } from './base'
import { apiRequest } from './client'
import type { DashboardResponse } from './types'

export const dashboardKeys = {
  all: (organizationId: string) => ['dashboard', organizationId] as const,
  summary: (organizationId: string) => ['dashboard', organizationId, 'summary'] as const,
}

export function getDashboard(organizationId: string, signal?: AbortSignal): Promise<DashboardResponse> {
  return apiRequest<DashboardResponse>(`${orgBase(organizationId)}/dashboard`, { signal })
}
