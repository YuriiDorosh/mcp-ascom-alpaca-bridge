import { useState } from 'react'
import { telescopeGet } from '../../api'
import { formatJson } from '../../formatJson'
import type { WithBusyFn } from '../mcp/types'

type Props = { withBusy: WithBusyFn; busy: boolean }

type ExecStep = {
  step?: number
  tool_name?: string
  purpose?: string
  enabled?: boolean
  skip_reason?: string | null
}

export function McpExecutionPlanPanel({ withBusy, busy }: Props) {
  const [mode, setMode] = useState<'async' | 'sync'>('async')
  const [includeDisabled, setIncludeDisabled] = useState(true)
  const [plan, setPlan] = useState<unknown>(null)
  const [showRaw, setShowRaw] = useState(false)

  const loadPlan = () =>
    withBusy(async () => {
      const params = new URLSearchParams()
      params.set('mode', mode)
      params.set('include_disabled_commands', String(includeDisabled))
      const path = `/telescopes/tools/mcp-execution-plan?${params.toString()}`
      const j = await telescopeGet(path)
      setPlan(j)
    })

  const o = plan && typeof plan === 'object' ? (plan as Record<string, unknown>) : null
  const steps = o && Array.isArray(o.steps) ? (o.steps as ExecStep[]) : []

  return (
    <div className="panel">
      <header className="panel-header">
        <h2 className="panel-title">Suggested command order</h2>
        <p className="panel-lead">
          A human-readable playbook of telescope steps tailored to capabilities (what is allowed vs skipped). Matches
          the structured plan agents follow.
        </p>
      </header>
      <p className="hint">
        Data comes from <code>GET /telescopes/tools/mcp-execution-plan</code>; toggling mode only changes how aggressively
        the backend sequences async tooling.
      </p>
      <div className="row">
        <label>
          <span>mode</span>
          <select value={mode} onChange={(e) => setMode(e.target.value as 'async' | 'sync')}>
            <option value="async">async</option>
            <option value="sync">sync</option>
          </select>
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <input
            type="checkbox"
            checked={includeDisabled}
            onChange={(e) => setIncludeDisabled(e.target.checked)}
          />
          <span>include_disabled_commands</span>
        </label>
        <button type="button" disabled={busy} onClick={loadPlan}>
          Load plan
        </button>
        {plan != null ? (
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <input type="checkbox" checked={showRaw} onChange={(e) => setShowRaw(e.target.checked)} />
            <span>Raw JSON</span>
          </label>
        ) : null}
      </div>
      {o ? (
        <>
          <p className="exec-plan-summary">
            <strong>{String(o.objective ?? '—')}</strong>
            {typeof o.mode === 'string' ? (
              <>
                {' '}
                · mode <code>{o.mode}</code>
              </>
            ) : null}
            {o.stats && typeof o.stats === 'object' ? (
              <>
                {' '}
                · steps{' '}
                <code>
                  {String((o.stats as Record<string, unknown>).returned_steps ?? '?')} /{' '}
                  {String((o.stats as Record<string, unknown>).baseline_steps ?? '?')}
                </code>
              </>
            ) : null}
          </p>
          {steps.length > 0 ? (
            <div className="exec-plan-table-wrap">
              <table className="exec-plan-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>tool</th>
                    <th>enabled</th>
                    <th>purpose</th>
                    <th>skip</th>
                  </tr>
                </thead>
                <tbody>
                  {steps.map((s, i) => (
                    <tr key={`${s.tool_name ?? 't'}-${i}`} className={s.enabled === false ? 'exec-row-off' : ''}>
                      <td>{s.step ?? i + 1}</td>
                      <td>
                        <code>{s.tool_name ?? '—'}</code>
                      </td>
                      <td>{s.enabled === true ? 'yes' : s.enabled === false ? 'no' : '—'}</td>
                      <td>{s.purpose ?? '—'}</td>
                      <td className="exec-skip">{s.skip_reason ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
          {showRaw ? (
            <>
              <h3 className="subhead">Full payload</h3>
              <pre className="json exec-plan-raw">{formatJson(plan)}</pre>
            </>
          ) : null}
        </>
      ) : null}
    </div>
  )
}
