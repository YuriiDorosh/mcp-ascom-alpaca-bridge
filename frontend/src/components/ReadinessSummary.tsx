type Props = { data: unknown }

export function ReadinessSummary({ data }: Props) {
  if (!data || typeof data !== 'object') {
    return null
  }
  const o = data as Record<string, unknown>
  const req = o.requires_real_telescope_now
  const trigger = o.trigger_task_id
  const action = o.operator_action
  if (typeof req !== 'boolean') {
    return null
  }
  return (
    <p className="preflight-summary">
      <span className={req ? 'req-pill req-pill--yes' : 'req-pill req-pill--no'}>
        {req ? 'Real telescope needed for HIL gate' : 'Software / dry-run paths OK without live mount'}
      </span>
      {typeof trigger === 'string' && trigger ? (
        <>
          {' '}
          · task <code>{trigger}</code>
        </>
      ) : null}
      {typeof action === 'string' && action ? (
        <>
          <br />
          <span className="preflight-action">{action}</span>
        </>
      ) : null}
    </p>
  )
}
