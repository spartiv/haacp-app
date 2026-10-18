import { useInfiniteQuery } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'
import { controlKeys, listAuditEvents } from '../../api/controls'
import type { AuditEvent } from '../../api/types'
import { StatusBadge } from '../../components/StatusBadge'
import { errorMessage, uk } from '../../i18n/uk'
import { formatTimestamp } from '../../lib/dates'
import { formatReading } from '../../lib/readings'

const t = uk.audit

interface AuditDrawerProps {
  orgId: string
  recordId: string
  title: string
  onClose: () => void
}

/** Read-only, append-only timeline. Native <dialog>: focus trap + Esc for free. */
export function AuditDrawer({ orgId, recordId, title, onClose }: AuditDrawerProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const dialog = dialogRef.current
    if (dialog && !dialog.open) dialog.showModal()
  }, [])

  const query = useInfiniteQuery({
    queryKey: controlKeys.audit(orgId, recordId),
    queryFn: ({ pageParam, signal }) => listAuditEvents(orgId, recordId, pageParam, signal),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
  })

  const events = query.data?.pages.flatMap((page) => page.items) ?? []

  return (
    <dialog
      ref={dialogRef}
      className="audit-drawer"
      aria-labelledby="audit-title"
      onClose={onClose}
      onClick={(event) => {
        if (event.target === dialogRef.current) dialogRef.current.close() // backdrop click
      }}
    >
      <div className="audit-drawer__panel">
        <header className="audit-drawer__head">
          <p className="audit-drawer__kicker caps">{t.kicker}</p>
          <h2 className="audit-drawer__title caps" id="audit-title">
            {title}
          </h2>
          <button className="btn btn--secondary caps" type="button" onClick={() => dialogRef.current?.close()}>
            {uk.common.close}
          </button>
        </header>

        {query.isPending ? (
          <p className="audit-state caps" role="status">
            {uk.common.loading}
          </p>
        ) : query.isError ? (
          <div className="sheet-error" role="alert">
            <p className="sheet-error__label caps">{uk.common.error}</p>
            <p>
              {t.loadFailed} {errorMessage(query.error)}
            </p>
            <button className="btn btn--primary caps" type="button" onClick={() => void query.refetch()}>
              {uk.common.retry}
            </button>
          </div>
        ) : events.length === 0 ? (
          <p className="audit-state">{t.empty}</p>
        ) : (
          <>
            <ol className="audit-list">
              {events.map((event) => (
                <AuditEntry key={event.id} event={event} />
              ))}
            </ol>
            {query.hasNextPage && (
              <button
                className="btn btn--secondary btn--wide caps"
                type="button"
                onClick={() => void query.fetchNextPage()}
                disabled={query.isFetchingNextPage}
              >
                {query.isFetchingNextPage ? uk.common.loading : t.loadOlder}
              </button>
            )}
            {!query.hasNextPage && <p className="audit-end caps">{t.start}</p>}
          </>
        )}
      </div>
    </dialog>
  )
}

function AuditEntry({ event }: { event: AuditEvent }) {
  const time = <time dateTime={event.created_at}>{formatTimestamp(event.created_at)}</time>

  if (event.event_type === 'record_submitted') {
    return (
      <li className="audit-entry audit-entry--submitted">
        <p className="audit-entry__stamp caps">{uk.record.submitted}</p>
        <p className="audit-entry__meta caps">
          #{event.seq} / {time} / {event.actor.full_name}
        </p>
      </li>
    )
  }

  const amended = event.event_type === 'item_amended'
  return (
    <li className={`audit-entry${amended ? ' audit-entry--amended' : ''}`}>
      <p className="audit-entry__meta caps">
        #{event.seq} / {time}
        {amended && <span className="audit-entry__tag"> {t.amendment}</span>}
      </p>
      <p className="audit-entry__item">{event.item_label ?? t.removedItem}</p>
      <p className="audit-entry__transition">
        {event.previous_status && <StatusBadge status={event.previous_status} />}
        <span aria-label={t.changedTo}> → </span>
        {event.new_status && <StatusBadge status={event.new_status} />}
        {event.numeric_value !== null && (
          <span className="audit-entry__reading">{formatReading(event.numeric_value, event.item_unit)}</span>
        )}
      </p>
      {event.corrective_action && (
        <p className="audit-entry__note">
          <span className="caps">{t.correctiveAction}</span> {event.corrective_action}
        </p>
      )}
      {event.amendment_reason && (
        <p className="audit-entry__note">
          <span className="caps">{t.reason}</span> {event.amendment_reason}
        </p>
      )}
      <p className="audit-entry__actor caps">
        {uk.performer.did(event.performed_by.full_name)}
        {event.performed_by.id !== event.actor.id && (
          <span className="audit-entry__via"> / {uk.performer.via(event.actor.full_name)}</span>
        )}
      </p>
    </li>
  )
}
