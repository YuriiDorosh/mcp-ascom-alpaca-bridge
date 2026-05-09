import { useCallback, useEffect, useState } from 'react'
import { apiGet, getApiBase, setRuntimeApiBase, telescopeGet, telescopePost } from './api'

type ApiHealth = { state: 'idle' | 'ok' | 'fail'; detail?: string }

function formatJson(data: unknown): string {
  return JSON.stringify(data, null, 2)
}

export default function App() {
  const [apiBaseInput, setApiBaseInput] = useState(() => getApiBase())
  const [commandToken, setCommandToken] = useState('')

  const [statusJson, setStatusJson] = useState<string | null>(null)
  const [capabilitiesJson, setCapabilitiesJson] = useState<string | null>(null)
  const [lastCmd, setLastCmd] = useState<string | null>(null)

  const [raHours, setRaHours] = useState(1)
  const [decDeg, setDecDeg] = useState(5)
  const [trackingEnabled, setTrackingEnabled] = useState(false)

  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [apiHealth, setApiHealth] = useState<ApiHealth>({ state: 'idle' })

  const checkApiHealth = useCallback(async () => {
    setApiHealth({ state: 'idle' })
    try {
      const j = (await apiGet('/health')) as { status?: string }
      if (j?.status === 'ok') {
        setApiHealth({ state: 'ok' })
      } else {
        setApiHealth({ state: 'fail', detail: 'Unexpected /health response' })
      }
    } catch (e) {
      setApiHealth({
        state: 'fail',
        detail: e instanceof Error ? e.message : String(e),
      })
    }
  }, [])

  useEffect(() => {
    void checkApiHealth()
  }, [checkApiHealth])

  const applyApiBase = useCallback(() => {
    setRuntimeApiBase(apiBaseInput)
    setError(null)
    void checkApiHealth()
  }, [apiBaseInput, checkApiHealth])

  const withBusy = async <T,>(fn: () => Promise<T>): Promise<T | undefined> => {
    setError(null)
    setBusy(true)
    try {
      return await fn()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
      return undefined
    } finally {
      setBusy(false)
    }
  }

  const loadStatus = () =>
    withBusy(async () => {
      const j = await telescopeGet('/telescopes/status')
      setStatusJson(formatJson(j))
    })

  const loadCapabilities = () =>
    withBusy(async () => {
      const j = await telescopeGet('/telescopes/capabilities')
      setCapabilitiesJson(formatJson(j))
    })

  const sendSlew = () =>
    withBusy(async () => {
      const j = await telescopePost(
        '/telescopes/commands/slew-icrs',
        { ra_hours: raHours, dec_degrees: decDeg },
        commandToken || undefined,
      )
      setLastCmd(formatJson(j))
    })

  const sendSync = () =>
    withBusy(async () => {
      const j = await telescopePost(
        '/telescopes/commands/sync-icrs',
        { ra_hours: raHours, dec_degrees: decDeg },
        commandToken || undefined,
      )
      setLastCmd(formatJson(j))
    })

  const sendTracking = () =>
    withBusy(async () => {
      const j = await telescopePost(
        '/telescopes/commands/tracking',
        { enabled: trackingEnabled },
        commandToken || undefined,
      )
      setLastCmd(formatJson(j))
    })

  return (
    <div className="app">
      <div className="app-header">
        <h1>Alpaca Astro Center — operator (local)</h1>
        <div className="header-actions">
          <span
            className={`api-pill api-pill--${apiHealth.state === 'ok' ? 'ok' : apiHealth.state === 'fail' ? 'fail' : 'idle'}`}
            title={apiHealth.detail}
          >
            {apiHealth.state === 'ok' && 'API /health OK'}
            {apiHealth.state === 'fail' && (apiHealth.detail ? `API fault: ${apiHealth.detail}` : 'API unreachable')}
            {apiHealth.state === 'idle' && 'Checking API…'}
          </span>
          <a
            className="docs-link"
            href={`${getApiBase()}/docs`}
            target="_blank"
            rel="noreferrer"
          >
            OpenAPI docs
          </a>
        </div>
      </div>

      <div className="panel">
        <h2>Connection</h2>
        <div className="row">
          <label>
            <span>API base (matches VITE_API_BASE)</span>
            <input
              type="text"
              value={apiBaseInput}
              onChange={(e) => setApiBaseInput(e.target.value)}
              spellCheck={false}
            />
          </label>
          <button type="button" className="secondary" onClick={applyApiBase}>
            Use
          </button>
          <button type="button" className="secondary" disabled={busy} onClick={() => void checkApiHealth()}>
            Ping /health
          </button>
        </div>
        <div className="row">
          <label>
            <span>Command token (optional, if COMMAND_AUTH_TOKEN set on backend)</span>
            <input
              type="password"
              value={commandToken}
              onChange={(e) => setCommandToken(e.target.value)}
              autoComplete="off"
            />
          </label>
        </div>
        <p className="hint">
          Backend must allow this origin in <code>CORS_ALLOWED_ORIGINS</code> (defaults include Vite{' '}
          <code>:5173</code>). Current base: <code>{getApiBase()}</code>
        </p>
      </div>

      <div className="panel">
        <h2>Read-only</h2>
        <div className="row">
          <button type="button" disabled={busy} onClick={loadStatus}>
            GET /telescopes/status
          </button>
          <button type="button" className="secondary" disabled={busy} onClick={loadCapabilities}>
            GET /telescopes/capabilities
          </button>
        </div>
        {statusJson && (
          <>
            <h2 style={{ marginTop: '1rem' }}>Status</h2>
            <pre className="json">{statusJson}</pre>
          </>
        )}
        {capabilitiesJson && (
          <>
            <h2 style={{ marginTop: '1rem' }}>Capabilities</h2>
            <pre className="json">{capabilitiesJson}</pre>
          </>
        )}
      </div>

      <div className="panel">
        <h2>Commands (moves hardware when Alpaca is enabled)</h2>
        <div className="row">
          <label>
            <span>RA (hours)</span>
            <input
              type="number"
              step="any"
              value={raHours}
              onChange={(e) => setRaHours(Number(e.target.value))}
            />
          </label>
          <label>
            <span>Dec (degrees)</span>
            <input
              type="number"
              step="any"
              value={decDeg}
              onChange={(e) => setDecDeg(Number(e.target.value))}
            />
          </label>
        </div>
        <div className="row">
          <button type="button" disabled={busy} onClick={sendSlew}>
            POST slew-icrs
          </button>
          <button type="button" className="secondary" disabled={busy} onClick={sendSync}>
            POST sync-icrs
          </button>
        </div>
        <div className="row">
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <input
              type="checkbox"
              checked={trackingEnabled}
              onChange={(e) => setTrackingEnabled(e.target.checked)}
            />
            <span>Tracking on</span>
          </label>
          <button type="button" disabled={busy} onClick={sendTracking}>
            POST tracking
          </button>
        </div>
        <p className="hint">
          Ensure a safe sky area and mount state before issuing commands. Sync with Seestar physical constraints and your site limits.
        </p>
        {lastCmd && (
          <>
            <h2 style={{ marginTop: '0.75rem' }}>Last command response</h2>
            <pre className="json">{lastCmd}</pre>
          </>
        )}
      </div>

      {error && <p className="err">{error}</p>}
    </div>
  )
}
