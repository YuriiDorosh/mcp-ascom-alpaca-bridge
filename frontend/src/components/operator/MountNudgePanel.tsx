import { useCallback, useMemo, useState } from 'react'
import { telescopeGet, telescopePost } from '../../api'

/** One jog step: ΔRA sidereal seconds (east +), ΔDec arcseconds (north +). */
type StepRow = {
  readonly id: string
  readonly group: string
  readonly raSec: number
  readonly decArcsec: number
}

/**
 * ΔRA_degrees ≈ (Δ_sidereal_seconds / 3600) × 15 at the celestial equator (δ≈0).
 * ΔDec_degrees = decArcsec / 3600 exactly (handler clamps poles).
 * Backend limits: ±43_200 sidereal-second RA (=±12 sidereal hour ≈±180°Eq), ±648000″ Dec (=±180° before clamp).
 */
const STEP_ROWS: readonly StepRow[] = [
  { id: 'm03', group: 'Ultrafine (slow trim)', raSec: 0.03, decArcsec: 0.12 },
  { id: 'm06', group: 'Ultrafine', raSec: 0.06, decArcsec: 0.25 },
  { id: 'm10', group: 'Ultrafine', raSec: 0.1, decArcsec: 0.5 },
  { id: 'm25', group: 'Ultrafine', raSec: 0.25, decArcsec: 1 },
  { id: 'm05_2', group: 'Ultrafine', raSec: 0.5, decArcsec: 2 },
  { id: 'm1_4', group: 'Very small', raSec: 1, decArcsec: 4 },
  { id: 'm2_8', group: 'Very small', raSec: 2, decArcsec: 8 },
  { id: 'm5_20', group: 'Small', raSec: 5, decArcsec: 20 },
  { id: 'm12_48', group: 'Small', raSec: 12, decArcsec: 48 },
  { id: 'm24_96', group: 'Modest', raSec: 24, decArcsec: 96 },
  { id: 'm42_168', group: 'Modest', raSec: 42, decArcsec: 168 },
  { id: 'm72_288', group: 'Medium−', raSec: 72, decArcsec: 288 },
  { id: 'm120_480', group: 'Medium', raSec: 120, decArcsec: 480 },
  { id: 'm210_840', group: 'Medium', raSec: 210, decArcsec: 840 },
  { id: 'm330_1320', group: 'Medium+', raSec: 330, decArcsec: 1320 },
  { id: 'm480_1920', group: 'Large−', raSec: 480, decArcsec: 1920 },
  { id: 'm780_3120', group: 'Large', raSec: 780, decArcsec: 3120 },
  { id: 'm1200_4800', group: 'Large', raSec: 1200, decArcsec: 4800 },
  { id: 'm1650_6600', group: 'Large+', raSec: 1650, decArcsec: 6600 },
  { id: 'combo_3600_10800', group: 'Large diagonal (combined)', raSec: 3600, decArcsec: 10_800 },
  // Legacy cap highlight: ΔRA sidereal sec = ±3600 is only ~15°Eq — many users intuit “big” as tens of degrees.
  { id: 'ra_hour_1', group: 'RA-only (historic one-hour slew ≈15° Eq)', raSec: 3600, decArcsec: 0 },
  ...(
    [
      [7200, 'RA-only (~30° Eq)'],
      [10_800, 'RA-only (~45° Eq)'],
      [14_400, 'RA-only (~60° Eq)'],
      [18_000, 'RA-only (~75° Eq)'],
      [21_600, 'RA-only (~90° Eq)'],
      [25_200, 'RA-only (~105° Eq)'],
      [28_800, 'RA-only (~120° Eq)'],
      [32_400, 'RA-only (~135° Eq)'],
      [36_000, 'RA-only (~150° Eq)'],
      [39_600, 'RA-only (~165° Eq)'],
      [43_200, 'RA-only (~180° Eq, backend max)'],
    ] as const
  ).map(([raSec, group]) => ({ id: `ra_only_${raSec}`, group: String(group), raSec: Number(raSec), decArcsec: 0 })),
  ...(
    [
      [54_000, 'Dec-only (~15° declination)'],
      [108_000, 'Dec-only (~30°)'],
      [162_000, 'Dec-only (~45°)'],
      [216_000, 'Dec-only (~60°)'],
      [270_000, 'Dec-only (~75°)'],
      [324_000, 'Dec-only (~90° toward pole clamp)'],
      [432_000, 'Dec-only (~120°, clamp-heavy)'],
      [540_000, 'Dec-only (~150°, clamp-heavy)'],
      [648_000, 'Dec-only (~±180°, heavy clamp ±90°)'],
    ] as const
  ).map(([decArcsec, group]) => ({
    id: `dec_only_${decArcsec}`,
    group: String(group),
    raSec: 0,
    decArcsec: Number(decArcsec),
  })),
] as const

const DEFAULT_STEP_ID = 'm2_8'

function rowById(id: string): StepRow | undefined {
  return STEP_ROWS.find((p) => p.id === id)
}

