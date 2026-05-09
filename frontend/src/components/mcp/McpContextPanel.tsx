import { useState } from 'react'
import { telescopeGet } from '../../api'
import { formatJson } from '../../formatJson'
import type { WithBusyFn } from './types'

type Props = { withBusy: WithBusyFn; busy: boolean }

export function McpContextPanel({ withBusy, busy }: Props) {
  const [designation, setDesignation] = useState('')
  const [ephemerisBody, setEphemerisBody] = useState('')
  const [obstimeUtcIso, setObstimeUtcIso] = useState(() => new Date().toISOString().slice(0, 19) + 'Z')
  const [context, setContext] = useState<unknown>(null)

  const loadContext = () =>
    withBusy(async () => {
      const params = new URLSearchParams()
      const des = designation.trim()
      const body = ephemerisBody.trim()
      if (des) {
        params.set('designation', des)
      }
      if (body) {
        params.set('ephemeris_body', body)
        params.set('obstime_utc_iso', obstimeUtcIso.trim())
      }
      const q = params.toString()
      const path = `/telescopes/context/mcp${q ? `?${q}` : ''}`
      const j = await telescopeGet(path)
      setContext(j)
    })

  return (
    <div className="panel">
      <h2>MCP context snapshot</h2>
      <p className="hint">
        Mirrors <code>GET /telescopes/context/mcp</code> — resolves optional SIMBAD name and/or ephemeris body when
        backend features are enabled.
      </p>
      <div className="row">
        <label>
          <span>Catalog designation (optional)</span>
          <input
            type="text"
            value={designation}
            onChange={(e) => setDesignation(e.target.value)}
            placeholder="e.g. m31"
            spellCheck={false}
          />
        </label>
      </div>
      <div className="row">
        <label>
          <span>Ephemeris body (optional)</span>
          <input
            type="text"
            value={ephemerisBody}
            onChange={(e) => setEphemerisBody(e.target.value)}
            placeholder="e.g. mars"
            spellCheck={false}
          />
        </label>
        <label>
          <span>obstime UTC ISO (required with ephemeris)</span>
          <input
            type="text"
            value={obstimeUtcIso}
            onChange={(e) => setObstimeUtcIso(e.target.value)}
            spellCheck={false}
          />
        </label>
      </div>
      <div className="row">
        <button type="button" disabled={busy} onClick={loadContext}>
          GET /telescopes/context/mcp
        </button>
      </div>
      {context != null ? (
        <>
          <h3 className="subhead">Response</h3>
          <pre className="json mcp-context-json">{formatJson(context)}</pre>
        </>
      ) : null}
    </div>
  )
}
