import { useCallback, useState } from 'react'
import { telescopeGet, telescopePost } from '../../api'

type StepPreset = 'fine' | 'medium' | 'coarse'

function stepSiderealPairs(preset: StepPreset): { raSec: number; decArcsec: number } {
  switch (preset) {
    case 'fine':
      return { raSec: 30, decArcsec: 120 }
    case 'medium':
      return { raSec: 120, decArcsec: 480 }
    case 'coarse':
      return { raSec: 300, decArcsec: 1200 }
    default:
      return { raSec: 120, decArcsec: 480 }
  }
}

type Props = {
  withBusy: <T>(fn: () => Promise<T>) => Promise<T | undefined>
  busy: boolean
  commandToken: string
  onApplyIcrs?: (ra: number, dec: number) => void
}

/** Small equatorial bumps (read current + slew) — not a dome/camera joystick. */
export function MountNudgePanel(props: Props) {
  const { withBusy, busy, commandToken, onApplyIcrs } = props
  const [preset, setPreset] = useState<StepPreset>('medium')
  const [lastRead, setLastRead] = useState<string | null>(null)
  const [lastNudge, setLastNudge] = useState<string | null>(null)

  const refreshPosition = useCallback(() => {
    return withBusy(async () => {
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

  const nudge = useCallback(
    (deltaRaSec: number, deltaDecArcsec: number) => {
      return withBusy(async () => {
        const j = (await telescopePost(
          '/telescopes/commands/nudge-equatorial',
          { delta_ra_sidereal_seconds: deltaRaSec, delta_dec_arcseconds: deltaDecArcsec },
          commandToken || undefined,
        )) as Record<string, unknown>
        setLastNudge(JSON.stringify(j, null, 2))
        const ra = Number(j['target_ra_hours'])
        const dec = Number(j['target_dec_degrees'])
        if (Number.isFinite(ra) && Number.isFinite(dec)) {
          onApplyIcrs?.(ra, dec)
        }
      })
    },
    [commandToken, onApplyIcrs, withBusy],
  )

  const { raSec, decArcsec } = stepSiderealPairs(preset)

  return (
    <div className="panel panel--full mount-nudge-panel">
      <header className="panel-header">
        <h2 className="panel-title">Mount jog · ICRS equatorial bumps</h2>
        <p className="panel-lead">
          Reads current Alpaca <code>RightAscension</code>/<code>Declination</code>, then issues a short slew. Units: RA
          offset in <strong>sidereal seconds</strong> (east positive); Dec offset in <strong>arcseconds</strong> (north
          positive). This steers the <strong>mount</strong>, not an independent camera PTZ.
        </p>
      </header>

      <div className="row mount-nudge-toolbar">
        <label>
          <span>Step size</span>
          <select value={preset} onChange={(e) => setPreset(e.target.value as StepPreset)} disabled={busy}>
            <option value="fine">Fine (~30s RA · 2′ Dec)</option>
            <option value="medium">Medium (~2m RA · 8′ Dec)</option>
            <option value="coarse">Coarse (~5m RA · 20′ Dec)</option>
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
            className="mount-nudge-btn"
            disabled={busy}
            title={`North +${decArcsec}″ Dec`}
            onClick={() => void nudge(0, decArcsec)}
          >
            N
          </button>
          <span className="mount-nudge-spacer" />

          <button
            type="button"
            className="mount-nudge-btn"
            disabled={busy}
            title={`West −${raSec}s RA`}
            onClick={() => void nudge(-raSec, 0)}
          >
            W
          </button>
          <div className="mount-nudge-center" aria-hidden>
            <span className="mount-nudge-step-label">
              ΔRA {raSec}s · ΔDec {decArcsec}″
            </span>
          </div>
          <button
            type="button"
            className="mount-nudge-btn"
            disabled={busy}
            title={`East +${raSec}s RA`}
            onClick={() => void nudge(raSec, 0)}
          >
            E
          </button>

          <span className="mount-nudge-spacer" />
          <button
            type="button"
            className="mount-nudge-btn"
            disabled={busy}
            title={`South −${decArcsec}″ Dec`}
            onClick={() => void nudge(0, -decArcsec)}
          >
            S
          </button>
          <span className="mount-nudge-spacer" />
        </div>
      </div>

      <p className="hint">
        Command token is required when <code>COMMAND_AUTH_TOKEN</code> is set. After a successful nudge, the mount
        command form can pick up the new target from the response (or press refresh to copy from the driver).
      </p>

      {lastRead ? (
        <>
          <h3 className="subhead">Last mount position</h3>
          <pre className="json mount-nudge-json">{lastRead}</pre>
        </>
      ) : null}
      {lastNudge ? (
        <>
          <h3 className="subhead">Last nudge ack</h3>
          <pre className="json mount-nudge-json">{lastNudge}</pre>
        </>
      ) : null}
    </div>
  )
}
