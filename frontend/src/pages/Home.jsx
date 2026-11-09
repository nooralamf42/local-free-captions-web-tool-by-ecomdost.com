import * as React from 'react'
import { Upload, Loader2, Check, Trash2, Wand2, Pencil, FolderOpen, Cpu, Film, AlertTriangle, Download, Play, Settings } from 'lucide-react'
import { Button, Badge, Progress, Select, ToggleGroup, ToggleItem, Label } from '@/components/ui'
import { useStore } from '@/store'
import { api, send } from '@/lib/api'
import { cn, fmtT } from '@/lib/utils'
import SettingsDialog from '@/components/SettingsDialog'

const LANGS = [['auto', 'Auto-detect'], ['en', 'English'], ['hi', 'Hindi / Hinglish'], ['ur', 'Urdu'], ['bn', 'Bengali'], ['mr', 'Marathi'],
  ['gu', 'Gujarati'], ['pa', 'Punjabi'], ['ta', 'Tamil'], ['te', 'Telugu'], ['kn', 'Kannada'], ['ml', 'Malayalam'], ['es', 'Spanish'],
  ['fr', 'French'], ['de', 'German'], ['pt', 'Portuguese'], ['ar', 'Arabic'], ['id', 'Indonesian']].map(([value, label]) => ({ value, label }))
const MODELS = [
  { value: 'turbo', label: 'Fast · large-v3-turbo (recommended)' },
  { value: 'apex', label: 'Hinglish · Apex (Roman letters, best for Hindi + English)' },
  { value: 'large', label: 'Best · large-v3 (slower)' },
  { value: 'medium', label: 'Medium' },
  { value: 'small', label: 'Small (quick drafts)' },
]
const BUSY = ['queued', 'transcribing', 'rendering']
const STEPS = ['Added', 'Transcribe', 'Edit', 'Export']

