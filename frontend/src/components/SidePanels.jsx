import * as React from 'react'
import { Download, Loader2, Play, Rocket } from 'lucide-react'
import { Button, Label, Progress, Select, Switch } from '@/components/ui'
import { StyleCard } from './StylePanel'
import { cn, fmtT } from '@/lib/utils'
import { send } from '@/lib/api'

export function TextPanel({ segments, onSeek, onEdit, t }) {
  return (
    <div className="space-y-2 pb-6">
      <p className="text-[11px] text-muted-foreground">One line per spoken sentence. Fix words freely — timing of unchanged words is kept and new words are spread over the gap. For exact word timing use the timeline below.</p>
      {segments.map((s, i) => {
        const active = t >= s.words[0].s && t < s.words[s.words.length - 1].e
        return (
          <div key={i} className={cn('flex gap-2 rounded-lg border p-2', active && 'border-primary/60 bg-primary/5')}>
            <button onClick={() => onSeek(s.words[0].s + 0.01)} className="h-7 shrink-0 cursor-pointer rounded-md bg-muted px-1.5 text-[11px] tabular-nums text-muted-foreground hover:text-foreground">{fmtT(s.words[0].s)} ▶</button>
            <textarea
              defaultValue={s.words.map((w) => w.w).join(' ')} key={s.words.map((w) => w.w).join(' ') + i} rows={2}
              onBlur={(e) => { const v = e.target.value.trim(); if (v !== s.words.map((w) => w.w).join(' ')) onEdit(i, v) }}
              className="w-full resize-y rounded-md bg-muted px-2 py-1.5 text-sm outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
        )
      })}
    </div>
  )
}

export function ExportPanel({ job, styles, design, setDesign }) {
  const [picked, setPicked] = React.useState(() => new Set([design.style]))
  const [allTweaks, setAllTweaks] = React.useState(false)
  const [busyReq, setBusyReq] = React.useState(false)
  const busy = ['queued', 'transcribing', 'rendering'].includes(job.status)
  const toggle = (id) => setPicked((p) => { const n = new Set(p); n.has(id) ? n.delete(id) : n.add(id); return n })

  const go = async () => {
    setBusyReq(true)
    const place = { x: design.ov.x, y: design.ov.y, safe: design.ov.safe, words: design.ov.words, max_chars: design.ov.max_chars }
    Object.keys(place).forEach((k) => place[k] === undefined && delete place[k])
    const by = {}
    for (const id of picked) by[id] = allTweaks || id === design.style ? design.ov : place
    await send(`/api/jobs/${job.id}/run`, 'POST', { kind: 'render', styles: [...picked], overrides: design.ov, by_style: by, fit: design.fit || 'auto', offset: design.offset || 0, quality: design.quality || '1080p', fps: design.fps || 'source' }).catch(() => {})
    setBusyReq(false)
  }
  const pct = Math.round((job.progress || 0) * 100)
  return (
    <div className="space-y-3 pb-6">
      <div className="rounded-xl border bg-card/60 p-3">
        <div className="mb-1 text-sm font-semibold">Export videos</div>
        <p className="text-xs text-muted-foreground">Tick as many styles as you like — each becomes its own MP4 (1080p, or 2K 1440×2560 and 60 fps from the bar at the top) with the original audio. No limits, no watermark.</p>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {styles.map((s) => (
          <div key={s.id} className="space-y-1">
            <StyleCard s={s} compact ov={s.id === design.style || allTweaks ? design.ov : {}} selected={picked.has(s.id)} onPick={() => toggle(s.id)} />
            <div className="px-1 text-[11px] font-medium">{s.label}</div>
          </div>
        ))}
      </div>
      <div className="flex items-center justify-between rounded-lg border p-2.5 text-xs">
        <span className="pr-3">Use my size/colour tweaks for every ticked style<br /><span className="text-muted-foreground">Placement and words-on-screen always apply.</span></span>
        <Switch checked={allTweaks} onCheckedChange={setAllTweaks} />
      </div>
      <div className="flex gap-2">
        <Button variant="secondary" size="sm" onClick={() => setPicked(new Set(styles.map((s) => s.id)))}>All styles</Button>
        <Button variant="secondary" size="sm" onClick={() => setPicked(new Set([design.style]))}>Only current</Button>
      </div>
      <Button className="h-11 w-full text-base" onClick={go} disabled={!picked.size || busy || busyReq}>
        {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Rocket className="h-4 w-4" />}
        {busy ? 'Rendering…' : `Export ${picked.size} video${picked.size === 1 ? '' : 's'}`}
      </Button>
      {busy && (
        <div className="rounded-lg border p-3">
          <div className="mb-1 text-xs"><b className="text-primary">{job.stage}</b> · {pct}%</div>
          <Progress value={pct} />
        </div>
      )}
      {job.status === 'error' && <div className="text-xs text-destructive">{job.message}</div>}
      {job.outputs?.length > 0 && (
        <div className="space-y-1.5">
          <Label>Finished files</Label>
          {job.outputs.map((o) => (
            <div key={o.file} className="flex items-center gap-2 rounded-lg border bg-success/5 px-2.5 py-1.5 text-xs">
              <span className="min-w-0 flex-1 truncate" title={o.file}>{o.file}</span>
              <a className="text-success hover:underline" href={`/outputs/${encodeURIComponent(o.file)}`} target="_blank" rel="noreferrer"><Play className="inline h-3.5 w-3.5" /> Play</a>
              <a className="text-success hover:underline" href={`/outputs/${encodeURIComponent(o.file)}?dl=1`}><Download className="inline h-3.5 w-3.5" /></a>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

