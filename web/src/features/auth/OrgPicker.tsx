import type { MyOrganization } from '../../api/types'
import { cancelSignIn, completeSignIn, type PendingSignIn } from '../../auth/signIn'
import { uk } from '../../i18n/uk'

const t = uk.orgPicker

interface OrgPickerProps {
  pending: PendingSignIn
  lastUsedId: string | null
  onBack: () => void
}

/** Second login step, only for accounts with more than one organization. */
export function OrgPicker({ pending, lastUsedId, onBack }: OrgPickerProps) {
  const choose = (organization: MyOrganization) => completeSignIn(pending, organization)

  return (
    <section className="login-sheet" aria-labelledby="org-title">
      <h1 className="login-sheet__title caps" id="org-title">
        {t.title}
      </h1>
      <p className="login-sheet__hint">{t.hint}</p>

      <ul className="org-list">
        {pending.organizations.map((org) => (
          <li key={org.organization_id}>
            <button className="org-option" type="button" onClick={() => choose(org)}>
              <span className="org-option__name">{org.name}</span>
              <span className="org-option__meta caps">
                {t.role[org.role] ?? org.role}
                {org.title ? ` / ${org.title}` : ''}
                {org.organization_id === lastUsedId && <span className="org-option__last"> [ {t.lastUsed} ]</span>}
              </span>
            </button>
          </li>
        ))}
      </ul>

      <button
        className="btn btn--secondary btn--wide caps"
        type="button"
        onClick={() => {
          cancelSignIn(pending)
          onBack()
        }}
      >
        {t.back}
      </button>

      <p className="login-sheet__foot caps">{pending.email}</p>
    </section>
  )
}