function fmtRaSec(s: number): string {
  if (Math.abs(s) >= 60) return `${Math.round(s)}s`
  if (Math.abs(s) >= 1) return `${Number(s.toFixed(2))}s`
  return `${Number(s.toFixed(3))}s`
}

function fmtDecArcsec(a: number): string {
  if (Math.abs(a) >= 60) return `${Math.round(a / 60)}′`
  if (Math.abs(a) >= 10) return `${Number(a.toFixed(1))}″`
  return `${Number(a.toFixed(2))}″`
}

/** Apparent Δ along RA axis at celestial equator: Δdegrees ≈ ΔRA_hours × 15. */
function deltaRaDegreesApproxEquator(siderealSec: number): number {
  return (siderealSec / 3600) * 15
}

function deltaDecDegrees(arcseconds: number): number {
  return arcseconds / 3600
}

function formatDegreesHint(p: StepRow): string {
  const raDeg = Math.abs(deltaRaDegreesApproxEquator(p.raSec))
  const decDeg = Math.abs(deltaDecDegrees(p.decArcsec))
  const chunks: string[] = []
  if (raDeg > 1e-9) chunks.push(`~${raDeg >= 100 ? Math.round(raDeg) : Number(raDeg.toPrecision(3))}°Eq RA`)
  if (decDeg > 1e-9)
    chunks.push(`~${decDeg >= 100 ? Math.round(decDeg) : Number(decDeg.toPrecision(3))}° Decl.`)
  if (!chunks.length) return ''
  return ` — ${chunks.join(' · ')}`
}

type Props = {
  withBusy: <T>(fn: () => Promise<T>) => Promise<T | undefined>
  busy: boolean
  commandToken: string
  onApplyIcrs?: (ra: number, dec: number) => void
}

