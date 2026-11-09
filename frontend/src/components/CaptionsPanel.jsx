import * as React from 'react'
import { ChevronDown, Eye, EyeOff } from 'lucide-react'
import { cn, fmtTP } from '@/lib/utils'

const WEAK = /^(a|an|the|to|of|in|on|at|for|and|or|but|is|are|was|if|so|as|with|that|your|my|our|ka|ki|ke|ko|se|me|mein|par|aur|ya|ek|hai|ho|toh|ye|yeh|wo|woh|jo)$/
/** same rule as the server (engine/ass.py pick_hero): user-flagged words, else the most keyword-like word */
export function autoHero(words) {
  const flagged = words.map((w, i) => (w.hero ? i : -1)).filter((i) => i >= 0)
  if (flagged.length) return { idx: flagged, auto: false }
  let best = 0, bs = [-1, -1, 0]
  words.forEach((w, i) => {
    const t = w.w.toLowerCase().replace(/[^\p{L}\p{N}_]/gu, '')
    const sc = [WEAK.test(t) ? 0 : 1, Math.min(t.length, 14), -i]
    if (sc[0] > bs[0] || (sc[0] === bs[0] && (sc[1] > bs[1] || (sc[1] === bs[1] && sc[2] > bs[2])))) { bs = sc; best = i }
  })
  return { idx: [best], auto: true }
}

/** Left panel : every caption as a card of word chips. Shift/right-click a chip = make it the big word behind you. */
export default function CaptionsPanel({ segments, t, sel, setSel, seek, behindStyle, ops, lines, setLines }) {
  const [editing, setEditing] = React.useState(null)
  const refs = React.useRef({})
  const activeSeg = segments.findIndex((s) => t >= s.words[0].s && t < s.words[s.words.length - 1].e + 0.05)
  React.useEffect(() => { const el = refs.current[activeSeg]; if (el) el.scrollIntoView({ block: 'nearest' }) }, [activeSeg])
  const commit = () => { if (editing) { ops.rename(editing.si, editing.wi, editing.text); setEditing(null) } }
  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="space-y-3 border-b p-3">
        <div className="text-sm font-semibold">Captions</div>
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold tracking-wider text-muted-foreground">LINES</span>
          <div className="flex rounded-lg bg-muted p-0.5 text-xs">
            {[[1, '1 Line'], [2, '2 Lines']].map(([n, l]) => (
              <button key={n} onClick={() => setLines(n)} className={cn('cursor-pointer rounded-md px-3 py-1 font-medium', lines === n ? 'bg-primary text-primary-foreground' : 'text-muted-foreground')}>{l}</button>
            ))}
          </div>
        </div>
        {behindStyle && <p className="text-[11px] leading-snug text-muted-foreground"><b className="text-success">Green</b> word = shown BIG behind the person. <b>Shift+click</b> (or right-click) a word to choose it. Click “Behind” on a card to switch that caption on/off.</p>}
      </div>
      <div className="min-h-0 flex-1 space-y-2 overflow-auto p-3">
        {segments.map((s, si) => {
          const behind = behindStyle && s.behind !== false
          const hero = behind ? autoHero(s.words) : { idx: [], auto: true }
          return (
            <div key={si} ref={(el) => (refs.current[si] = el)} className={cn('rounded-xl border bg-card/60 p-2.5', si === activeSeg && 'border-primary/70 bg-primary/5')}>
              <div className="mb-2 flex items-center gap-2 text-[11px] text-muted-foreground">
                <span className="font-semibold text-foreground">{si + 1}</span>
                {behindStyle && (
                  <button onClick={() => ops.toggleBehind(si)} title="Hero word behind the person for this caption"
                    className={cn('flex cursor-pointer items-center gap-1 rounded-md px-1.5 py-0.5 font-semibold', behind ? 'bg-success/15 text-success' : 'bg-muted text-muted-foreground')}>
                    {behind ? <Eye className="h-3 w-3" /> : <EyeOff className="h-3 w-3" />}{behind ? 'Behind' : 'Front'}
                  </button>
                )}
                <button onClick={() => seek(s.words[0].s + 0.001)} className="ml-auto cursor-pointer tabular-nums hover:text-foreground">{fmtTP(s.words[0].s)} → {fmtTP(s.words[s.words.length - 1].e)}</button>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {s.words.map((w, wi) => {
                  const isHero = hero.idx.includes(wi)
                  const isSel = sel && sel.si === si && sel.wi === wi
                  const active = t >= w.s && t < w.e
                  if (editing && editing.si === si && editing.wi === wi) {
                    return <input key={wi} autoFocus value={editing.text} onChange={(e) => setEditing({ ...editing, text: e.target.value })} onBlur={commit}
                      onKeyDown={(e) => { if (e.key === 'Enter') commit(); if (e.key === 'Escape') setEditing(null); e.stopPropagation() }}
                      className="h-7 rounded-md bg-background px-2 text-sm outline-none ring-2 ring-primary" style={{ width: Math.max(48, editing.text.length * 9 + 20) }} />
                  }
                  return (
                    <button key={wi}
                      onClick={(e) => { if (e.shiftKey && behind) ops.toggleHero(si, wi); else { setSel({ si, wi }); seek(w.s + 0.001) } }}
                      onContextMenu={(e) => { e.preventDefault(); if (behind) ops.toggleHero(si, wi) }}
                      onDoubleClick={() => setEditing({ si, wi, text: w.w })}
                      className={cn('cursor-pointer rounded-md border px-2 py-1 text-sm transition-colors',
                        isHero ? 'border-success/50 bg-success/15 text-success' : 'border-transparent bg-muted hover:bg-accent',
                        active && 'bg-foreground text-background', isSel && 'ring-2 ring-primary')}
                    >{w.w}</button>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
