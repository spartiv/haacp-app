import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useId, useState, type FormEvent } from 'react'
import { createChemical, deleteChemical, referenceKeys, updateChemical } from '../../api/references'
import type { Chemical, ChemicalCategory } from '../../api/types'
import type { Session } from '../../auth/session'
import { PanelState } from '../../components/PanelState'
import { uk } from '../../i18n/uk'
import { routes } from '../../routes'
import { DocumentCell } from './DocumentCell'
import { useChemicals } from './queries'
import { canManage } from './helpers'
import { Choice, FormError, InlineDelete, JournalLayout, Section } from './ui'

const t = uk.journals
const tc = t.chemicals

const CATEGORIES: readonly ChemicalCategory[] = ['cleaning', 'disinfecting']

function useInvalidate(orgId: string) {
  const queryClient = useQueryClient()
  return () => void queryClient.invalidateQueries({ queryKey: referenceKeys.chemicals(orgId) })
}

export function ChemicalsPage({ session }: { session: Session }) {
  const orgId = session.organization_id
  const manager = canManage(session)
  const chemicals = useChemicals(orgId)

  return (
    <JournalLayout backTo={routes.journalGroup('references')} kicker={tc.kicker} title={t.name.chemicals}>
      {manager && (
        <Section title={tc.add}>
          <ChemicalForm orgId={orgId} />
        </Section>
      )}
      <Section title={t.name.chemicals} aside={chemicals.data && <span className="caps jsection__title">{chemicals.data.length}</span>}>
        {!manager && <p className="jsection__note">{t.managersOnly}</p>}
        {chemicals.data === undefined ? (
          <div className="jsection__pad">
            <PanelState error={chemicals.isError ? chemicals.error : undefined} onRetry={() => void chemicals.refetch()} />
          </div>
        ) : chemicals.data.length === 0 ? (
          <p className="jsection__empty">{tc.none}</p>
        ) : (
          <ul className="register register--two">
            {chemicals.data.map((item) => (
              <ChemicalRow key={item.id} orgId={orgId} item={item} manager={manager} />
            ))}
          </ul>
        )}
      </Section>
    </JournalLayout>
  )
}

function ChemicalForm({ orgId, initial, onDone }: { orgId: string; initial?: Chemical; onDone?: () => void }) {
  const id = useId()
  const invalidate = useInvalidate(orgId)
  const [name, setName] = useState(initial?.name ?? '')
  const [category, setCategory] = useState<ChemicalCategory>(initial?.category ?? 'cleaning')
  const valid = name.trim() !== ''

  const mutation = useMutation({
    mutationFn: () => {
      const body = { name: name.trim(), category }
      return initial ? updateChemical(orgId, initial.id, body) : createChemical(orgId, body)
    },
    onSuccess: () => {
      invalidate()
      if (!initial) setName('')
      onDone?.()
    },
  })

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (valid && !mutation.isPending) mutation.mutate()
  }

  return (
    <form className={initial ? 'jform jform--tight' : 'jform'} onSubmit={submit}>
      <label className="field">
        <span className="field__label caps">
          {tc.name} <span className="req">*</span>
        </span>
        <input className="input" value={name} maxLength={200} onChange={(e) => setName(e.target.value)} placeholder={tc.namePlaceholder} />
      </label>
      <div className="field">
        <span className="field__label caps" id={`${id}-cat`}>
          {tc.category}
        </span>
        <Choice
          value={category}
          labelledBy={`${id}-cat`}
          onChange={setCategory}
          options={CATEGORIES.map((value) => ({ value, label: tc.categories[value] ?? value }))}
        />
      </div>
      <div className="jform__actions">
        <button className="btn btn--primary caps" type="submit" disabled={!valid || mutation.isPending}>
          {mutation.isPending ? t.saving : initial ? t.save : `+ ${t.add}`}
        </button>
        {onDone && (
          <button className="btn btn--secondary caps" type="button" onClick={onDone} disabled={mutation.isPending}>
            {uk.common.cancel}
          </button>
        )}
      </div>
      <div className="jform__wide">
        <FormError error={mutation.error} />
      </div>
    </form>
  )
}

function ChemicalRow({ orgId, item, manager }: { orgId: string; item: Chemical; manager: boolean }) {
  const invalidate = useInvalidate(orgId)
  const [editing, setEditing] = useState(false)
  const remove = useMutation({ mutationFn: () => deleteChemical(orgId, item.id), onSuccess: invalidate })

  if (editing) {
    return (
      <li className="reg-row reg-row--editing">
        <ChemicalForm orgId={orgId} initial={item} onDone={() => setEditing(false)} />
      </li>
    )
  }

  return (
    <li className="reg-row">
      <div className="reg-row__main">
        <p className="reg-row__title">{item.name}</p>
        <p className="reg-row__meta caps">{tc.categories[item.category]}</p>
      </div>
      <div className="reg-row__side">
        <DocumentCell orgId={orgId} owner="chemicals" ownerId={item.id} attachmentId={item.attachment_id} manager={manager} onChanged={invalidate} />
        {manager && (
          <span className="reg-row__tools">
            <button className="link-btn caps" type="button" onClick={() => setEditing(true)}>
              {t.edit}
            </button>
            <InlineDelete onConfirm={() => remove.mutate()} pending={remove.isPending} error={remove.error} />
          </span>
        )}
      </div>
    </li>
  )
}
