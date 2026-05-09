import { useCallback, useEffect, useRef, useState } from 'react'
import {
  apiGet,
  getApiBase,
  getOperatorWebSocketUrl,
  setRuntimeApiBase,
  telescopeGet,
  telescopePost,
} from './api'
import { ReadinessSummary } from './components/ReadinessSummary'
import { CoordinatesPanel } from './components/mcp/CoordinatesPanel'
import { McpBootstrapPanel } from './components/mcp/McpBootstrapPanel'
import { McpContextPanel } from './components/mcp/McpContextPanel'
import { McpExecutionPlanPanel } from './components/operator/McpExecutionPlanPanel'
import { ModelInferencePanel } from './components/operator/ModelInferencePanel'
import { formatJson } from './formatJson'

type ApiHealth = { state: 'idle' | 'ok' | 'fail'; detail?: string }

type WsUiState = 'off' | 'connecting' | 'open' | 'error'

export default function App() {
  const [apiBaseInput, setApiBaseInput] = useState(() => getApiBase())
  const [commandToken, setCommandToken] = useState('')

  const [readinessData, setReadinessData] = useState<unknown>(null)
  const [overviewData, setOverviewData] = useState<unknown>(null)

  const [statusJson, setStatusJson] = useState<string | null>(null)
  const [capabilitiesJson, setCapabilitiesJson] = useState<string | null>(null)
  const [lastCmd, setLastCmd] = useState<string | null>(null)

  const [raHours, setRaHours] = useState(1)
  const [decDeg, setDecDeg] = useState(5)
  const [trackingEnabled, setTrackingEnabled] = useState(false)

  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [apiHealth, setApiHealth] = useState<ApiHealth>({ state: 'idle' })

  const wsRef = useRef<WebSocket | null>(null)
  const [wsUi, setWsUi] = useState<{ state: WsUiState; detail?: string }>({ state: 'off' })
  const [wsLog, setWsLog] = useState<string>('')

  const [liveViewMeta, setLiveViewMeta] = useState<Record<string, unknown> | null>(null)

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

  const disconnectOperatorWs = useCallback(() => {
    wsRef.current?.close()
    wsRef.current = null
    setWsUi({ state: 'off' })
    setWsLog('')
  }, [])

  const connectOperatorWs = useCallback(() => {
    disconnectOperatorWs()
    setWsUi({ state: 'connecting' })
    try {
      const ws = new WebSocket(getOperatorWebSocketUrl())
      wsRef.current = ws
      ws.onopen = () => setWsUi({ state: 'open' })
      ws.onerror = () => setWsUi({ state: 'error', detail: 'WebSocket error (check API base / mixed content)' })
      ws.onmessage = (ev) => {
        try {
          const j = JSON.parse(ev.data as string) as unknown
          setWsLog(formatJson(j))
        } catch {
          setWsLog(String(ev.data))
        }
      }
      ws.onclose = () => {
        wsRef.current = null
        setWsUi({ state: 'off' })
      }
    } catch (e) {
      setWsUi({ state: 'error', detail: e instanceof Error ? e.message : String(e) })
    }
  }, [disconnectOperatorWs])

  useEffect(() => {
    return () => {
      wsRef.current?.close()
      wsRef.current = null
    }
  }, [])

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

  const loadHardwareReadiness = () =>
    withBusy(async () => {
      const j = await telescopeGet('/telescopes/hardware/readiness')
      setReadinessData(j)
    })

  const loadHardwareOverview = () =>
    withBusy(async () => {
      const j = await telescopeGet('/telescopes/hardware/overview')
      setOverviewData(j)
    })

  const loadLiveViewMeta = () =>
    withBusy(async () => {
      const j = await telescopeGet('/telescopes/operator/live-view')
      setLiveViewMeta(j as Record<string, unknown>)
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
            href={`${getApiBase()}/api/docs`}
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
          Backend must allow this origin in <code>CORS_ALLOWED_ORIGINS</code> (defaults include browser{' '}
          <code>http://localhost:FRONTEND_PORT</code>, e.g. Vite or nginx on{' '}
          <code>:5173</code>). Current API base: <code>{getApiBase()}</code>
        </p>
      </div>

      <McpBootstrapPanel withBusy={withBusy} busy={busy} />
      <McpContextPanel withBusy={withBusy} busy={busy} />
      <CoordinatesPanel withBusy={withBusy} busy={busy} />

      <McpExecutionPlanPanel withBusy={withBusy} busy={busy} />
      <ModelInferencePanel withBusy={withBusy} busy={busy} />

      <div className="panel">
        <h2>Hardware preflight (read-only API)</h2>
        <p className="hint">
          Uses <code>GET /telescopes/hardware/*</code> — no mount motion. For live Seestar checks (smoke / validation)
          follow <code>docs/TASKS.md</code> and CLI targets when readiness says so.
        </p>
        <div className="row">
          <button type="button" className="secondary" disabled={busy} onClick={loadHardwareReadiness}>
            GET /telescopes/hardware/readiness
          </button>
          <button type="button" className="secondary" disabled={busy} onClick={loadHardwareOverview}>
            GET /telescopes/hardware/overview
          </button>
        </div>
        {readinessData != null && (
          <>
            <ReadinessSummary data={readinessData} />
            <h3 className="subhead">Readiness JSON</h3>
            <pre className="json">{formatJson(readinessData)}</pre>
          </>
        )}
        {overviewData != null && (
          <>
            <h3 className="subhead">Overview JSON</h3>
            <pre className="json">{formatJson(overviewData)}</pre>
          </>
        )}
      </div>

      <div className="panel">
        <h2>Operator WebSocket (backend → browser)</h2>
        <p className="hint">
          Connects to <code>{getOperatorWebSocketUrl()}</code> — periodic <code>telescope_status</code> JSON (same
          contract as REST). Close before changing API base.
        </p>
        <div className="row">
          <button type="button" disabled={busy || wsUi.state === 'connecting'} onClick={connectOperatorWs}>
            Connect
          </button>
          <button type="button" className="secondary" disabled={busy} onClick={disconnectOperatorWs}>
            Disconnect
          </button>
          <span className="ws-status">
            {wsUi.state === 'off' && 'disconnected'}
            {wsUi.state === 'connecting' && 'connecting…'}
            {wsUi.state === 'open' && 'connected'}
            {wsUi.state === 'error' && (wsUi.detail ? `error: ${wsUi.detail}` : 'error')}
          </span>
        </div>
        {wsLog ? (
          <>
            <h3 className="subhead">Last WebSocket message</h3>
            <pre className="json ws-log">{wsLog}</pre>
          </>
        ) : null}
      </div>

      <div className="panel">
        <h2>Live view (FOV)</h2>
        <p className="hint">
          Loads <code>GET /telescopes/operator/live-view</code>. When the backend exposes an <code>image_url</code>{' '}
          (still or stream URL), it renders here so you are not slewing blind. Seestar-specific video may need a
          follow-up integration task.
        </p>
        <div className="row">
          <button type="button" className="secondary" disabled={busy} onClick={loadLiveViewMeta}>
            Refresh live-view metadata
          </button>
        </div>
        {liveViewMeta ? (
          <>
            <p className="live-view-meta">
              {liveViewMeta.available === true ? (
                <span className="live-flag live-flag--ok">preview URL available</span>
              ) : (
                <span className="live-flag live-flag--muted">no preview URL yet (API placeholder)</span>
              )}{' '}
              <code>provider={(liveViewMeta.provider as string) ?? '?'}</code>
            </p>
            {typeof liveViewMeta.notes === 'string' ? <p className="hint">{liveViewMeta.notes}</p> : null}
            {typeof liveViewMeta.image_url === 'string' && liveViewMeta.image_url.length > 0 ? (
              <div className="live-view-frame">
                <img className="live-view-img" alt="Telescope live view" src={liveViewMeta.image_url} />
              </div>
            ) : null}
            <h3 className="subhead">Contract JSON</h3>
            <pre className="json">{formatJson(liveViewMeta)}</pre>
          </>
        ) : null}
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
