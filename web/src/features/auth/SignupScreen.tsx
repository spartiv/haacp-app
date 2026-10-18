import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link } from 'react-router'
import { ApiError } from '../../api/client'
import { signUp } from '../../auth/signIn'
import { errorCode, errorMessage, uk } from '../../i18n/uk'
import { routes } from '../../routes'
import { AuthLayout } from './AuthLayout'

const t = uk.signup

type Field = 'email' | 'password' | 'fullName' | 'organizationName'
type Errors = Partial<Record<Field, string>>

const MIN_PASSWORD = 8 // same rule as the server
const EMAIL_SHAPE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

/**
 * Two short steps on one sheet: (1) email + password, (2) name + venue.
 * Nothing is sent until step 2, which creates the account and the venue
 * (with this person as owner) and signs them in.
 */
export function SignupScreen() {
  const [step, setStep] = useState<1 | 2>(1)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [organizationName, setOrganizationName] = useState('')
  const [errors, setErrors] = useState<Errors>({})
  const [submitError, setSubmitError] = useState<unknown>(null)
  const [submitting, setSubmitting] = useState(false)
  const firstField = useRef<HTMLInputElement>(null)

  // Move focus to the first field of each step (keyboard and screen readers).
  useEffect(() => firstField.current?.focus(), [step])

  const next = (event: FormEvent) => {
    event.preventDefault()
    const found: Errors = {}
    if (!EMAIL_SHAPE.test(email.trim())) found.email = t.emailInvalid
    if (password.length < MIN_PASSWORD) found.password = t.passwordShort
    setErrors(found)
    if (Object.keys(found).length === 0) {
      setSubmitError(null)
      setStep(2)
    }
  }

  const create = async (event: FormEvent) => {
    event.preventDefault()
    const found: Errors = {}
    if (!fullName.trim()) found.fullName = t.nameRequired
    if (!organizationName.trim()) found.organizationName = t.orgRequired
    setErrors(found)
    if (Object.keys(found).length > 0 || submitting) return

    setSubmitting(true)
    setSubmitError(null)
    try {
      // On success the session starts and the app replaces this screen.
      await signUp({ email: email.trim(), password, fullName: fullName.trim(), organizationName: organizationName.trim() })
    } catch (error) {
      setSubmitting(false)
      if (error instanceof ApiError && error.code === 'email_already_registered') {
        setErrors({ email: errorMessage(error) })
        setStep(1)
        return
      }
      setSubmitError(error)
    }
  }

  const fieldProps = (field: Field) => ({
    id: `signup-${field}`,
    className: errors[field] ? 'login-input login-input--invalid' : 'login-input',
    'aria-invalid': errors[field] ? true : undefined,
    'aria-describedby': errors[field] ? `signup-${field}-error` : `signup-${field}-help`,
  })

  const help = (field: Field, text?: string) =>
    errors[field] ? (
      <p className="login-field-error" id={`signup-${field}-error`}>
        {errors[field]}
      </p>
    ) : text ? (
      <p className="login-field-help" id={`signup-${field}-help`}>
        {text}
      </p>
    ) : null

  return (
    <AuthLayout>
      {step === 1 ? (
        <form className="login-sheet" onSubmit={next} noValidate aria-labelledby="signup-title">
          <p className="login-step caps">{t.step(1)}</p>
          <h1 className="login-sheet__title caps" id="signup-title">
            {t.title}
          </h1>
          <p className="login-sheet__hint">{t.hint}</p>

          <div className="login-field">
            <label className="login-label caps" htmlFor="signup-email">
              {uk.login.email}
            </label>
            <input
              {...fieldProps('email')}
              ref={firstField}
              type="email"
              autoComplete="username"
              inputMode="email"
              spellCheck={false}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            {help('email')}
          </div>

          <div className="login-field">
            <label className="login-label caps" htmlFor="signup-password">
              {uk.login.password}
            </label>
            <input
              {...fieldProps('password')}
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            {help('password', t.passwordHint)}
          </div>

          <button className="login-submit caps" type="submit">
            [ {t.next} ]
          </button>
          <p className="login-switch">
            {t.haveAccount}{' '}
            <Link className="login-switch__link caps" to={routes.dashboard}>
              {t.signIn}
            </Link>
          </p>
        </form>
      ) : (
        <form className="login-sheet" onSubmit={create} noValidate aria-labelledby="signup-about-title">
          <p className="login-step caps">{t.step(2)}</p>
          <h1 className="login-sheet__title caps" id="signup-about-title">
            {t.aboutTitle}
          </h1>
          <p className="login-sheet__hint">{t.aboutHint}</p>

          {submitError !== null && (
            <div className="login-alert" role="alert">
              <p className="login-alert__label caps">{uk.common.error}</p>
              <p className="login-alert__message">{errorMessage(submitError)}</p>
              <p className="login-alert__code caps">
                {uk.common.code}: {errorCode(submitError)}
              </p>
            </div>
          )}

          <div className="login-field">
            <label className="login-label caps" htmlFor="signup-fullName">
              {t.fullName}
            </label>
            <input
              {...fieldProps('fullName')}
              ref={firstField}
              autoComplete="name"
              maxLength={200}
              placeholder={t.fullNamePlaceholder}
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
            {help('fullName')}
          </div>

          <div className="login-field">
            <label className="login-label caps" htmlFor="signup-organizationName">
              {t.org}
            </label>
            <input
              {...fieldProps('organizationName')}
              autoComplete="organization"
              maxLength={200}
              placeholder={t.orgPlaceholder}
              value={organizationName}
              onChange={(e) => setOrganizationName(e.target.value)}
            />
            {help('organizationName')}
          </div>

          <button className="login-submit caps" type="submit" disabled={submitting} aria-busy={submitting}>
            {submitting ? t.creating : `[ ${t.create} ]`}
          </button>
          <button className="login-back caps" type="button" onClick={() => setStep(1)} disabled={submitting}>
            {t.back}
          </button>
        </form>
      )}
    </AuthLayout>
  )
}
