import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useId, useState, type FormEvent } from 'react'
import { useSearchParams } from 'react-router'
import {
  batchKeys,
  createBatch,
  createProduct,
  createProductChecklistItem,
  deleteBatch,
  deleteProduct,
  deleteProductChecklistItem,
  listBatches,
  listProductChecklist,
} from '../../api/batches'
import { dashboardKeys } from '../../api/dashboard'
import type { Batch, Product, ProductChecklistItem } from '../../api/types'
import type { Session } from '../../auth/session'
import { PanelState } from '../../components/PanelState'
import { PresetChips } from '../../components/PresetChips'
import { StatusBadge } from '../../components/StatusBadge'
import { uk } from '../../i18n/uk'
import { formatShortDate } from '../../lib/dates'
import { routes } from '../../routes'
import { useProducts } from './queries'
import { PerformerSelect } from '../team/PerformerSelect'
import { useMemberNames, usePerformer } from '../team/performer'
import { canManage, MIN_TEXT, useShowMore, YES_NO } from './helpers'
import { Choice, FormError, InlineDelete, JournalLayout, PeopleLine, Section, ShowMore, WithToday } from './ui'

const t = uk.journals
const tb = t.batches

export function BatchesPage({ session }: { session: Session }) {
  return (
    <JournalLayout backTo={routes.journalGroup('events')} kicker={tb.kicker} title={t.name.batches}>
      <WithToday orgId={session.organization_id}>{(today) => <Batches session={session} today={today} />}</WithToday>
    </JournalLayout>
  )
}

function Batches({ session, today }: { session: Session; today: string }) {
  const orgId = session.organization_id
  const manager = canManage(session)
  const products = useProducts(orgId)
  const [searchParams, setSearchParams] = useSearchParams()
  const requested = searchParams.get('product')
  const product = products.data?.find((p) => p.id === requested) ?? products.data?.[0]

  const choose = (id: string) => setSearchParams({ product: id }, { replace: true })

  if (products.data === undefined) {
    return (
      <div className="jsection">
        <div className="jsection__pad">
          <PanelState error={products.isError ? products.error : undefined} onRetry={() => void products.refetch()} />
        </div>
      </div>
    )
  }

  return (
    <>
      <Section title={tb.productsLabel}>
        {products.data.length === 0 ? (
          <p className="jsection__empty">
            {tb.noProducts} {!manager && tb.noProductsStaff}
          </p>
        ) : (
          <div className="jsection__pad">
            <div className="pick-chips" role="group" aria-label={tb.productsLabel}>
              {products.data.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  className="pick-chip"
                  aria-pressed={p.id === product?.id}
                  onClick={() => choose(p.id)}
                >
                  {p.name}
                </button>
              ))}
            </div>
          </div>
        )}
        {manager && <AddProductForm orgId={orgId} onCreated={(created) => choose(created.id)} />}
      </Section>

      {product && <ProductJournal key={product.id} session={session} product={product} today={today} />}
    </>
  )
}

function AddProductForm({ orgId, onCreated }: { orgId: string; onCreated: (product: Product) => void }) {
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const mutation = useMutation({
    mutationFn: () => createProduct(orgId, name.trim()),
    onSuccess: (product) => {
      setName('')
      void queryClient.invalidateQueries({ queryKey: batchKeys.products(orgId) })
      onCreated(product)
    },
  })
  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (name.trim() && !mutation.isPending) mutation.mutate()
  }
  return (
    <form className="jform jform--split" onSubmit={submit}>
      <label className="field">
        <span className="field__label caps">{tb.productName}</span>
        <input className="input" value={name} maxLength={200} onChange={(e) => setName(e.target.value)} placeholder={tb.productPlaceholder} />
      </label>
      <div className="jform__actions">
        <button className="btn btn--secondary caps" type="submit" disabled={!name.trim() || mutation.isPending}>
          {mutation.isPending ? t.saving : `+ ${tb.addProduct}`}
        </button>
        <FormError error={mutation.error} />
      </div>
    </form>
  )
}

