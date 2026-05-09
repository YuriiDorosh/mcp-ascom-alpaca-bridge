import { useState } from 'react'
import { telescopePost } from '../../api'
import { formatJson } from '../../formatJson'
import type { WithBusyFn } from './types'

type Props = { withBusy: WithBusyFn; busy: boolean }

export function CoordinatesPanel({ withBusy, busy }: Props) {
  const [raHours, setRaHours] = useState(5.5)
  const [decDeg, setDecDeg] = useState(22.0)
  const [latitudeDeg, setLatitudeDeg] = useState(50.45)
  const [longitudeDeg, setLongitudeDeg] = useState(30.52)
  const [elevationM, setElevationM] = useState(180)
  const [obstimeUtcIso, setObstimeUtcIso] = useState(() => new Date().toISOString().slice(0, 19) + 'Z')
  const [altAzResult, setAltAzResult] = useState<unknown>(null)

  const convert = () =>
    withBusy(async () => {
      const j = await telescopePost('/telescopes/coordinates/radec-to-altaz', {
        ra_hours: raHours,
        dec_degrees: decDeg,
        latitude_deg: latitudeDeg,
        longitude_deg: longitudeDeg,
        elevation_m: elevationM,
        obstime_utc_iso: obstimeUtcIso.trim(),
      })
      setAltAzResult(j)
    })

  return (
    <div className="panel">
      <header className="panel-header">
        <h2 className="panel-title">Sky map → local direction</h2>
        <p className="panel-lead">
          Convert “where in the sky catalogue” (RA/Dec) into altitude &amp; azimuth for an observer on Earth — think
          compass direction and how high above the horizon it sits.
        </p>
      </header>
      <p className="hint">
        Example site defaults to central Ukraine placeholders; replace latitude, longitude, and elevation with your
        observing spot for real answers.
      </p>
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
          <span>Dec (°)</span>
          <input type="number" step="any" value={decDeg} onChange={(e) => setDecDeg(Number(e.target.value))} />
        </label>
      </div>
      <div className="row">
        <label>
          <span>Latitude (°)</span>
          <input
            type="number"
            step="any"
            value={latitudeDeg}
            onChange={(e) => setLatitudeDeg(Number(e.target.value))}
          />
        </label>
        <label>
          <span>Longitude (°)</span>
          <input
            type="number"
            step="any"
            value={longitudeDeg}
            onChange={(e) => setLongitudeDeg(Number(e.target.value))}
          />
        </label>
        <label>
          <span>Elevation (m)</span>
          <input
            type="number"
            step="any"
            value={elevationM}
            onChange={(e) => setElevationM(Number(e.target.value))}
          />
        </label>
      </div>
      <div className="row">
        <label>
          <span>obstime UTC ISO</span>
          <input type="text" value={obstimeUtcIso} onChange={(e) => setObstimeUtcIso(e.target.value)} spellCheck={false} />
        </label>
        <button type="button" disabled={busy} onClick={convert}>
          Convert
        </button>
      </div>
      {altAzResult != null ? (
        <>
          <h3 className="subhead">Horizontal coordinates</h3>
          <pre className="json">{formatJson(altAzResult)}</pre>
        </>
      ) : null}
    </div>
  )
}
