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
  { id: 'm03', group: 'Найтонше (повільне підлагоджування)', raSec: 0.03, decArcsec: 0.12 },
  { id: 'm06', group: 'Найтонке', raSec: 0.06, decArcsec: 0.25 },
  { id: 'm10', group: 'Найтонке', raSec: 0.1, decArcsec: 0.5 },
  { id: 'm25', group: 'Найтонке', raSec: 0.25, decArcsec: 1 },
  { id: 'm05_2', group: 'Найтонке', raSec: 0.5, decArcsec: 2 },
  { id: 'm1_4', group: 'Дуже дрібне', raSec: 1, decArcsec: 4 },
  { id: 'm2_8', group: 'Дуже дрібне', raSec: 2, decArcsec: 8 },
  { id: 'm5_20', group: 'Дрібне', raSec: 5, decArcsec: 20 },
  { id: 'm12_48', group: 'Дрібне', raSec: 12, decArcsec: 48 },
  { id: 'm24_96', group: 'Мале', raSec: 24, decArcsec: 96 },
  { id: 'm42_168', group: 'Мале', raSec: 42, decArcsec: 168 },
  { id: 'm72_288', group: 'Середнє-', raSec: 72, decArcsec: 288 },
  { id: 'm120_480', group: 'Середнє', raSec: 120, decArcsec: 480 },
  { id: 'm210_840', group: 'Середнє', raSec: 210, decArcsec: 840 },
  { id: 'm330_1320', group: 'Середнє+', raSec: 330, decArcsec: 1320 },
  { id: 'm480_1920', group: 'Велике-', raSec: 480, decArcsec: 1920 },
  { id: 'm780_3120', group: 'Велике', raSec: 780, decArcsec: 3120 },
  { id: 'm1200_4800', group: 'Велике', raSec: 1200, decArcsec: 4800 },
  { id: 'm1650_6600', group: 'Велике+', raSec: 1650, decArcsec: 6600 },
  { id: 'm2280_9120', group: 'Найбільші кроки (дуже широкі стрибки)', raSec: 2280, decArcsec: 9120 },
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
            'Цільова позиція збіглась з попередньою з точністю драйвера — рух могло бути не видно. Спробуй більший крок або перевір статус альпака.',
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
          Читає поточний Alpaca{' '}
          <code>
            RightAscension
          </code> /{' '}
          <code>
            Declination
          </code>{' '}
          і робить короткий slew до нової екваторіальної цілі. Це <strong>монтування телескопа</strong>, не керування
          дзеркальною камерою pan/tilt.
        </p>
      </header>

      <p className="hint mount-nudge-orientation">
        <strong>Стрілки на кнопках</strong> — напрямок на <strong>небесній сфері</strong> (ICRS): N/S змінюють
        declination (↑ північний полюс сфери, ↓ південь), E/W — right ascension (→ схід, тобто більша година RA; ←
        захід). Кадр Seestar може бути повернутий і обрізаний, тому «вгорі кнопки N» не означає «вгору по зображенню».
      </p>

      <div className="row mount-nudge-toolbar">
        <label className="mount-nudge-select-wrap">
          <span>Крок (градація)</span>
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
            title={`Північ по Dec: +${decArcsec}″ declination`}
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
            title={`Захід: −${raSec}s RA (менша година)`}
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
            title={`Схід: +${raSec}s RA (більша година)`}
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
            title={`Південь по Dec: −${decArcsec}″ declination`}
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
        Якщо увімкнено{' '}
        <code>COMMAND_AUTH_TOKEN</code>, потрібен заголовок токена. Як поспішають короткі nudge підряд, деякі драйвери
        все одно роблять повний асинхронний slew (~секунди) — тривалість запиту не завжди залежить від розміру кроку.
        Після кожної серії затиснень є сенс натиснути «GET mount», щоб зчитати факт RA/Dec.
      </p>

      {staleHint ? <p className="hint hint--callout">{staleHint}</p> : null}

      {lastRead ? (
        <>
          <h3 className="subhead">Остання позиція монту</h3>
          <pre className="json mount-nudge-json">{lastRead}</pre>
        </>
      ) : null}
      {lastNudge ? (
        <>
          <h3 className="subhead">Остання відповідь nudge</h3>
          <pre className="json mount-nudge-json">{lastNudge}</pre>
        </>
      ) : null}
    </div>
  )
}
