export async function api(url, opts) {
  const r = await fetch(url, opts)
  if (!r.ok) throw new Error((await r.text()).slice(0, 300))
  return r
}
export const getJSON = async (u) => (await api(u)).json()
export const send = (u, method, body) =>
  api(u, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body ?? {}) })
export const qs = (o) => encodeURIComponent(JSON.stringify(o))