function ProductJournal({ session, product, today }: { session: Session; product: Product; today: string }) {
  const orgId = session.organization_id
  const checklist = useQuery({
    queryKey: batchKeys.checklist(orgId, product.id),
    queryFn: ({ signal }) => listProductChecklist(orgId, product.id, signal),
  })
  const batches = useQuery({
    queryKey: batchKeys.batches(orgId, product.id),
    queryFn: ({ signal }) => listBatches(orgId, product.id, signal),
  })
  const { visible, remaining, more } = useShowMore(batches.data)
  const names = useMemberNames(orgId)

  return (
    <>
      <ChecklistPanel session={session} product={product} items={checklist.data} error={checklist.isError ? checklist.error : undefined} retry={() => void checklist.refetch()} />

      {checklist.data && (
        <Section title={`${tb.newBatch}: ${product.name}`}>
          <BatchForm session={session} product={product} items={checklist.data} today={today} />
        </Section>
      )}

      <Section title={tb.list} aside={batches.data && <span className="caps jsection__title">{batches.data.length}</span>}>
        {batches.data === undefined ? (
          <div className="jsection__pad">
            <PanelState error={batches.isError ? batches.error : undefined} onRetry={() => void batches.refetch()} />
          </div>
        ) : batches.data.length === 0 ? (
          <p className="jsection__empty">{tb.none}</p>
        ) : (
          <>
            <ul className="register">
              {visible.map((batch) => (
                <BatchRow key={batch.id} orgId={orgId} product={product} batch={batch} items={checklist.data ?? []} names={names} />
              ))}
            </ul>
            <ShowMore remaining={remaining} onMore={more} />
          </>
        )}
      </Section>
    </>
  )
}

interface ChecklistPanelProps {
  session: Session
  product: Product
  items: ProductChecklistItem[] | undefined
  error: unknown
  retry: () => void
}

/** The product's reusable checklist. Owners/managers can add and remove questions. */
function ChecklistPanel({ session, product, items, error, retry }: ChecklistPanelProps) {
  const orgId = session.organization_id
  const manager = canManage(session)
  const [configuring, setConfiguring] = useState(false)
  const [label, setLabel] = useState('')
  const queryClient = useQueryClient()
  const key = batchKeys.checklist(orgId, product.id)

  const add = useMutation({
    mutationFn: () => createProductChecklistItem(orgId, product.id, label.trim()),
    onSuccess: () => {
      setLabel('')
      setConfiguring(true) // stay in edit mode after the first question
      void queryClient.invalidateQueries({ queryKey: key })
    },
  })
  const removeProduct = useMutation({
    mutationFn: () => deleteProduct(orgId, product.id),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: batchKeys.products(orgId) }),
  })

  const editing = manager && (configuring || items?.length === 0)

  return (
    <Section
      title={tb.checklist}
      aside={
        manager &&
        items !== undefined &&
        items.length > 0 && (
          <button className="link-btn caps" type="button" onClick={() => setConfiguring((value) => !value)}>
            {configuring ? tb.doneConfiguring : tb.configure}
          </button>
        )
      }
    >
      {items === undefined ? (
        <div className="jsection__pad">
          <PanelState error={error} onRetry={retry} />
        </div>
      ) : (
        <>
          <p className="jsection__note">{items.length === 0 ? tb.checklistEmpty : tb.checklistHint}</p>
          {items.length > 0 && (
            <ol className="register">
              {items.map((item, index) => (
                <ChecklistItemRow key={item.id} orgId={orgId} productId={product.id} item={item} index={index} editable={editing} />
              ))}
            </ol>
          )}
          {editing && (
            <form
              className="jform jform--split"
              onSubmit={(event) => {
                event.preventDefault()
                if (label.trim() && !add.isPending) add.mutate()
              }}
            >
              <label className="field jform__wide">
                <span className="field__label caps">{tb.addQuestion}</span>
                <input className="input" value={label} maxLength={500} onChange={(e) => setLabel(e.target.value)} placeholder={tb.questionPlaceholder} />
              </label>
              <div className="jform__actions">
                <button className="btn btn--secondary caps" type="submit" disabled={!label.trim() || add.isPending}>
                  {add.isPending ? t.saving : `+ ${tb.addQuestion}`}
                </button>
                <span className="jform__spacer" />
                <InlineDelete
                  label={`${t.delete}: ${product.name}`}
                  question={`${t.delete} «${product.name}»?`}
                  onConfirm={() => removeProduct.mutate()}
                  pending={removeProduct.isPending}
                  error={removeProduct.error}
                />
              </div>
              <div className="jform__wide">
                <FormError error={add.error} />
              </div>
            </form>
          )}
        </>
      )}
    </Section>
  )
}

