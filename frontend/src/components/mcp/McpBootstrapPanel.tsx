import { useState } from 'react'
import { telescopeGet } from '../../api'
import { formatJson } from '../../formatJson'
import type { WithBusyFn } from './types'

function summarizeEffectiveManifest(data: unknown): { total: number; enabled: number } | null {
  if (!data || typeof data !== 'object') {
    return null
  }
  const manifest = (data as Record<string, unknown>).effective_manifest as Record<string, unknown> | undefined
  const tools = manifest?.tools
  if (!Array.isArray(tools)) {
    return null
  }
  let enabled = 0
  for (const t of tools) {
    if (t && typeof t === 'object' && (t as { enabled?: boolean }).enabled === true) {
      enabled += 1
    }
  }
  return { total: tools.length, enabled }
}

type Props = { withBusy: WithBusyFn; busy: boolean }

export function McpBootstrapPanel({ withBusy, busy }: Props) {
  const [bootstrap, setBootstrap] = useState<unknown>(null)
  const [planningGuide, setPlanningGuide] = useState<unknown>(null)
  const [showBootstrapRaw, setShowBootstrapRaw] = useState(false)

  const loadBootstrap = () =>
    withBusy(async () => {
      const j = await telescopeGet('/telescopes/tools/mcp-bootstrap')
      setBootstrap(j)
    })

  const loadPlanningGuide = () =>
    withBusy(async () => {
      const j = await telescopeGet('/telescopes/tools/mcp-planning-guide')
      setPlanningGuide(j)
    })

  const stats = summarizeEffectiveManifest(bootstrap)

  return (
    <div className="panel">
      <header className="panel-header">
        <h2 className="panel-title">MCP bootstrap &amp; planning</h2>
        <p className="panel-lead">
          See the same tool list and planning notes that AI agents use. No sky knowledge required — this is just the
          contract the backend exposes.
        </p>
      </header>
      <p className="hint">
        Optional command token is sent automatically when you fill it in the Connection card and the route is guarded.
      </p>
      <div className="row">
        <button type="button" disabled={busy} onClick={loadBootstrap}>
          GET /telescopes/tools/mcp-bootstrap
        </button>
        <button type="button" className="secondary" disabled={busy} onClick={loadPlanningGuide}>
          GET /telescopes/tools/mcp-planning-guide
        </button>
        {bootstrap != null ? (
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <input
              type="checkbox"
              checked={showBootstrapRaw}
              onChange={(e) => setShowBootstrapRaw(e.target.checked)}
            />
            <span>Show raw bootstrap JSON</span>
          </label>
        ) : null}
      </div>
      {stats ? (
        <div className="mcp-stat-grid">
          <div className="mcp-stat">
            <span className="mcp-stat-label">effective tools</span>
            <span className="mcp-stat-value">
              {stats.enabled}/{stats.total} enabled
            </span>
          </div>
        </div>
      ) : null}
      {bootstrap != null && showBootstrapRaw ? (
        <>
          <h3 className="subhead">mcp-bootstrap</h3>
          <pre className="json">{formatJson(bootstrap)}</pre>
        </>
      ) : null}
      {planningGuide != null ? (
        <>
          <h3 className="subhead">mcp-planning-guide</h3>
          <pre className="json">{formatJson(planningGuide)}</pre>
        </>
      ) : null}
    </div>
  )
}
