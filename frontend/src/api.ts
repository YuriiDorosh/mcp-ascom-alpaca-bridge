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