function ChecklistItemRow(props: { orgId: string; productId: string; item: ProductChecklistItem; index: number; editable: boolean }) {
  const { orgId, productId, item, index, editable } = props
  const queryClient = useQueryClient()
  const remove = useMutation({
    mutationFn: () => deleteProductChecklistItem(orgId, productId, item.id),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: batchKeys.checklist(orgId, productId) }),
  })
  return (
    <li className="reg-row">
      <p className="reg-row__date">{String(index + 1).padStart(2, '0')}</p>
      <p className="reg-row__title">{item.label}</p>
      <div className="reg-row__side">
        {editable && <InlineDelete onConfirm={() => remove.mutate()} pending={remove.isPending} error={remove.error} />}
      </div>
    </li>
  )
}

type Answer = 'yes' | 'no'

function BatchForm(props: { session: Session; product: Product; items: ProductChecklistItem[]; today: string }) {
  const { session, product, items, today } = props
  const orgId = session.organization_id
  const performer = usePerformer(session)
  const id = useId()
  const queryClient = useQueryClient()
  const [number, setNumber] = useState('')
  const [name, setName] = useState('')
  const [date, setDate] = useState(today)
  const [answers, setAnswers] = useState<Record<string, Answer>>({})
  const [note, setNote] = useState('')
  const [action, setAction] = useState('')
  const [touched, setTouched] = useState(false)
  const [saved, setSaved] = useState(false)

  const deviation = items.some((item) => answers[item.id] === 'no')
  const problem = !number.trim()
    ? tb.needNumber
    : items.some((item) => answers[item.id] === undefined)
      ? tb.answerAll
      : deviation && action.trim().length < MIN_TEXT
        ? tb.needAction
        : null

  const mutation = useMutation({
    mutationFn: () =>
      createBatch(orgId, product.id, {
        number: number.trim(),
        name: name.trim() || null,
        production_date: date,
        answers: items.map((item) => ({ checklist_item_id: item.id, answer: answers[item.id] === 'yes' })),
        deviation_note: deviation ? note.trim() || null : null,
        corrective_action: deviation ? action.trim() : null,
        performed_by_user_id: performer.performerId,
      }),
    onSuccess: () => {
      setNumber('')
      setName('')
      setAnswers({})
      setNote('')
      setAction('')
      setTouched(false)
      setSaved(true)
      void queryClient.invalidateQueries({ queryKey: batchKeys.batches(orgId, product.id) })
      void queryClient.invalidateQueries({ queryKey: dashboardKeys.all(orgId) })
    },
  })

  const submit = (event: FormEvent) => {
    event.preventDefault()
    setTouched(true)
    setSaved(false)
    if (problem === null && !mutation.isPending) mutation.mutate()
  }

  return (
    <form className="jform" onSubmit={submit} noValidate>
      <PerformerSelect session={session} choice={performer} wide />
      <label className="field">
        <span className="field__label caps">
          {tb.number} <span className="req">*</span>
        </span>
        <input className="input" value={number} maxLength={100} onChange={(e) => setNumber(e.target.value)} />
      </label>
      <label className="field">
        <span className="field__label caps">{tb.nameOptional}</span>
        <input className="input" value={name} maxLength={200} onChange={(e) => setName(e.target.value)} />
      </label>
      <label className="field">
        <span className="field__label caps">
          {tb.productionDate} <span className="req">*</span>
        </span>
        <input className="input" type="date" value={date} max={today} onChange={(e) => e.target.value && setDate(e.target.value)} />
      </label>

      {items.length > 0 && (
        <ul className="qlist">
          {items.map((item) => (
            <li key={item.id} className={`qlist__row${answers[item.id] === 'no' ? ' qlist__row--bad' : ''}`}>
              <p className="qlist__label" id={`${id}-${item.id}`}>
                {item.label}
              </p>
              <Choice
                value={answers[item.id] ?? null}
                options={YES_NO}
                labelledBy={`${id}-${item.id}`}
                onChange={(value) => setAnswers((current) => ({ ...current, [item.id]: value }))}
              />
            </li>
          ))}
        </ul>
      )}

      {deviation && (
        <>
          <label className="field jform__wide">
            <span className="field__label caps">{tb.deviationNote}</span>
            <textarea className="input" rows={2} maxLength={2000} value={note} onChange={(e) => setNote(e.target.value)} placeholder={tb.deviationNotePlaceholder} />
          </label>
          <div className="field jform__wide">
            <label className="field__label caps" htmlFor={`${id}-action`}>
              {uk.controls.correctiveAction} <span className="req">{uk.controls.required}</span>
            </label>
            <textarea
              id={`${id}-action`}
              className="input"
              rows={3}
              maxLength={2000}
              value={action}
              onChange={(e) => setAction(e.target.value)}
              placeholder={uk.controls.actionPlaceholder}
            />
            <PresetChips value={action} onChange={setAction} />
          </div>
        </>
      )}

      <div className="jform__actions">
        <button className="btn btn--primary caps" type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? t.saving : deviation ? uk.controls.saveDeviation : t.save}
        </button>
        {saved && !mutation.isPending && (
          <p className="jform__saved caps" role="status">
            {t.entrySaved}
          </p>
        )}
      </div>
      {touched && problem !== null && <p className="form-error jform__wide" role="alert">{problem}</p>}
      <div className="jform__wide">
        <FormError error={mutation.error} />
      </div>
    </form>
  )
}

