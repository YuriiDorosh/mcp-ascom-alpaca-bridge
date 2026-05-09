let runtimeApiBase: string | null = null

export function setRuntimeApiBase(url: string): void {
  runtimeApiBase = url.trim().replace(/\/$/, '')
}

export function getApiBase(): string {
  if (runtimeApiBase) {
    return runtimeApiBase
  }
  const raw = import.meta.env.VITE_API_BASE
  if (raw && raw.length > 0) {
    return raw.replace(/\/$/, '')
  }
  return 'http://127.0.0.1:8000'
}

/** WebSocket URL for operator telemetry (`/telescopes/ws/operator` on the API host). */
export function getOperatorWebSocketUrl(): string {
  const base = getApiBase()
  if (base.startsWith('https://')) {
    return `wss://${base.slice('https://'.length)}/telescopes/ws/operator`
  }
  if (base.startsWith('http://')) {
    return `ws://${base.slice('http://'.length)}/telescopes/ws/operator`
  }
  return `${base}/telescopes/ws/operator`
}

function headersRead(token?: string): Record<string, string> {
  const h: Record<string, string> = { Accept: 'application/json' }
  if (token) {
    h['X-Command-Token'] = token
  }
  return h
}

function headersJson(token?: string): Record<string, string> {
  return {
    ...headersRead(token),
    'Content-Type': 'application/json',
  }
}

/** Unauthenticated GET for system routes (`/health`, `/ready`) and similar. */
export async function apiGet(path: string): Promise<unknown> {
  const base = getApiBase()
  const res = await fetch(`${base}${path}`, {
    headers: { Accept: 'application/json' },
  })
  const text = await res.text()
  if (!res.ok) {
    throw new Error(`${res.status}: ${text || res.statusText}`)
  }
  return text ? JSON.parse(text) : null
}

export async function telescopeGet(path: string, token?: string): Promise<unknown> {
  const base = getApiBase()
  const res = await fetch(`${base}${path}`, {
    headers: headersRead(token),
  })
  const text = await res.text()
  if (!res.ok) {
    throw new Error(`${res.status}: ${text || res.statusText}`)
  }
  return text ? JSON.parse(text) : null
}

export async function telescopePost(path: string, body: object, token?: string): Promise<unknown> {
  const base = getApiBase()
  const res = await fetch(`${base}${path}`, {
    method: 'POST',
    headers: headersJson(token),
    body: JSON.stringify(body),
  })
  const text = await res.text()
  if (!res.ok) {
    throw new Error(`${res.status}: ${text || res.statusText}`)
  }
  return text ? JSON.parse(text) : null
}

/** POST with query string (e.g. model inference enqueue-and-wait timeout params). */
export async function telescopePostWithQuery(
  path: string,
  body: object,
  query: Record<string, string | number | boolean>,
  token?: string,
): Promise<unknown> {
  const base = getApiBase()
  const q = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    q.set(key, String(value))
  }
  const suffix = q.toString() ? `?${q.toString()}` : ''
  const res = await fetch(`${base}${path}${suffix}`, {
    method: 'POST',
    headers: headersJson(token),
    body: JSON.stringify(body),
  })
  const text = await res.text()
  if (!res.ok) {
    throw new Error(`${res.status}: ${text || res.statusText}`)
  }
  return text ? JSON.parse(text) : null
}
