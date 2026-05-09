import { useCallback, useMemo, useState } from 'react'
import { telescopeGet, telescopePost } from '../../api'

/** One jog step: ΔRA sidereal seconds (east +), ΔDec arcseconds (north +). */
type StepPreset = {
  readonly id: string
  readonly group: string
  readonly raSec: number
  readonly decArcsec: number
}

/**
 * Dense graduation: quasi-«millimetric» at the bottom (fractions of arcsecond /
 * hundredths sidereal-second), sensible middle, big sweeps at the top.
 * Backend caps roughly ±3600s RA · ±21600″ Dec — we stay safely inside both.
 */
const STEP_PRESETS: readonly StepPreset[] = [
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
  { id: 'm2280_9120', group: 'Largest bumps (wide steps)', raSec: 2280, decArcsec: 9120 },
] as const

const DEFAULT_STEP_ID = 'm2_8'

function presetById(id: string): StepPreset | undefined {
  return STEP_PRESETS.find((p) => p.id === id)
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

type Props = {
  withBusy: <T>(fn: () => Promise<T>) => Promise<T | undefined>
  busy: boolean
  commandToken: string
  onApplyIcrs?: (ra: number, dec: number) => void
}

/** Small equatorial bumps (read current + slew) — mount axes, not camera PTZ. */
export function MountNudgePanel(props: Props) {
  const { withBusy, busy, commandToken, onApplyIcrs } = props
  const [presetId, setPresetId] = useState<string>(DEFAULT_STEP_ID)
  const [lastRead, setLastRead] = useState<string | null>(null)
  const [lastNudge, setLastNudge] = useState<string | null>(null)
  const [staleHint, setStaleHint] = useState<string | null>(null)

  const step = presetById(presetId) ?? presetById(DEFAULT_STEP_ID)!

  const optionsGrouped = useMemo(() => {
    const map = new Map<string, StepPreset[]>()
    for (const p of STEP_PRESETS) {
      const list = map.get(p.group) ?? []
      list.push(p)
      map.set(p.group, list)
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

        /* Rough float tolerance in driver units (~0.048 sidereal-second RA slice, ~0.7″ Dec). */
        if (
          Number.isFinite(priorRa) &&
          Number.isFinite(targetRa) &&
          Number.isFinite(priorDec) &&
          Number.isFinite(targetDec) &&
          nearlyEq(priorRa, targetRa, 1.3334e-5) &&
          nearlyEq(priorDec, targetDec, 7 / 36_000)
        ) {
          setStaleHint(
            'Target matches prior within driver precision — any motion may be invisible. Try a larger step or check Alpaca / mount status.',
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
          Reads the current Alpaca <code>RightAscension</code>/<code>Declination</code>, then executes a short slew to a new
          equatorial target. This moves the <strong>telescope mount</strong>, not a separate PTZ steer for the imaging
          camera.
        </p>
      </header>

      <p className="hint mount-nudge-orientation">
        <strong>Button arrows</strong> describe motion on the <strong>sky sphere</strong> (ICRS): N/S bump declination (↑
        toward the north celestial pole, ↓ south), while E/W change right ascension (→ east, higher RA hour value; ←
        west). A Seestar preview can be cropped or rotated — “N above the keypad” does <em>not</em> imply “toward the
        top edge of your image”.
      </p>

      <div className="row mount-nudge-toolbar">
        <label className="mount-nudge-select-wrap">
          <span>Step size</span>
          <select value={presetId} onChange={(e) => setPresetId(e.target.value)} disabled={busy}>
            {optionsGrouped.map(([group, items]) => (
              <optgroup key={group} label={group}>
                {items.map((p) => (
                  <option key={p.id} value={p.id}>
                    ΔRA {fmtRaSec(p.raSec)} · ΔDec {fmtDecArcsec(p.decArcsec)}
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
            title={`West: −${raSec}s sidereal RA (earlier RA hours)`}
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
              ΔRA {fmtRaSec(raSec)} · ΔDec {fmtDecArcsec(decArcsec)}
            </span>
          </div>
          <button
            type="button"
            className="mount-nudge-btn mount-nudge-btn--dir"
            disabled={busy}
            title={`East: +${raSec}s sidereal RA (later RA hours)`}
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
        When <code>COMMAND_AUTH_TOKEN</code> is set, callers must supply the matching header. Even tiny back-to-back
        nudges often pay the cost of one async Alpaca slew cycle (often seconds)—request latency is not proportional to
        step size on every rig. Between bursts, tap <strong>GET mount/icrs-equatorial</strong> to confirm the RA/Dec the
        driver reports.
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