function BatchRow(props: { orgId: string; product: Product; batch: Batch; items: ProductChecklistItem[]; names: Map<string, string> }) {
  const { orgId, product, batch, items, names } = props
  const queryClient = useQueryClient()
  const remove = useMutation({
    mutationFn: () => deleteBatch(orgId, batch.id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: batchKeys.batches(orgId, product.id) })
      void queryClient.invalidateQueries({ queryKey: dashboardKeys.all(orgId) })
    },
  })
  const labels = new Map(items.map((item) => [item.id, item.label]))
  const failed = batch.answers.filter((answer) => !answer.answer)

  return (
    <li className={`reg-row${batch.has_deviation ? ' reg-row--crit' : ''}`}>
      <p className="reg-row__date">{formatShortDate(batch.production_date)}</p>
      <div className="reg-row__main">
        <p className="reg-row__title">
          № {batch.number}
          {batch.name && ` / ${batch.name}`}
        </p>
        {failed.length > 0 && (
          <ul className="reg-row__answers">
            {failed.map((answer) => (
              <li key={answer.checklist_item_id} className="bad">
                ✕ {labels.get(answer.checklist_item_id) ?? uk.audit.removedItem}
              </li>
            ))}
          </ul>
        )}
        {batch.deviation_note && <p className="reg-row__text">{batch.deviation_note}</p>}
        {batch.corrective_action && (
          <p className="reg-row__action">
            <span className="caps">{uk.controls.correctiveAction}:</span> {batch.corrective_action}
          </p>
        )}
        {batch.answers.length === 0 && <p className="reg-row__meta caps">{tb.noChecks}</p>}
        <PeopleLine names={names} performedBy={batch.performed_by_user_id} savedBy={batch.signatory_user_id} />
      </div>
      <div className="reg-row__side">
        <StatusBadge status={batch.has_deviation ? 'deviation' : 'pass'} />
        <InlineDelete onConfirm={() => remove.mutate()} pending={remove.isPending} error={remove.error} />
      </div>
    </li>
  )
}
