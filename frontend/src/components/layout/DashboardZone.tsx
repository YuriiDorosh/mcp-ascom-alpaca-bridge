import type { ReactNode } from 'react'

export type DashboardZoneCols = 'single' | 'fluid' | 'pair'

type Props = {
  zoneId: string
  title: string
  description?: string
  cols: DashboardZoneCols
  children: ReactNode
}

/** Groups related operator cards; layout inspired by segmented imaging workspaces (see docs/PLAN.md). */
export function DashboardZone({ zoneId, title, description, cols, children }: Props) {
  return (
    <section className="workspace-zone" aria-labelledby={zoneId}>
      <header className="zone-head">
        <h2 className="zone-kicker" id={zoneId}>
          {title}
        </h2>
        {description ? <p className="zone-desc">{description}</p> : null}
      </header>
      <div className={`zone-grid zone-grid--${cols}`}>{children}</div>
    </section>
  )
}
