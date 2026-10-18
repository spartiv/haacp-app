// Building blocks shared by every journal screen, so they all look and behave alike.
import { useState, type ReactNode } from 'react'
import { Link } from 'react-router'
import { PanelState } from '../../components/PanelState'
import { errorMessage, uk } from '../../i18n/uk'
import { useOrgToday } from '../controls/useOrgToday'
import './journals.css'

const t = uk.journals

interface JournalLayoutProps {
  backTo: string
  kicker: string
  title: string
  aside?: ReactNode
  children: ReactNode
}

export function JournalLayout({ backTo, kicker, title, aside, children }: JournalLayoutProps) {
  return (
    <div className="jpage">
      <Link className="jpage-back caps" to={backTo}>
        {t.back}
      </Link>
      <header className="jpage-head">
        <div>
          <p className="jpage-head__kicker caps">{kicker}</p>
          <h1 className="jpage-head__title">{title}</h1>
        </div>
        {aside !== undefined && <div className="jpage-head__aside">{aside}</div>}
      </header>
      {children}
    </div>
  )
}

interface SectionProps {
  title: string
  aside?: ReactNode
  children: ReactNode
  id?: string
}

/** One white panel with a title strip. */
export function Section({ title, aside, children, id }: SectionProps) {
  const headingId = id ?? `section-${title}`
  return (
    <section className="jsection" aria-labelledby={headingId}>
      <header className="jsection__head">
        <h2 className="jsection__title caps" id={headingId}>
          {title}
        </h2>
        {aside}
      </header>
      {children}
    </section>
  )
}

/** Waits for the organization's "today" (server, org timezone) before rendering dated forms. */
export function WithToday({ orgId, children }: { orgId: string; children: (today: string) => ReactNode }) {
  const query = useOrgToday(orgId)
  if (query.data === undefined) {
    return (
      <div className="jsection">
        <div className="jsection__pad">
          <PanelState error={query.isError ? query.error : undefined} onRetry={() => void query.refetch()} />
        </div>
      </div>
    )
  }
  return <>{children(query.data)}</>
}

interface ChoiceProps<T extends string> {
  value: T | null
  options: readonly { value: T; label: string; bad?: boolean }[]
  onChange: (value: T) => void
  labelledBy: string
  disabled?: boolean
}

/**
 * Segmented choice (yes/no, pass/deviation). An option marked `bad` is the one
 * that means a deviation; when chosen it is outlined in red as well as filled.
 */
export function Choice<T extends string>({ value, options, onChange, labelledBy, disabled }: ChoiceProps<T>) {
  return (
    <div className="toggle-group" role="radiogroup" aria-labelledby={labelledBy}>
      {options.map((option) => {
        const on = value === option.value
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={on}
            className={`toggle caps${on ? ' toggle--on' : ''}${on && option.bad ? ' toggle--bad' : ''}`}
            disabled={disabled}
            onClick={() => onChange(option.value)}
          >
            {option.label}
          </button>
        )
      })}
    </div>
  )
}

/** Delete with a second, explicit confirmation step (no browser dialogs). */
export function InlineDelete({
  onConfirm,
  pending,
  error,
  label = t.delete,
  question = t.confirmDelete,
}: {
  onConfirm: () => void
  pending: boolean
  error: unknown
  label?: string
  question?: string
}) {
  const [asking, setAsking] = useState(false)
  if (!asking) {
    return (
      <button className="link-btn caps" type="button" onClick={() => setAsking(true)}>
        {label}
      </button>
    )
  }
  return (
    <span className="inline-confirm" role="group" aria-label={question}>
      <span className="inline-confirm__q caps">{question}</span>
      <button className="btn btn--danger btn--sm caps" type="button" onClick={onConfirm} disabled={pending}>
        {pending ? t.deleting : t.confirmYes}
      </button>
      <button className="btn btn--secondary btn--sm caps" type="button" onClick={() => setAsking(false)} disabled={pending}>
        {uk.common.cancel}
      </button>
      {error !== null && error !== undefined && (
        <span className="inline-confirm__error" role="alert">
          {errorMessage(error)}
        </span>
      )}
    </span>
  )
}

export function FormError({ error }: { error: unknown }) {
  if (error === null || error === undefined) return null
  return (
    <p className="form-error" role="alert">
      {errorMessage(error)}
    </p>
  )
}

export function ShowMore({ remaining, onMore }: { remaining: number; onMore: () => void }) {
  if (remaining === 0) return null
  return (
    <div className="jsection__pad">
      <button className="btn btn--secondary btn--wide caps" type="button" onClick={onMore}>
        {t.showMore(Math.min(remaining, 30))}
      </button>
    </div>
  )
}

/** A status tag: text + border pattern + color, never color alone (DESIGN.md §5). */
export function Tag({ tone, children }: { tone: 'ok' | 'crit' | 'warn' | 'muted' | 'ink'; children: ReactNode }) {
  return <span className={`tag tag--${tone} caps`}>{children}</span>
}

/** "Виконав(ла): X / обліковий запис: Y" — the account only when it differs from the person. */
export function PeopleLine({ names, performedBy, savedBy }: { names: Map<string, string>; performedBy: string; savedBy: string }) {
  if (names.size === 0) return null
  const name = (id: string) => names.get(id) ?? uk.performer.unknown
  return (
    <p className="reg-row__meta caps">
      {uk.performer.did(name(performedBy))}
      {performedBy !== savedBy && <span className="reg-row__via"> / {uk.performer.via(name(savedBy))}</span>}
    </p>
  )
}