/** Equatorial bumps: mount slew, not camera PTZ; compare logs with GET mount + Alpaca timeouts. */
export function MountNudgePanel(props: Props) {
  const { withBusy, busy, commandToken, onApplyIcrs } = props
  const [presetId, setPresetId] = useState<string>(DEFAULT_STEP_ID)
  const [lastRead, setLastRead] = useState<string | null>(null)
  const [lastNudge, setLastNudge] = useState<string | null>(null)
  const [staleHint, setStaleHint] = useState<string | null>(null)

  const step = rowById(presetId) ?? rowById(DEFAULT_STEP_ID)!

  const optionsGrouped = useMemo(() => {
    const map = new Map<string, StepRow[]>()
    for (const row of STEP_ROWS) {
      const list = map.get(row.group) ?? []
      list.push(row)
      map.set(row.group, list)
    }
    return Array.from(map.entries())
  }, [])

  const refreshPosition = useCallback(() => {
    return withBusy(async () => {
      setStaleHint(null)
      const j = (await telescopeGet('/telescopes/mount/icrs-equatorial', commandToken || undefined)) as Record<
        string,
        unknown
      >
      setLastRead(JSON.stringify(j, null, 2))
      const ra = Number(j['ra_hours'])
      const dec = Number(j['dec_degrees'])
      if (Number.isFinite(ra) && Number.isFinite(dec)) {
        onApplyIcrs?.(ra, dec)
      }
    })
  }, [commandToken, onApplyIcrs, withBusy])

  const nearlyEq = (a: number, b: number, eps: number): boolean => Math.abs(a - b) <= eps

  const nudge = useCallback(
    (deltaRaSec: number, deltaDecArcsec: number) => {
      return withBusy(async () => {
        setStaleHint(null)
        const j = (await telescopePost(
          '/telescopes/commands/nudge-equatorial',
          { delta_ra_sidereal_seconds: deltaRaSec, delta_dec_arcseconds: deltaDecArcsec },
          commandToken || undefined,
        )) as Record<string, unknown>

        const priorRa = Number(j['prior_ra_hours'])
        const priorDec = Number(j['prior_dec_degrees'])
        const targetRa = Number(j['target_ra_hours'])
        const targetDec = Number(j['target_dec_degrees'])

        if (
          Number.isFinite(priorRa) &&
          Number.isFinite(targetRa) &&
          Number.isFinite(priorDec) &&
          Number.isFinite(targetDec) &&
          nearlyEq(priorRa, targetRa, 1.3334e-5) &&
          nearlyEq(priorDec, targetDec, 7 / 36_000)
        ) {
          setStaleHint(
            'Target matches prior within driver precision — any motion may be invisible. Confirm connectivity to Alpaca, try RA-only presets, or check mount power / clamps.',
          )
        }

        setLastNudge(JSON.stringify(j, null, 2))
        const ra = targetRa
        const dec = targetDec
        if (Number.isFinite(ra) && Number.isFinite(dec)) {
          onApplyIcrs?.(ra, dec)
        }
      })
    },
    [commandToken, onApplyIcrs, withBusy],
  )

  const { raSec, decArcsec } = step

  return (
    <div className="panel panel--full mount-nudge-panel">
      <header className="panel-header">
        <h2 className="panel-title">Mount jog · ICRS equatorial bumps</h2>
        <p className="panel-lead">
          Reads Alpaca <code>RightAscension</code>/<code>Declination</code>, slews relative to those numbers. Buttons
          combine <strong>sidereal seconds of RA</strong> and <strong>arcseconds of declination</strong> — those are{' '}
          <em>not</em> image degrees unless you convert (see Degree reference below). This steers the{' '}
          <strong>mount</strong>, not a PTZ tweak of the JPEG preview alone.
        </p>
      </header>

      <p className="hint mount-nudge-orientation">
        <strong>Degrees reference:</strong> ΔRA expressed in apparent degrees near the celestial equator (δ≈0) roughly
        equals <code>(ΔRA_sidereal_seconds / 3600) × 15</code>. Older builds capped ΔRA near{' '}
        <code>±3600s</code>, i.e. <strong>~±15°</strong> Eq per click regardless of labels — use{' '}
        <strong>RA-only (~180° Eq)</strong> when you need a hemisphere-wide east/west slew. Compass arrows denote sky
        sphere axes; the Seestar image can be arbitrarily rotated versus those axes.
      </p>

      <div className="row mount-nudge-toolbar">
        <label className="mount-nudge-select-wrap">
          <span>Step preset</span>
          <select value={presetId} onChange={(e) => setPresetId(e.target.value)} disabled={busy}>
            {optionsGrouped.map(([group, items]) => (
              <optgroup key={group} label={group}>
                {items.map((row) => (
                  <option key={row.id} value={row.id}>
                    ΔRA {fmtRaSec(row.raSec)} · ΔDec {fmtDecArcsec(row.decArcsec)}
                    {formatDegreesHint(row)}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        </label>
        <button type="button" className="secondary" disabled={busy} onClick={() => void refreshPosition()}>
          GET mount/icrs-equatorial
        </button>
      </div>

      <div className="mount-nudge-pad" aria-label="Equatorial jog pad">
        <div className="mount-nudge-grid">
          <span className="mount-nudge-spacer" />
          <button
            type="button"
            className="mount-nudge-btn mount-nudge-btn--dir"
            disabled={busy}
            title={`North on Dec axis: +${decArcsec}″ declination`}
            onClick={() => void nudge(0, decArcsec)}
          >
            <span className="mount-nudge-arrow" aria-hidden>
              ↑
            </span>
            <span className="mount-nudge-letter">N</span>
            <span className="mount-nudge-axis">+Dec</span>
          </button>
          <span className="mount-nudge-spacer" />

          <button
            type="button"
            className="mount-nudge-btn mount-nudge-btn--dir"
            disabled={busy}
            title={`West: −${raSec}s sidereal RA`}
            onClick={() => void nudge(-raSec, 0)}
          >
            <span className="mount-nudge-arrow" aria-hidden>
              ←
            </span>
            <span className="mount-nudge-letter">W</span>
            <span className="mount-nudge-axis">−RA</span>
          </button>
          <div className="mount-nudge-center" aria-hidden>
            <span className="mount-nudge-step-label">
              ΔRA {fmtRaSec(raSec)}
              <br />
              ΔDec {fmtDecArcsec(decArcsec)}
              {formatDegreesHint(step)}
            </span>
          </div>
          <button
            type="button"
            className="mount-nudge-btn mount-nudge-btn--dir"
            disabled={busy}
            title={`East: +${raSec}s sidereal RA`}
            onClick={() => void nudge(raSec, 0)}
          >
            <span className="mount-nudge-arrow" aria-hidden>
              →
            </span>
            <span className="mount-nudge-letter">E</span>
            <span className="mount-nudge-axis">+RA</span>
          </button>

          <span className="mount-nudge-spacer" />
          <button
            type="button"
            className="mount-nudge-btn mount-nudge-btn--dir"
            disabled={busy}
            title={`South on Dec axis: −${decArcsec}″ declination`}
            onClick={() => void nudge(0, -decArcsec)}
          >
            <span className="mount-nudge-arrow" aria-hidden>
              ↓
            </span>
            <span className="mount-nudge-letter">S</span>
            <span className="mount-nudge-axis">−Dec</span>
          </button>
          <span className="mount-nudge-spacer" />
        </div>
      </div>

      <p className="hint">
        If <code>GET /telescopes/status</code> reports <code>alpaca_live.reachable:false</code> with a Docker timeout,
        containers must reach Seestar LAN IP/port (Compose often vs host bridge). Huge declination deltas clamp to ±90°
        poles — expect partial motion if you live near the clamps.
      </p>

      {staleHint ? <p className="hint hint--callout">{staleHint}</p> : null}

      {lastRead ? (
        <>
          <h3 className="subhead">Last mount position</h3>
          <pre className="json mount-nudge-json">{lastRead}</pre>
        </>
      ) : null}
      {lastNudge ? (
        <>
          <h3 className="subhead">Last nudge response</h3>
          <pre className="json mount-nudge-json">{lastNudge}</pre>
        </>
      ) : null}
    </div>
  )
}
