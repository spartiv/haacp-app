import { useQueryClient } from '@tanstack/react-query'
import { errorCode, errorMessage, uk } from '../i18n/uk'
import './PanelState.css'

/** Inline loading / error line, so one failed request never blanks the whole dashboard. */
export function PanelState({ error, onRetry }: { error?: unknown; onRetry?: () => void }) {
  const queryClient = useQueryClient()
  // After an outage every panel has failed: one retry reloads all of them.
  const retryAll = () => {
    onRetry?.()
    void queryClient.refetchQueries({ type: 'active', predicate: (query) => query.state.status === 'error' })
  }
  if (error === undefined || error === null) {
    return (
      <p className="panel-state caps" role="status">
        {uk.common.loading}
      </p>
    )
  }
  return (
    <div className="panel-state panel-state--error" role="alert">
      <p>
        <span className="caps">{uk.common.error}</span> {errorMessage(error)}{' '}
        <span className="panel-state__code caps">
          {uk.common.code}: {errorCode(error)}
        </span>
      </p>
      {onRetry && (
        <button className="btn btn--secondary caps" type="button" onClick={retryAll}>
          {uk.common.retry}
        </button>
      )}
    </div>
  )
}
