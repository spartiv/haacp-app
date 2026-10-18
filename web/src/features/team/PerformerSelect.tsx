import { useId } from 'react'
import type { Session } from '../../auth/session'
import { uk } from '../../i18n/uk'
import type { PerformerChoice } from './performer'
import './performer.css'

const t = uk.performer

/** "Виконавець" picker. Hidden for a one-person team, where it would only add noise. */
export function PerformerSelect({ session, choice, wide = false }: { session: Session; choice: PerformerChoice; wide?: boolean }) {
  const id = useId()
  if (choice.active.length < 2) return null
  return (
    <div className={`performer${wide ? ' performer--wide' : ''}`}>
      <label className="performer__label caps" htmlFor={id}>
        {t.label}
      </label>
      <select className="performer__select" id={id} value={choice.performerId} onChange={(e) => choice.setPerformer(e.target.value)} aria-describedby={`${id}-hint`}>
        {choice.active.map((member) => (
          <option key={member.user_id} value={member.user_id}>
            {member.user_id === session.user.id ? t.you(member.full_name) : member.full_name}
          </option>
        ))}
      </select>
      <p className="performer__hint" id={`${id}-hint`}>
        {t.hint}
      </p>
    </div>
  )
}
