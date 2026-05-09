import { useState } from 'react'
import { telescopeGet, telescopePost, telescopePostWithQuery } from '../../api'
import { formatJson } from '../../formatJson'
import type { WithBusyFn } from '../mcp/types'

type Props = { withBusy: WithBusyFn; busy: boolean }

export function ModelInferencePanel({ withBusy, busy }: Props) {
  const [prompt, setPrompt] = useState('Local model smoke: respond with ok.')
  const [timeoutSec, setTimeoutSec] = useState(20)
  const [pollSec, setPollSec] = useState(0.5)
  const [lastSyncResult, setLastSyncResult] = useState<unknown>(null)
  const [requestId, setRequestId] = useState('')
  const [lastAsync, setLastAsync] = useState<unknown>(null)

  const runEnqueueAndWait = () =>
    withBusy(async () => {
      const j = await telescopePostWithQuery(
        '/telescopes/model/inference/enqueue-and-wait',
        { prompt },
        { timeout_seconds: timeoutSec, poll_interval_seconds: pollSec },
      )
      setLastSyncResult(j)
    })

  const runEnqueueOnly = () =>
    withBusy(async () => {
      const j = (await telescopePost('/telescopes/model/inference', { prompt })) as { request_id?: string }
      setRequestId(typeof j.request_id === 'string' ? j.request_id : '')
      setLastAsync(j)
    })

  const pollStatus = () =>
    withBusy(async () => {
      const id = requestId.trim()
      if (!id) {
        return
      }
      const j = await telescopeGet(`/telescopes/model/inference/${encodeURIComponent(id)}/status`)
      setLastAsync(j)
    })

  const waitResult = () =>
    withBusy(async () => {
      const id = requestId.trim()
      if (!id) {
        return
      }
      const q = new URLSearchParams({
        timeout_seconds: String(timeoutSec),
        poll_interval_seconds: String(pollSec),
      })
      const j = await telescopeGet(
        `/telescopes/model/inference/${encodeURIComponent(id)}/wait?${q.toString()}`,
      )
      setLastAsync(j)
    })

  return (
    <div className="panel">
      <h2>Model inference (Kafka pipeline)</h2>
      <p className="hint">
        Requires backend + Kafka + model-service (e.g. <code>make app-dev-with-model</code>). Uses the same HTTP
        surface as MCP tools.
      </p>
      <div className="row">
        <label className="stretch">
          <span>Prompt</span>
          <textarea
            className="prompt-area"
            rows={3}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            spellCheck={false}
          />
        </label>
      </div>
      <div className="row">
        <label>
          <span>timeout_seconds</span>
          <input
            type="number"
            step="any"
            min={0.1}
            max={60}
            value={timeoutSec}
            onChange={(e) => setTimeoutSec(Number(e.target.value))}
          />
        </label>
        <label>
          <span>poll_interval_seconds</span>
          <input
            type="number"
            step="any"
            min={0.05}
            max={2}
            value={pollSec}
            onChange={(e) => setPollSec(Number(e.target.value))}
          />
        </label>
      </div>
      <div className="row">
        <button type="button" disabled={busy} onClick={runEnqueueAndWait}>
          POST enqueue-and-wait
        </button>
      </div>
      {lastSyncResult != null ? (
        <>
          <h3 className="subhead">Last enqueue-and-wait response</h3>
          <pre className="json">{formatJson(lastSyncResult)}</pre>
        </>
      ) : null}

      <h3 className="subhead">Async path (enqueue → status / wait)</h3>
      <div className="row">
        <button type="button" className="secondary" disabled={busy} onClick={runEnqueueOnly}>
          POST enqueue only
        </button>
      </div>
      <div className="row">
        <label>
          <span>request_id</span>
          <input
            type="text"
            value={requestId}
            onChange={(e) => setRequestId(e.target.value)}
            spellCheck={false}
            placeholder="filled after enqueue-only"
          />
        </label>
        <button type="button" className="secondary" disabled={busy || !requestId.trim()} onClick={pollStatus}>
          GET status
        </button>
        <button type="button" className="secondary" disabled={busy || !requestId.trim()} onClick={waitResult}>
          GET wait
        </button>
      </div>
      {lastAsync != null ? (
        <>
          <h3 className="subhead">Async response</h3>
          <pre className="json model-inf-json">{formatJson(lastAsync)}</pre>
        </>
      ) : null}
    </div>
  )
}
