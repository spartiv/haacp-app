import { useMutation } from '@tanstack/react-query'
import { useRef } from 'react'
import { attachDocument, detachDocument, downloadAttachment, type DocumentOwner } from '../../api/references'
import { errorMessage, uk } from '../../i18n/uk'
import { InlineDelete, Tag } from './ui'

const td = uk.journals.document

/** Same limits as the backend: PDF / PNG / JPEG. */
const ACCEPT = '.pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg'

interface DocumentCellProps {
  orgId: string
  owner: DocumentOwner
  ownerId: string
  attachmentId: string | null
  manager: boolean
  /** Safety-critical equipment without a document is flagged on the dashboard too. */
  critical?: boolean
  onChanged: () => void
}

/** A passport / manual / safety data sheet attached to one reference row. */
export function DocumentCell({ orgId, owner, ownerId, attachmentId, manager, critical = false, onChanged }: DocumentCellProps) {
  const fileInput = useRef<HTMLInputElement>(null)

  const download = useMutation({
    mutationFn: (id: string) => downloadAttachment(orgId, id),
    onSuccess: ({ blob, filename }) => {
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename ?? 'document'
      link.click()
      setTimeout(() => URL.revokeObjectURL(url), 10_000)
    },
  })
  const upload = useMutation({
    mutationFn: (file: File) => attachDocument(orgId, owner, ownerId, file),
    onSuccess: onChanged,
  })
  const detach = useMutation({
    mutationFn: () => detachDocument(orgId, owner, ownerId),
    onSuccess: onChanged,
  })

  const error = download.error ?? upload.error

  return (
    <div className="doc-cell">
      {attachmentId === null ? (
        <Tag tone={critical ? 'crit' : 'muted'}>{critical ? td.missingCritical : td.none}</Tag>
      ) : (
        <button className="link-btn caps" type="button" onClick={() => download.mutate(attachmentId)} disabled={download.isPending}>
          {download.isPending ? td.downloading : `↓ ${td.download}`}
        </button>
      )}

      {manager && (
        <span className="reg-row__tools">
          <input
            ref={fileInput}
            type="file"
            accept={ACCEPT}
            hidden
            onChange={(event) => {
              const file = event.target.files?.[0]
              event.target.value = '' // the same file can be chosen again after an error
              if (file) upload.mutate(file)
            }}
          />
          <button
            className="link-btn caps"
            type="button"
            onClick={() => fileInput.current?.click()}
            disabled={upload.isPending}
            title={td.hint}
          >
            {upload.isPending ? td.uploading : attachmentId === null ? `+ ${td.upload}` : td.replace}
          </button>
          {attachmentId !== null && (
            <InlineDelete
              label={td.remove}
              question={`${td.remove}?`}
              onConfirm={() => detach.mutate()}
              pending={detach.isPending}
              error={detach.error}
            />
          )}
        </span>
      )}

      {error !== null && (
        <p className="doc-cell__error" role="alert">
          {errorMessage(error)}
        </p>
      )}
    </div>
  )
}
