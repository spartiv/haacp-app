import { useActionState, useState } from 'react'
import { ApiError } from '../../api/client'
import { readRememberedLogin, sessionStore } from '../../auth/session'
import { type PendingSignIn, signIn } from '../../auth/signIn'
import { errorCode, errorMessage, uk } from '../../i18n/uk'
import { OrgPicker } from './OrgPicker'
import './LoginScreen.css'

const t = uk.login

type Field = 'email' | 'password'

interface LoginFormState {
  email: string
  fieldErrors: Partial<Record<Field, string>>
  error: unknown
  /** Set when the account has several organizations: show the picker. */
  pending: PendingSignIn | null
}

async function submitLogin(_previous: LoginFormState, formData: FormData): Promise<LoginFormState> {
  const email = String(formData.get('email') ?? '').trim()
  const password = String(formData.get('password') ?? '')

  const fieldErrors: LoginFormState['fieldErrors'] = {}
  if (email === '') fieldErrors.email = t.emailRequired
  if (password === '') fieldErrors.password = t.passwordRequired
  if (Object.keys(fieldErrors).length > 0) return { email, fieldErrors, error: null, pending: null }

  try {
    const pending = await signIn({ email, password })
    return { email, fieldErrors: {}, error: null, pending }
  } catch (error) {
    return { email, fieldErrors: {}, error, pending: null }
  }
}

function errorLabel(error: unknown): string {
  if (!(error instanceof ApiError)) return uk.common.error
  if (error.status === 401 || error.status === 403) return t.denied
  if (error.status === 0 || error.status >= 500) return t.noConnection
  return uk.common.error
}

export function LoginScreen() {
  const [remembered] = useState(readRememberedLogin)
  const [initialState] = useState<LoginFormState>(() => ({
    email: remembered?.email ?? '',
    fieldErrors: {},
    error: null,
    pending: null,
  }))
  const [state, formAction, isSubmitting] = useActionState(submitLogin, initialState)
  // The picker is dismissed locally ("other account"), without another form action.
  const [dismissed, setDismissed] = useState<PendingSignIn | null>(null)
  const endNotice =
    state !== initialState
      ? null
      : sessionStore.endReason === 'expired'
        ? t.expired
        : sessionStore.endReason === 'access_revoked'
          ? t.accessRevoked
          : null
  const picking = state.pending !== null && state.pending !== dismissed ? state.pending : null

  const fieldProps = (field: Field) => {
    const message = state.fieldErrors[field]
    return {
      id: `login-${field}`,
      name: field,
      className: message ? 'login-input login-input--invalid' : 'login-input',
      'aria-invalid': message ? true : undefined,
      'aria-describedby': message ? `login-${field}-error` : undefined,
    }
  }

  const fieldError = (field: Field) => {
    const message = state.fieldErrors[field]
    return message ? (
      <p className="login-field-error" id={`login-${field}-error`}>
        {message}
      </p>
    ) : null
  }

  return (
    <div className="login-page">
      <section className="login-brand" aria-label="HACCP">
        <p className="login-brand__title">НАССР</p>
        <p className="login-brand__sub">{t.brandSub}</p>
      </section>

      <div className="login-sheet-stack">
        {picking ? (
          <OrgPicker
            pending={picking}
            // Only the same account's last choice is meaningful.
            lastUsedId={remembered?.email === picking.email ? remembered.organization_id : null}
            onBack={() => setDismissed(picking)}
          />
        ) : (
          <form className="login-sheet" action={formAction} noValidate aria-labelledby="login-title">
            <h1 className="login-sheet__title caps" id="login-title">
              {t.title}
            </h1>
            <p className="login-sheet__hint">{t.hint}</p>

            {endNotice && (
              <p className="login-notice caps" role="status">
                {endNotice}
              </p>
            )}

            {state.error !== null && (
              <div className="login-alert" role="alert">
                <p className="login-alert__label caps">{errorLabel(state.error)}</p>
                <p className="login-alert__message">{errorMessage(state.error)}</p>
                <p className="login-alert__code caps">
                  {uk.common.code}: {errorCode(state.error)}
                </p>
              </div>
            )}

            <div className="login-field">
              <label className="login-label caps" htmlFor="login-email">
                {t.email}
              </label>
              <input
                {...fieldProps('email')}
                type="email"
                autoComplete="username"
                inputMode="email"
                spellCheck={false}
                defaultValue={state.email}
                key={`email-${state.email}`}
              />
              {fieldError('email')}
            </div>

            <div className="login-field">
              <label className="login-label caps" htmlFor="login-password">
                {t.password}
              </label>
              <input {...fieldProps('password')} type="password" autoComplete="current-password" />
              {fieldError('password')}
            </div>

            <button className="login-submit caps" type="submit" disabled={isSubmitting} aria-busy={isSubmitting}>
              {isSubmitting ? t.submitting : `[ ${t.submit} ]`}
            </button>

            <p className="login-sheet__foot caps">{t.foot}</p>
          </form>
        )}
      </div>
    </div>
  )
}