const stepIdx = (j) => (j.status === 'done' ? 3 : j.status === 'rendering' ? 3 : BUSY.includes(j.status) && !j.has_transcript ? 1 : j.has_transcript ? 2 : 0)
const fmtE = (s) => { s = Math.max(0, Math.round(s)); return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0') }

export default function Home() {
  const { state, refresh, speech, setSpeech, design } = useStore()
  const [drag, setDrag] = React.useState(false)
  const [settingsOpen, setSettingsOpen] = React.useState(false)
  const [models, setModels] = React.useState([])
  React.useEffect(() => { api('/api/models').then((r) => r.json()).then(setModels).catch(() => {}) }, [settingsOpen])
  const [upl, setUpl] = React.useState('')
  const fileRef = React.useRef()
  const dragN = React.useRef(0)

  const upload = React.useCallback(async (files) => {
    files = files.filter((f) => /^(video|audio)\//.test(f.type) || /\.(mp4|mov|mkv|webm|m4v|avi|mp3|wav|m4a)$/i.test(f.name))
    if (!files.length) { setUpl('No video files found in what you dropped.'); return }
    for (let i = 0; i < files.length; i++) {
      const label = `Uploading ${i + 1} of ${files.length}: ${files[i].name}`
      setUpl(label + ' — 0%')
      try {
        await new Promise((res, rej) => {
          const x = new XMLHttpRequest(); x.open('POST', '/api/upload')
          x.upload.onprogress = (e) => e.lengthComputable && setUpl(label + ' — ' + Math.round((e.loaded / e.total) * 100) + '%')
          x.onload = () => (x.status < 300 ? res() : rej(new Error(x.responseText)))
          x.onerror = () => rej(new Error('network error'))
          const fd = new FormData(); fd.append('files', files[i]); x.send(fd)
        })
      } catch (e) { setUpl('Upload failed: ' + e.message); return }
      refresh()
    }
    setUpl(`Added ${files.length} file(s). Press “Generate captions”.`)
  }, [refresh])

  // whole page is a drop target
  React.useEffect(() => {
    const has = (e) => e.dataTransfer && [...e.dataTransfer.types].includes('Files')
    const enter = (e) => { if (!has(e)) return; e.preventDefault(); dragN.current++; setDrag(true) }
    const over = (e) => { if (!has(e)) return; e.preventDefault(); e.dataTransfer.dropEffect = 'copy' }
    const leave = (e) => { if (!has(e)) return; dragN.current = Math.max(0, dragN.current - 1); if (!dragN.current) setDrag(false) }
    const drop = (e) => { if (!has(e)) return; e.preventDefault(); dragN.current = 0; setDrag(false); upload([...e.dataTransfer.files]) }
    window.addEventListener('dragenter', enter); window.addEventListener('dragover', over)
    window.addEventListener('dragleave', leave); window.addEventListener('drop', drop)
    return () => { window.removeEventListener('dragenter', enter); window.removeEventListener('dragover', over); window.removeEventListener('dragleave', leave); window.removeEventListener('drop', drop) }
  }, [upload])

  const jobs = state.jobs
  const active = jobs.find((j) => j.status === 'transcribing' || j.status === 'rendering')
  const waiting = jobs.filter((j) => j.status === 'queued').length
  const gen = async (j) => { await send(`/api/jobs/${j.id}/run`, 'POST', { kind: 'transcribe', ...speech }).catch(() => {}); refresh() }
  const del = async (j) => { await api(`/api/jobs/${j.id}`, { method: 'DELETE' }).catch(() => {}); refresh() }
  const genAll = async () => { for (const j of jobs) if (!BUSY.includes(j.status) && !j.has_transcript) await gen(j) }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <header className="flex items-center gap-3 border-b px-6 py-3">
        <div className="flex items-center gap-2 text-base font-semibold"><Film className="h-5 w-5 text-primary" />Local Captions</div>
        <Badge tone={state.gpu ? 'new' : 'warn'} className="gap-1"><Cpu className="h-3 w-3" />{state.gpu ? 'GPU transcription' : 'CPU only'} · {state.nvenc ? 'NVENC' : 'x264'}</Badge>
        <div className="flex-1" />
        <Button variant="ghost" size="sm" onClick={() => api('/api/open-outputs', { method: 'POST' })}><FolderOpen className="h-4 w-4" />Open outputs folder</Button>
        <Button variant="secondary" size="sm" onClick={() => setSettingsOpen(true)}><Settings className="h-4 w-4" />Settings</Button>
      </header>
      <SettingsDialog open={settingsOpen} onOpenChange={setSettingsOpen} onChanged={setModels} />

      {drag && (
        <div className="pointer-events-none fixed inset-3 z-50 flex items-center justify-center rounded-2xl border-4 border-dashed border-primary bg-background/90 text-3xl font-bold">
          Drop videos to add them
        </div>
      )}

      <div className="grid min-h-0 flex-1 grid-cols-[minmax(0,1fr)_380px] gap-5 overflow-hidden p-5 max-[1000px]:grid-cols-1 max-[1000px]:overflow-auto">
        <div className="flex min-h-0 flex-col gap-4 overflow-auto pr-1">
          <button
            onClick={() => fileRef.current.click()}
            className="flex cursor-pointer flex-col items-center gap-1 rounded-xl border-2 border-dashed bg-card/40 px-4 py-9 text-muted-foreground transition-colors hover:border-primary hover:text-foreground"
          >
            <Upload className="mb-1 h-6 w-6" />
            <b className="text-base text-foreground">Drop videos anywhere on this page</b>
            <span className="text-xs">or click to choose · as many as you like · no length or count limit</span>
          </button>
          <input ref={fileRef} type="file" accept="video/*,audio/*" multiple hidden onChange={(e) => { upload([...e.target.files]); e.target.value = '' }} />
          {upl && <div className="-mt-2 text-xs text-muted-foreground">{upl}</div>}

          {(active || waiting > 0) && (() => {
            const j = active || jobs.find((x) => x.status === 'queued')
            const pct = Math.round((j.progress || 0) * 100)
            return (
              <div className="rounded-xl border border-yellow-500/40 bg-yellow-500/5 p-3">
                <div className="flex items-center gap-2 text-sm font-semibold"><Loader2 className="h-4 w-4 animate-spin text-yellow-400" />
                  “{j.name}” — {j.stage || j.status}{active ? ` · ${pct}%` : ''}</div>
                <div className="mt-1 text-xs text-muted-foreground">
                  {active && j.started ? `${fmtE(state.now - j.started)} elapsed · ` : ''}{jobs.filter((x) => x.status === 'done').length} of {jobs.length} finished{waiting ? ` · ${waiting} waiting` : ''}
                </div>
                <Progress value={active ? pct : 3} className="mt-2 h-2.5" />
              </div>
            )
          })()}

          <div className="rounded-xl border bg-card/40">
            <div className="flex items-center justify-between px-4 py-3">
              <div className="text-sm font-semibold">Videos <span className="ml-1 text-muted-foreground">({jobs.length})</span></div>
              <Button size="sm" onClick={genAll} disabled={!jobs.some((j) => !j.has_transcript && !BUSY.includes(j.status))}><Wand2 className="h-4 w-4" />Generate captions for all</Button>
            </div>
            {jobs.length === 0 && <div className="px-4 pb-5 text-sm text-muted-foreground">Nothing yet. Drop a video above.</div>}
            {jobs.map((j) => <JobRow key={j.id} j={j} now={state.now} onGen={() => gen(j)} onDel={() => del(j)} />)}
          </div>

          <div className="rounded-xl border bg-card/40 p-4">
            <div className="mb-2 text-sm font-semibold">Activity <span className="text-xs font-normal text-muted-foreground">— what the app is doing</span></div>
            <LogBox log={state.log} />
          </div>
        </div>

        <aside className="flex min-h-0 flex-col gap-4 overflow-auto">
          <div className="rounded-xl border bg-card/40 p-4">
            <div className="mb-3 text-sm font-semibold">Speech</div>
            <div className="space-y-3">
              <div className="space-y-1.5"><Label>Language spoken</Label><Select value={speech.lang} onValueChange={(v) => setSpeech((s) => ({ ...s, lang: v }))} options={LANGS} /></div>
              <div className="space-y-1.5"><Label>Captions written as</Label>
                <ToggleGroup value={speech.mode} onValueChange={(v) => v && setSpeech((s) => ({ ...s, mode: v }))}>
                  <ToggleItem value="spoken">As spoken</ToggleItem><ToggleItem value="roman">Hinglish (Roman)</ToggleItem><ToggleItem value="translate">English</ToggleItem>
                </ToggleGroup>
                <p className="text-[11px] leading-snug text-muted-foreground">As spoken keeps Hindi in Devanagari. Hinglish types Hindi words in English letters. English translates the speech.</p>
              </div>
              <div className="space-y-1.5"><Label>Accuracy</Label><Select value={speech.model} onValueChange={(v) => setSpeech((s) => ({ ...s, model: v }))} options={MODELS.map((m) => ({ ...m, label: m.label + (models.length && !models.find((x) => x.id === m.value)?.installed ? ' — not downloaded' : '') }))} />
                {models.length > 0 && !models.find((x) => x.id === speech.model)?.installed && (
                  <div className="flex items-center gap-2 rounded-lg border border-yellow-500/40 bg-yellow-500/5 p-2 text-[11px]">
                    <AlertTriangle className="h-4 w-4 shrink-0 text-yellow-400" />
                    <span className="flex-1">This speech model is not on this computer yet.</span>
                    <Button size="xs" onClick={() => setSettingsOpen(true)}><Download className="h-3.5 w-3.5" />Download</Button>
                  </div>
                )}
              </div>
            </div>
          </div>
          <div className="rounded-xl border bg-card/40 p-4 text-xs text-muted-foreground">
            <div className="mb-1 text-sm font-semibold text-foreground">How it works</div>
            1. Drop videos · 2. <b className="text-foreground">Generate captions</b> · 3. <b className="text-foreground">Open editor</b> to pick a style (hover to see it animate), move/resize captions, change words per screen, fix text on the timeline · 4. <b className="text-foreground">Export</b> as many style versions as you want.
          </div>
        </aside>
      </div>
    </div>
  )
}

function JobRow({ j, now, onGen, onDel }) {
  const busy = BUSY.includes(j.status)
  const pct = Math.round((j.progress || 0) * 100)
  const si = stepIdx(j)
  return (
    <div className="border-t px-4 py-3">
      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1">
          <div className="truncate text-sm font-medium" title={j.name}>{j.name}</div>
          <div className="text-xs text-muted-foreground">
            {fmtT(j.duration)} · {j.width}×{j.height}{j.tinfo ? ` · ${j.language} · ${j.tinfo}` : ''}
          </div>
          <div className="mt-2 flex gap-1">
            {STEPS.map((s, i) => (
              <span key={s} className={cn('flex-1 rounded-md py-0.5 text-center text-[11px]', i < si || j.status === 'done' ? 'bg-success/15 text-success' : i === si ? 'bg-primary/20 font-semibold text-primary' : 'bg-muted text-muted-foreground')}>
                {i < si || j.status === 'done' ? '✓ ' : ''}{i === si && busy ? <Loader2 className="mr-1 inline h-3 w-3 animate-spin" /> : null}{s}
              </span>
            ))}
          </div>
          {busy && (
            <div className="mt-2">
              <div className="text-xs"><b className="text-primary">{j.stage || j.status}</b> {j.status !== 'queued' ? pct + '%' : ''}{j.started ? ` · ${fmtE(now - j.started)} elapsed` : ''}</div>
              <Progress value={j.status === 'queued' ? 3 : pct} className="mt-1" />
            </div>
          )}
          {j.status === 'error' && <div className="mt-2 flex items-center gap-1 text-xs text-destructive"><AlertTriangle className="h-3.5 w-3.5" />{j.message}</div>}
          {!busy && j.proxy === 'making' && <div className="mt-1 text-[11px] text-muted-foreground">Preparing preview copy…</div>}
          {j.outputs?.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {j.outputs.map((o) => (
                <span key={o.file} className="inline-flex items-center gap-1 rounded-full bg-success/10 px-2 py-0.5 text-[11px] text-success">
                  <a href={`/outputs/${encodeURIComponent(o.file)}`} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 hover:underline"><Play className="h-3 w-3" />{o.file}</a>
                  <a href={`/outputs/${encodeURIComponent(o.file)}?dl=1`} title="Download"><Download className="h-3 w-3" /></a>
                </span>
              ))}
            </div>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          {!j.has_transcript
            ? <Button size="sm" onClick={onGen} disabled={busy}><Wand2 className="h-4 w-4" />Generate captions</Button>
            : <>
                <Button size="sm" onClick={() => (location.hash = `#/edit/${j.id}`)} disabled={busy}><Pencil className="h-4 w-4" />Open editor</Button>
                <Button size="sm" variant="outline" onClick={onGen} disabled={busy} title="Transcribe again with the settings on the right">Redo</Button>
              </>}
          <Button size="icon" variant="ghost" onClick={onDel} disabled={busy} title="Remove from list"><Trash2 className="h-4 w-4" /></Button>
        </div>
      </div>
    </div>
  )
}

function LogBox({ log }) {
  const ref = React.useRef()
  const stick = React.useRef(true)
  React.useEffect(() => { const el = ref.current; if (el && stick.current) el.scrollTop = el.scrollHeight }, [log])
  return (
    <div
      ref={ref}
      onScroll={(e) => { const el = e.currentTarget; stick.current = el.scrollTop + el.clientHeight >= el.scrollHeight - 30 }}
      className="max-h-56 overflow-auto whitespace-pre-wrap rounded-lg bg-black/40 p-3 font-mono text-[12px] leading-relaxed text-muted-foreground"
    >
      {log?.length ? log.map((l, i) => <div key={i} className={/ERROR|WARNING/.test(l) ? 'text-destructive' : ''}>{l}</div>) : 'Waiting…'}
    </div>
  )
}
