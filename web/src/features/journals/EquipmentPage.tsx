import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { dashboardKeys } from '../../api/dashboard'
import { createEquipment, deleteEquipment, referenceKeys, updateEquipment } from '../../api/references'
import type { Equipment, EquipmentType } from '../../api/types'
import type { Session } from '../../auth/session'
import { PanelState } from '../../components/PanelState'
import { uk } from '../../i18n/uk'
import { routes } from '../../routes'
import { DocumentCell } from './DocumentCell'
import { useEquipment } from './queries'
import { canManage } from './helpers'
import { FormError, InlineDelete, JournalLayout, Section, Tag } from './ui'

const t = uk.journals
const tq = t.equipment

const TYPES: readonly EquipmentType[] = ['refrigeration', 'production', 'measuring', 'other']

function useInvalidate(orgId: string) {
  const queryClient = useQueryClient()
  return () => {
    void queryClient.invalidateQueries({ queryKey: referenceKeys.equipment(orgId) })
    // Safety-critical equipment without a document is a dashboard warning.
    void queryClient.invalidateQueries({ queryKey: dashboardKeys.all(orgId) })
  }
}

export function EquipmentPage({ session }: { session: Session }) {
  const orgId = session.organization_id
  const manager = canManage(session)
  const equipment = useEquipment(orgId)

  return (
    <JournalLayout backTo={routes.journalGroup('references')} kicker={tq.kicker} title={t.name.equipment}>
      {manager && (
        <Section title={tq.add}>
          <EquipmentForm orgId={orgId} />
        </Section>
      )}
      <Section title={t.name.equipment} aside={equipment.data && <span className="caps jsection__title">{equipment.data.length}</span>}>
        {!manager && <p className="jsection__note">{t.managersOnly}</p>}
        {equipment.data === undefined ? (
          <div className="jsection__pad">
            <PanelState error={equipment.isError ? equipment.error : undefined} onRetry={() => void equipment.refetch()} />
          </div>
        ) : equipment.data.length === 0 ? (
          <p className="jsection__empty">{tq.none}</p>
        ) : (
          <ul className="register">
            {equipment.data.map((item) => (
              <EquipmentRow key={item.id} orgId={orgId} item={item} manager={manager} />
            ))}
          </ul>
        )}
      </Section>
    </JournalLayout>
  )
}

function EquipmentForm({ orgId, initial, onDone }: { orgId: string; initial?: Equipment; onDone?: () => void }) {
  const invalidate = useInvalidate(orgId)
  const [name, setName] = useState(initial?.name ?? '')
  const [type, setType] = useState<EquipmentType>(initial?.type ?? 'refrigeration')
  const [frequency, setFrequency] = useState(initial?.frequency ?? '')
  const [amount, setAmount] = useState(String(initial?.amount ?? 1))
  const [critical, setCritical] = useState(initial?.affects_product_safety ?? false)
  const amountNumber = Number(amount)
  const valid = name.trim() !== '' && frequency.trim() !== '' && Number.isInteger(amountNumber) && amountNumber >= 1

  const mutation = useMutation({
    mutationFn: () => {
      const body = {
        name: name.trim(),
        type,
        frequency: frequency.trim(),
        amount: amountNumber,
        affects_product_safety: critical,
      }
      return initial ? updateEquipment(orgId, initial.id, body) : createEquipment(orgId, body)
    },
    onSuccess: () => {
      invalidate()
      if (!initial) {
        setName('')
        setFrequency('')
        setAmount('1')
        setCritical(false)
      }
      onDone?.()
    },
  })

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (valid && !mutation.isPending) mutation.mutate()
  }

  return (
    <form className={initial ? 'jform jform--tight' : 'jform'} onSubmit={submit}>
      <label className="field jform__wide">
        <span className="field__label caps">
          {tq.name} <span className="req">*</span>
        </span>
        <input className="input" value={name} maxLength={200} onChange={(e) => setName(e.target.value)} placeholder={tq.namePlaceholder} />
      </label>
      <label className="field">
        <span className="field__label caps">{tq.type}</span>
        <select className="input" value={type} onChange={(e) => setType(e.target.value as EquipmentType)}>
          {TYPES.map((value) => (
            <option key={value} value={value}>
              {tq.types[value]}
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        <span className="field__label caps">
          {tq.frequency} <span className="req">*</span>
        </span>
        <input className="input" value={frequency} maxLength={200} onChange={(e) => setFrequency(e.target.value)} placeholder={tq.frequencyPlaceholder} />
      </label>
      <label className="field">
        <span className="field__label caps">{tq.amount}</span>
        <input className="input" type="number" min={1} step={1} inputMode="numeric" value={amount} onChange={(e) => setAmount(e.target.value)} />
      </label>
      <label className="jform__check jform__wide">
        <input type="checkbox" checked={critical} onChange={(e) => setCritical(e.target.checked)} />
        {tq.safety}
      </label>
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

function EquipmentRow({ orgId, item, manager }: { orgId: string; item: Equipment; manager: boolean }) {
  const invalidate = useInvalidate(orgId)
  const [editing, setEditing] = useState(false)
  const remove = useMutation({ mutationFn: () => deleteEquipment(orgId, item.id), onSuccess: invalidate })
  const missingCritical = item.affects_product_safety && item.attachment_id === null

  if (editing) {
    return (
      <li className="reg-row reg-row--editing">
        <EquipmentForm orgId={orgId} initial={item} onDone={() => setEditing(false)} />
      </li>
    )
  }

  return (
    <li className={`reg-row${missingCritical ? ' reg-row--crit' : ''}`}>
      <p className="reg-row__date">× {item.amount}</p>
      <div className="reg-row__main">
        <p className="reg-row__title">{item.name}</p>
        <p className="reg-row__meta caps">
          {tq.types[item.type]} / {tq.maintenance(item.frequency)}
        </p>
        {item.affects_product_safety && <Tag tone="ink">{tq.safetyTag}</Tag>}
      </div>
      <div className="reg-row__side">
        <DocumentCell
          orgId={orgId}
          owner="equipment"
          ownerId={item.id}
          attachmentId={item.attachment_id}
          manager={manager}
          critical={item.affects_product_safety}
          onChanged={invalidate}
        />
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
