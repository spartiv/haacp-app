// The backend wraps every non-2xx response in this envelope (app/core/error_handlers.py).
// It is not described in openapi.json, so it is typed by hand here.

export interface ApiErrorBody {
  code: string
  message: string
  /** Present on 422 `validation_error` responses (Pydantic per-field errors). */
  details?: unknown[]
}

export interface ApiErrorEnvelope {
  error: ApiErrorBody
}

/** Error codes the UI branches on. Extend as screens need them. */
export const ErrorCode = {
  ControlRecordNotFilled: 'control_record_not_filled',
  FuturePeriodDate: 'future_period_date',
  Forbidden: 'forbidden',
  ValidationError: 'validation_error',
} as const

export function isApiErrorEnvelope(value: unknown): value is ApiErrorEnvelope {
  if (typeof value !== 'object' || value === null || !('error' in value)) return false
  const error: unknown = value.error
  return (
    typeof error === 'object' &&
    error !== null &&
    'code' in error &&
    typeof error.code === 'string' &&
    'message' in error &&
    typeof error.message === 'string'
  )
}
