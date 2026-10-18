import type { ReactNode } from 'react'
import { uk } from '../../i18n/uk'
import './LoginScreen.css'

/** Signed-out frame shared by login and sign-up: brand on the left, one sheet on the right. */
export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="login-page">
      <section className="login-brand" aria-label="HACCP">
        <p className="login-brand__title">НАССР</p>
        <p className="login-brand__sub">{uk.login.brandSub}</p>
      </section>
      <div className="login-sheet-stack">{children}</div>
    </div>
  )
}
