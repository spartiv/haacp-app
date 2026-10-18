import { QueryClient } from '@tanstack/react-query'
import { ApiError } from '../api/client'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // A sheet can be filled from several devices at once: refetch on focus, keep data briefly fresh.
      staleTime: 10_000,
      refetchOnWindowFocus: true,
      // 4xx won't fix itself on retry; network/5xx might — but retry once, fast,
      // so an outage shows its error (with a retry button) within about a second.
      retry: (failureCount, error) =>
        !(error instanceof ApiError && error.status >= 400 && error.status < 500) && failureCount < 1,
      retryDelay: 800,
    },
    mutations: { retry: false },
  },
})
