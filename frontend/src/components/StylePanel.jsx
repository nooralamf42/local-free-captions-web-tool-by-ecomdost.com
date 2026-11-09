import * as React from 'react'
import { Check, Save, Search, Trash2 } from 'lucide-react'
import { Badge, Button } from '@/components/ui'
import { cn } from '@/lib/utils'
import { qs } from '@/lib/api'
import { ls } from '@/store'

export const family = (s) => (s.behind ? 'Behind you' : s.mode === 'highlight' || s.mode === 'sweep' ? 'Highlight' : s.mode === 'flash' ? 'Flash' : s.words === 1 ? 'Pop' : 'Reveal')
export const previewOv = (ov) => { const { x, y, safe, offset, hero_x, hero_y, behind, ...rest } = ov || {}; return rest }
const POPULAR = ['classic-key', 'hormozi', 'mrbeast', 'ali', 'karaoke', 'headliner', 'beacon', 'driftwood', 'bubble', 'highlighted']

/** Template card: static poster; on hover the real animation (pre-rendered by our own pipeline) plays — same trick as other editors */
export function StyleCard({ s, ov, selected, onPick, compact, small }) {
  const [hover, setHover] = React.useState(false)
  const [playing, setPlaying] = React.useState(false)
  const q = `style=${s.id}&ov=${qs(previewOv(ov))}`
  return (
    <button
      onClick={onPick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => { setHover(false); setPlaying(false) }}
      className={cn('group relative block w-full cursor-pointer overflow-hidden rounded-xl border bg-[#0b0b10] text-left transition-shadow',
        selected ? 'ring-2 ring-primary' : 'hover:ring-1 hover:ring-white/30')}
    >
      <div className="relative aspect-[9/16] w-full">
        <img src={`/api/style-poster.png?${q}`} loading="lazy" alt={s.label} className="absolute inset-0 h-full w-full object-cover" />
        {hover && (
          <video src={`/api/style-clip.mp4?${q}`} autoPlay loop muted playsInline preload="none" onPlaying={() => setPlaying(true)}
            className={cn('absolute inset-0 h-full w-full object-cover transition-opacity duration-150', playing ? 'opacity-100' : 'opacity-0')} />
        )}
        {!small && (
          <div className="absolute right-1.5 top-1.5 flex gap-1">
            {(s.groups || []).includes('Popular') && <Badge className="bg-orange-500/90 text-white">Popular</Badge>}
            {s.behind && <Badge tone="new">Behind you</Badge>}
          </div>
        )}
        {selected && <div className="absolute left-1.5 top-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-primary"><Check className="h-3.5 w-3.5 text-white" /></div>}
      </div>
      {!compact && <div className="border-t border-white/5 px-2.5 py-1.5 text-xs font-semibold">{s.label}</div>}
    </button>
  )
}

const GROUPS = ['Popular', 'Behind you', 'Bold & animated', 'Clean', 'Property reels', 'Around you']
const FILTERS = ['All', ...GROUPS, 'More looks']
const inFilter = (s, f) => (f === 'All' ? (s.groups || []).length > 0 : f === 'More looks' ? !(s.groups || []).length : (s.groups || []).includes(f))

export default function TemplatesPanel({ styles, design, setStyle, setDesign }) {
  const [q, setQ] = React.useState('')
  const [f, setF] = React.useState('All')
  const [tab, setTab] = React.useState('templates')
  const [presets, setPresets] = React.useState(() => ls.get('presets', []))
  const savePresets = (p) => { setPresets(p); ls.set('presets', p) }
  const list = styles.filter((s) => inFilter(s, f) && (s.label + ' ' + s.desc).toLowerCase().includes(q.toLowerCase()))
  const counts = (x) => styles.filter((s) => inFilter(s, x)).length
  const savePreset = () => {
    const name = window.prompt('Name this preset (your current template + all tweaks):', (styles.find((s) => s.id === design.style)?.label || 'My preset'))
    if (name) savePresets([...presets, { name, style: design.style, ov: design.ov, offset: design.offset || 0 }])
  }
  return (
    <div className="flex h-full min-h-0 flex-col gap-3">
      <div className="flex gap-1 rounded-lg bg-muted p-1 text-xs">
        {[['templates', 'Templates'], ['presets', `My presets (${presets.length})`]].map(([k, n]) => (
          <button key={k} onClick={() => setTab(k)} className={cn('flex-1 cursor-pointer rounded-md py-1.5 font-medium', tab === k ? 'bg-card text-foreground shadow' : 'text-muted-foreground')}>{n}</button>
        ))}
      </div>
      {tab === 'templates' ? (
        <>
          <div className="flex items-center gap-2">
            <div className="flex flex-1 items-center gap-2 rounded-lg border bg-muted px-3">
              <Search className="h-4 w-4 text-muted-foreground" />
              <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Find a template…" className="h-9 flex-1 bg-transparent text-sm outline-none" />
            </div>
            <Button size="sm" variant="secondary" onClick={savePreset} title="Save the current template + tweaks as a preset"><Save className="h-4 w-4" />Save preset</Button>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {FILTERS.map((x) => (
              <button key={x} onClick={() => setF(x)} className={cn('cursor-pointer rounded-full border px-2.5 py-1 text-[11px] transition-colors', f === x ? 'border-primary bg-primary/15 text-primary' : 'text-muted-foreground hover:text-foreground')}>
                {x} <span className="opacity-60">{counts(x)}</span>
              </button>
            ))}
          </div>
          <div className="grid min-h-0 flex-1 auto-rows-max grid-cols-2 content-start gap-2.5 overflow-auto pb-4 pr-1">
            {list.map((s) => <StyleCard key={s.id} s={s} ov={design.ov} selected={design.style === s.id} onPick={() => setStyle(s.id)} />)}
            {!list.length && <div className="col-span-2 text-sm text-muted-foreground">No templates match.</div>}
          </div>
        </>
      ) : (
        <div className="min-h-0 flex-1 space-y-2 overflow-auto pb-4">
          {!presets.length && <p className="text-sm text-muted-foreground">No presets yet. Pick a template, tweak it in Customize, then press “Save preset”.</p>}
          {presets.map((p, i) => {
            const s = styles.find((x) => x.id === p.style)
            return (
              <div key={i} className="flex items-center gap-3 rounded-xl border p-2">
                <div className="w-28 shrink-0">{s && <StyleCard s={s} ov={p.ov} compact small selected={false} onPick={() => setDesign((d) => ({ ...d, style: p.style, ov: p.ov, offset: p.offset || 0 }))} />}</div>
                <div className="min-w-0 flex-1"><div className="truncate text-sm font-semibold">{p.name}</div><div className="text-xs text-muted-foreground">{s?.label}</div></div>
                <Button size="sm" onClick={() => setDesign((d) => ({ ...d, style: p.style, ov: p.ov, offset: p.offset || 0 }))}>Apply</Button>
                <Button size="icon" variant="ghost" onClick={() => savePresets(presets.filter((_, j) => j !== i))}><Trash2 className="h-4 w-4" /></Button>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
