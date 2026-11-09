import * as React from 'react'
import { Check, Download, ExternalLink, Loader2, Trash2 } from 'lucide-react'
import { api, getJSON, send } from '@/lib/api'
import { Badge, Button, Dialog, DialogContent, Label, Progress, Select, Switch, Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui'

const field = 'h-9 w-full rounded-md bg-muted px-2.5 text-sm outline-none focus:ring-2 focus:ring-ring'

/** Lists the models, with a Download button for each one that is not on this computer yet. */
function ModelsTab({ models, reload }) {
  const [busy, setBusy] = React.useState({})
  const go = async (id) => { setBusy((b) => ({ ...b, [id]: true })); await send(`/api/models/${id}/download`, 'POST').catch(() => {}); reload(); setBusy((b) => ({ ...b, [id]: false })) }
  const rm = async (m) => { if (confirm(`Delete “${m.label}” from this computer? You can download it again later.`)) { await api(`/api/models/${m.id}`, { method: 'DELETE' }).catch(() => {}); reload() } }
  return (
    <div className="space-y-2.5">
      <p className="text-xs text-muted-foreground">
        The speech and cut-out models are not bundled with the app. Press <b className="text-foreground">Download</b> once for the ones you want; they are saved in the
        <code className="mx-1 rounded bg-muted px-1">models/</code> folder and used offline afterwards. Nothing is downloaded unless you press a button.
      </p>
      {models.map((m) => (
        <div key={m.id} className="rounded-lg border bg-card/40 p-3">
          <div className="flex items-start gap-3">
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2 text-sm font-semibold">{m.label}
                {m.installed && <Badge tone="new" className="gap-1"><Check className="h-3 w-3" />Ready</Badge>}
              </div>
              <div className="mt-0.5 text-xs text-muted-foreground">{m.desc}</div>
              <div className="mt-1 text-[11px] text-muted-foreground">~{m.size_mb >= 1000 ? (m.size_mb / 1000).toFixed(1) + ' GB' : m.size_mb + ' MB'} · licence {m.license}</div>
              {m.error && <div className="mt-1 text-xs text-red-400">Download failed: {m.error}</div>}
            </div>
            <div className="shrink-0">
              {m.installed
                ? <Button size="sm" variant="ghost" onClick={() => rm(m)} title="Delete from this computer"><Trash2 className="h-4 w-4" /></Button>
                : m.downloading
                  ? <div className="flex items-center gap-2 text-xs"><Loader2 className="h-4 w-4 animate-spin" />{Math.round(m.progress * 100)}%</div>
                  : <Button size="sm" onClick={() => go(m.id)} disabled={busy[m.id]}><Download className="h-4 w-4" />Download</Button>}
            </div>
          </div>
          {m.downloading && <Progress value={Math.max(3, Math.round(m.progress * 100))} className="mt-2 h-2" />}
        </div>
      ))}
    </div>
  )
}

/** Provider, model and API key for the AI clean-up pass (numbers as digits, Hinglish spelling). */
function AiTab() {
  const [cfg, setCfg] = React.useState(null)
  const [form, setForm] = React.useState({})
  const [key, setKey] = React.useState('')
  const [test, setTest] = React.useState(null)
  const [saved, setSaved] = React.useState(false)
  const load = React.useCallback(async () => { const d = await getJSON('/api/settings'); setCfg(d); setForm(d.ai) }, [])
  React.useEffect(() => { load().catch(() => {}) }, [load])
  if (!cfg) return <div className="py-6 text-center text-sm text-muted-foreground">Loading…</div>
  const set = (k, v) => { setForm((f) => ({ ...f, [k]: v })); setSaved(false); setTest(null) }
  const pickProvider = (p) => { const pr = cfg.providers[p]; setForm((f) => ({ ...f, provider: p, url: pr.url || f.url, model: pr.model || f.model })); setSaved(false); setTest(null) }
  const body = () => ({ enabled: form.enabled, provider: form.provider, url: form.url, model: form.model, fallback: form.fallback || '', ...(key.trim() ? { key } : {}) })
  const save = async () => { const r = await send('/api/settings/ai', 'PUT', body()).then((x) => x.json()).catch(() => null); if (r) { setCfg(r); setForm(r.ai); setKey(''); setSaved(true) } }
  const runTest = async () => { setTest({ busy: true }); const r = await send('/api/settings/ai/test', 'POST', { url: form.url, model: form.model, key }).then((x) => x.json()).catch((e) => ({ ok: false, message: String(e) })); setTest(r) }
  const pr = cfg.providers[form.provider] || {}
  return (
    <div className="space-y-3">
      <p className="text-xs text-muted-foreground">
        After the speech model writes the transcript, an AI model can tidy it: spoken numbers become digits (“bees” → 20), Hinglish gets natural spelling
        (“ye”, “ke liye”), English words keep English spelling. It is optional. When on, <b className="text-foreground">the transcript text (not the video or audio)</b> is
        sent to the provider you choose below.
      </p>
      <div className="flex items-center justify-between rounded-lg border p-2.5 text-sm">
        <span>Use AI to polish transcripts</span><Switch checked={!!form.enabled} onCheckedChange={(v) => set('enabled', v)} />
      </div>
      <div className="space-y-1.5"><Label>Provider</Label>
        <Select value={form.provider} onValueChange={pickProvider} options={Object.entries(cfg.providers).map(([value, p]) => ({ value, label: p.label }))} />
        {pr.keys_url && <a href={pr.keys_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-[11px] text-primary hover:underline">Get a key <ExternalLink className="h-3 w-3" /></a>}
      </div>
      <div className="space-y-1.5"><Label>API key</Label>
        <input type="password" autoComplete="off" spellCheck={false} className={field} value={key} onChange={(e) => { setKey(e.target.value); setSaved(false) }}
          placeholder={cfg.ai.key_set ? `Saved (${cfg.ai.key_hint}) — type a new one to replace it` : 'Paste your API key'} />
        <p className="text-[11px] text-muted-foreground">
          Stored only on this computer, in <code className="rounded bg-muted px-1">workspace/settings.json</code>. You can also set it as an environment variable instead
          (<code className="rounded bg-muted px-1">AI_API_KEY</code>, or <code className="rounded bg-muted px-1">GROQ_API_KEY</code> / <code className="rounded bg-muted px-1">OPENAI_API_KEY</code> / <code className="rounded bg-muted px-1">XAI_API_KEY</code>).
          {cfg.ai.key_set && cfg.ai.key_source.startsWith('environment') ? ` Currently using the key from the ${cfg.ai.key_source}.` : ''}
        </p>
      </div>
      <div className="grid grid-cols-2 gap-3 max-[640px]:grid-cols-1">
        <div className="space-y-1.5"><Label>Model</Label><input className={field} value={form.model || ''} onChange={(e) => set('model', e.target.value)} spellCheck={false} /></div>
        <div className="space-y-1.5"><Label>Backup model (optional)</Label><input className={field} value={form.fallback || ''} onChange={(e) => set('fallback', e.target.value)} spellCheck={false} /></div>
      </div>
      <div className="space-y-1.5"><Label>API address (chat completions)</Label><input className={field} value={form.url || ''} onChange={(e) => set('url', e.target.value)} spellCheck={false} /></div>
      <div className="flex flex-wrap items-center gap-2">
        <Button onClick={save}>Save</Button>
        <Button variant="secondary" onClick={runTest} disabled={test && test.busy}>{test && test.busy ? <Loader2 className="h-4 w-4 animate-spin" /> : null}Test</Button>
        {saved && <span className="text-xs text-success">Saved</span>}
        {test && !test.busy && <span className={test.ok ? 'text-xs text-success' : 'text-xs text-red-400'}>{test.message}</span>}
      </div>
    </div>
  )
}

export default function SettingsDialog({ open, onOpenChange, onChanged }) {
  const [models, setModels] = React.useState([])
  const reload = React.useCallback(async () => { const m = await getJSON('/api/models').catch(() => null); if (m) { setModels(m); onChanged && onChanged(m) } return m }, [onChanged])
  React.useEffect(() => {
    if (!open) return undefined
    let dead = false
    const tick = async () => { const m = await reload(); if (!dead) setTimeout(tick, m && m.some((x) => x.downloading) ? 1200 : 4000) }
    tick()
    return () => { dead = true }
  }, [open, reload])
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent title="Settings" description="Models and the optional AI polish." className="w-[min(760px,94vw)]">
        <Tabs defaultValue="models">
          <TabsList className="mb-3"><TabsTrigger value="models">Models</TabsTrigger><TabsTrigger value="ai">AI polish</TabsTrigger></TabsList>
          <TabsContent value="models"><ModelsTab models={models} reload={reload} /></TabsContent>
          <TabsContent value="ai"><AiTab /></TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
