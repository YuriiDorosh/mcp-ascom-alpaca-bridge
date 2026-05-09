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
        <h1>Alpaca Astro Center · operator dashboard</h1>
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

      <main className="dashboard-grid" aria-label="Operator tools and telescope controls">
      <div className="panel">
        <header className="panel-header">
          <h2 className="panel-title">Connection</h2>
          <p className="panel-lead">
            Tell the dashboard where your API lives. Checking health does not touch the telescope — it is OK to poke
            around if you are new to this.
          </p>
        </header>
        <div className="row">
          <label>
            <span>API base URL (same idea as VITE_API_BASE)</span>
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
        <header className="panel-header">
          <h2 className="panel-title">Hardware preflight</h2>
          <p className="panel-lead">
            Quick “is everything wired?” checks — read-only endpoints, never nudges the mount. Agents (and cautious
            humans) use this before live runs.
          </p>
        </header>
        <p className="hint">
          Uses <code>GET /telescopes/hardware/*</code>. For full Seestar smoke/validation workflows see{' '}
          <code>docs/TASKS.md</code>.
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
        <header className="panel-header">
          <h2 className="panel-title">Live status stream</h2>
          <p className="panel-lead">
            Optional streaming channel for the same telescope status JSON you see over REST — handy for dashboards.
          </p>
        </header>
        <p className="hint">
          Connect to <code>{getOperatorWebSocketUrl()}</code>. Close before you change API base above.
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

      <div className="panel panel--full">
        <header className="panel-header">
          <h2 className="panel-title">What the telescope sees</h2>
          <p className="panel-lead">
            Camera previews and overlays so you never command blind. Backend still images, MJPEG relays, or both can
            show up side by side.
          </p>
        </header>
        <p className="hint">
          Still / URL mode: backend may return <code>image_url</code> via <code>GET /telescopes/operator/live-view</code>{' '}
          when configured.
        </p>
        <div className="row">
          <button type="button" className="secondary" disabled={busy} onClick={loadLiveViewMeta}>
            Refresh live-view metadata
          </button>
        </div>
        <h3 className="subhead">RTSP relay (MJPEG)</h3>
        <p className="hint">
          When <code>TELESCOPE_RTSP_URL</code> is set on the API, this frame loads{' '}
          <code>GET /api/v1/telescope/stream</code> as a multipart JPEG stream (503 if unset).
        </p>
        <p className="hint hint--callout">
          <strong>Seestar (incl. Seestar S30 Pro):</strong> the RTSP preview only works while the device is actually
          streaming from its built-in camera. ZWO does not publish an API to power the camera on from this bridge — in
          practice you start the feed from the mobile app first (e.g. enter <strong>Scenery</strong> / imaging mode; the
          exact menu label depends on firmware). After the camera is live, the MJPEG relay here should show video.
        </p>
        <div className="live-view-frame">
          <img
            className="live-view-img"
            alt="Telescope RTSP relay (configure TELESCOPE_RTSP_URL if this stays blank)"
            src={`${getApiBase().replace(/\/+$/, '')}/api/v1/telescope/stream`}
            key={apiBaseInput}
          />
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
        <header className="panel-header">
          <h2 className="panel-title">Telescope snapshot</h2>
          <p className="panel-lead">
            Inspect current state — these buttons only read data. Useful when you’re learning how the mount responds to
            the sky.
          </p>
        </header>
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
            <h3 className="section-title">Status payload</h3>
            <pre className="json">{statusJson}</pre>
          </>
        )}
        {capabilitiesJson && (
          <>
            <h3 className="section-title">Capabilities payload</h3>
            <pre className="json">{capabilitiesJson}</pre>
          </>
        )}
      </div>

      <div className="panel">
        <header className="panel-header">
          <h2 className="panel-title">Mount commands — careful</h2>
          <p className="panel-lead">
            These actions request real slew / sync / tracking when Alpaca control is enabled. Skip this card entirely if
            you only want read-only tooling.
          </p>
        </header>
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
            <h3 className="section-title">Last command response</h3>
            <pre className="json">{lastCmd}</pre>
          </>
        )}
      </div>

      </main>

      {error && <p className="err app-error">{error}</p>}
    </div>
  )
}
