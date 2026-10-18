import { useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router'
import { listMyOrganizations, meKeys } from '../../api/me'
import { type Session, sessionStore } from '../../auth/session'
import { signOut } from '../../auth/signIn'
import { uk } from '../../i18n/uk'
import { routes } from '../../routes'
import './AppShell.css'

const t = uk.shell

/** Signed-in frame: charcoal bar with section tabs, then the routed page. */
export function AppShell({ session }: { session: Session }) {
  const [signingOut, setSigningOut] = useState(false)
  const onControlSheet = useLocation().pathname.startsWith('/controls/')
  useMembershipGuard(session)

  const handleSignOut = () => {
    setSigningOut(true)
    void signOut()
  }

  return (
    <div className="shell">
      <header className="shell-bar caps">
        <span className="shell-bar__title">
          НАССР / <span title={session.organization_id}>{session.organization_name}</span>
        </span>
        <span className="shell-bar__meta">
          <span>{session.user.full_name}</span>
          <button className="shell-bar__signout caps" type="button" onClick={handleSignOut} disabled={signingOut}>
            {t.signOut}
          </button>
        </span>
      </header>

      <nav className="shell-nav caps" aria-label={t.nav}>
        <NavLink to={routes.dashboard} end className="shell-nav__link">
          {t.dashboard}
        </NavLink>
        {/* The daily and monthly sheets are journals too: keep this tab lit on them. */}
        <NavLink
          to={routes.journals}
          className={({ isActive }) => `shell-nav__link${isActive || onControlSheet ? ' active' : ''}`}
        >
          {t.journals}
        </NavLink>
      </nav>

      <main className="shell-main">
        <Outlet />
      </main>
    </div>
  )
}

/**
 * Re-checks the stored organization against the server on load and on focus.
 * If the membership is gone (removed, or the account belongs to another
 * database), the session ends with a clear reason instead of every screen
 * failing with "forbidden". Keeps the organization name/role current too.
 */
function useMembershipGuard(session: Session) {
  const { data } = useQuery({
    queryKey: meKeys.organizations,
    queryFn: ({ signal }) => listMyOrganizations(undefined, signal),
    staleTime: 5 * 60_000,
  })
  useEffect(() => {
    if (data === undefined) return
    const membership = data.find((org) => org.organization_id === session.organization_id)
    if (membership === undefined) sessionStore.end('access_revoked')
    else sessionStore.updateOrganization(membership)
  }, [data, session.organization_id])
}
