import * as React from 'react'
import { Trash2, Plus, Undo2, Redo2, ZoomIn, ZoomOut, Scissors, ChevronsLeft, ChevronsRight, Magnet } from 'lucide-react'
import { Button, Slider } from '@/components/ui'
import { cn } from '@/lib/utils'

const MIN = 0.06

/** Word timeline like videocaptions.ai: waveform, one block per word, drag block edges to retime,
 *  double-click to rename, Delete removes, click ruler to scrub. */
export default function Timeline({ segments, duration, t, playing, peaks, onSeek, begin, update, undo, redo, canUndo, canRedo, sel, setSel, pps, setPps, snap, setSnap, actions, styleBehind }) {
  const [editing, setEditing] = React.useState(null)   // {si, wi, text}
  const scroller = React.useRef()
  const playheadRef = React.useRef(t)
  playheadRef.current = t
  const canvas = React.useRef()
  const width = Math.max(600, duration * pps + 120)

  const words = React.useMemo(() => segments.flatMap((s, si) => s.words.map((w, wi) => ({ ...w, si, wi }))), [segments])
  const activeKey = React.useMemo(() => { const a = words.find((w) => t >= w.s && t < w.e); return a ? a.si + ':' + a.wi : null }, [words, t])

  // waveform
  React.useEffect(() => {
    const c = canvas.current; if (!c || !peaks?.length) return
    const dpr = window.devicePixelRatio || 1, h = 44
    c.width = width * dpr; c.height = h * dpr; c.style.width = width + 'px'; c.style.height = h + 'px'
    const g = c.getContext('2d'); g.scale(dpr, dpr); g.clearRect(0, 0, width, h)
    g.fillStyle = 'rgba(255,255,255,0.22)'
    const per = 20, bw = Math.max(1, pps / per - 0.5)
    for (let i = 0; i < peaks.length; i++) { const v = peaks[i] / 100 * (h - 4); g.fillRect(i * pps / per, (h - v) / 2, bw, Math.max(1, v)) }
  }, [peaks, pps, width])

  // follow the playhead while playing
  React.useEffect(() => {
    const el = scroller.current; if (!el || !playing) return
    const x = t * pps
    if (x > el.scrollLeft + el.clientWidth * 0.85 || x < el.scrollLeft) el.scrollLeft = Math.max(0, x - el.clientWidth * 0.2)
  }, [t, playing, pps])

  // Ctrl+wheel zooms, plain wheel scrolls the timeline sideways (like CapCut)
  React.useEffect(() => {
    const el = scroller.current; if (!el) return
    const w = (e) => {
      e.preventDefault()
      if (e.ctrlKey || e.metaKey) setPps((p) => Math.max(30, Math.min(400, Math.round(p * (e.deltaY < 0 ? 1.15 : 1 / 1.15)))))
      else el.scrollLeft += Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY
    }
    el.addEventListener('wheel', w, { passive: false }); return () => el.removeEventListener('wheel', w)
  }, [setPps])

  const seekFromEvent = (e) => {
    const r = scroller.current.getBoundingClientRect()
    onSeek(Math.max(0, Math.min(duration, (e.clientX - r.left + scroller.current.scrollLeft) / pps)))
  }
  const scrub = (e) => {
    e.currentTarget.setPointerCapture(e.pointerId); seekFromEvent(e)
    const mv = (ev) => seekFromEvent(ev), up = () => { window.removeEventListener('pointermove', mv); window.removeEventListener('pointerup', up) }
    window.addEventListener('pointermove', mv); window.addEventListener('pointerup', up)
  }

  // drag a word's edge; neighbours that touch move with it so no gap/overlap appears
  const dragEdge = (e, si, wi, edge) => {
    e.stopPropagation(); e.preventDefault()
    begin()
    const startX = e.clientX
    const flat = words.findIndex((w) => w.si === si && w.wi === wi)
    const w0 = words[flat], prev = words[flat - 1], next = words[flat + 1]
    const mv = (ev) => {
      const dt = (ev.clientX - startX) / pps
      const thr = 8 / pps
      const snapTo = (v) => { if (!snap) return v; const c = [playheadRef.current, ...words.flatMap((x) => [x.s, x.e])].filter((x) => Math.abs(x - v) < thr && x !== w0.s && x !== w0.e); return c.length ? c.sort((p, q) => Math.abs(p - v) - Math.abs(q - v))[0] : v }
      update((segs) => {
        const out = segs.map((s) => ({ ...s, words: s.words.map((w) => ({ ...w })) }))
        const W = out[si].words[wi]
        if (edge === 'r') {
          let ne = Math.max(W.s + MIN, snapTo(w0.e + dt))
          if (next) ne = Math.min(ne, next.e - MIN)
          W.e = ne
          if (next && Math.abs(next.s - w0.e) < 0.03) out[next.si].words[next.wi].s = ne
        } else {
          let ns = Math.min(W.e - MIN, snapTo(w0.s + dt))
          if (prev) ns = Math.max(ns, prev.s + MIN)
          ns = Math.max(0, ns)
          W.s = ns
          if (prev && Math.abs(prev.e - w0.s) < 0.03) out[prev.si].words[prev.wi].e = ns
        }
        return out
      }, false)
    }
    const up = () => { window.removeEventListener('pointermove', mv); window.removeEventListener('pointerup', up); update(null, true) }
    window.addEventListener('pointermove', mv); window.addEventListener('pointerup', up)
  }

  const commitText = () => {
    if (!editing) return
    const txt = editing.text.trim()
    begin()
    if (!txt) { update((segs) => segs.map((s, si) => (si === editing.si ? { ...s, words: s.words.filter((_, wi) => wi !== editing.wi) } : s)).filter((s) => s.words.length), true) }
    else update((segs) => segs.map((s, si) => (si === editing.si ? { ...s, words: s.words.map((w, wi) => (wi === editing.wi ? { ...w, w: txt } : w)) } : s)), true)
    setEditing(null)
  }

  const ticks = []
  const step = pps >= 160 ? 0.5 : pps >= 60 ? 1 : 5
  for (let x = 0; x <= duration + step; x += step) ticks.push(x)

  return (
    <div className="flex flex-col border-t bg-card/60">
      <div className="flex items-center gap-1 border-b px-2 py-1">
        <Button size="xs" variant="ghost" onClick={undo} disabled={!canUndo} title="Undo (Ctrl+Z)"><Undo2 className="h-3.5 w-3.5" /></Button>
        <Button size="xs" variant="ghost" onClick={redo} disabled={!canRedo} title="Redo (Ctrl+Y)"><Redo2 className="h-3.5 w-3.5" /></Button>
        <div className="mx-1 h-4 w-px bg-border" />
        <Button size="xs" variant="ghost" onClick={actions.trimLeft} title="Trim left edge to playhead (Q)"><ChevronsLeft className="h-3.5 w-3.5" />Trim left <kbd className="ml-1 rounded bg-muted px-1 text-[10px]">Q</kbd></Button>
        <Button size="xs" variant="ghost" onClick={actions.trimRight} title="Trim right edge to playhead (E or W)"><ChevronsRight className="h-3.5 w-3.5" />Trim right <kbd className="ml-1 rounded bg-muted px-1 text-[10px]">E</kbd></Button>
        <Button size="xs" variant="ghost" onClick={actions.split} title="Start a new caption line at the playhead (Ctrl+B)"><Scissors className="h-3.5 w-3.5" />Split <kbd className="ml-1 rounded bg-muted px-1 text-[10px]">Ctrl B</kbd></Button>
        <Button size="xs" variant="ghost" onClick={actions.add}><Plus className="h-3.5 w-3.5" />Add word</Button>
        <Button size="xs" variant="ghost" onClick={actions.del} disabled={!sel} title="Delete (Del)"><Trash2 className="h-3.5 w-3.5" />Delete</Button>
        <Button size="xs" variant={snap ? 'secondary' : 'ghost'} onClick={() => setSnap(!snap)} title="Snapping (N)"><Magnet className="h-3.5 w-3.5" />Snap</Button>        <div className="flex-1" />
        <ZoomOut className="h-3.5 w-3.5 text-muted-foreground" />
        <Slider className="w-28" min={30} max={400} step={5} value={[pps]} onValueChange={(v) => setPps(v[0])} />
        <ZoomIn className="h-3.5 w-3.5 text-muted-foreground" />
      </div>
      <div ref={scroller} className="relative overflow-x-auto overflow-y-hidden" style={{ height: 176 }}>
        <div className="relative" style={{ width, height: 136 }}>
          {/* ruler */}
          <div className="absolute inset-x-0 top-0 h-6 cursor-ew-resize border-b bg-background/60" onPointerDown={scrub}>
            {ticks.map((x) => (
              <div key={x} className="absolute top-0 h-full border-l border-border pl-1 text-[10px] text-muted-foreground" style={{ left: x * pps }}>{Number.isInteger(x) ? x + 's' : ''}</div>
            ))}
          </div>
          <canvas ref={canvas} className="absolute left-0 top-[84px]" onPointerDown={scrub} />
          {/* Person cut-out track (green) + caption lines track (tan), like other caption editors */}
          {styleBehind && segments.map((s, si) => (s.behind === false ? null : (
            <div key={'b' + si} onClick={() => actions.toggleBehind(si)} title="Person cut-out active for this caption — click to switch off"
              className="absolute top-[28px] h-[20px] cursor-pointer truncate rounded border border-emerald-400/40 bg-emerald-700/70 px-1.5 text-[10px] font-medium leading-[18px] text-white hover:bg-emerald-600"
              style={{ left: s.words[0].s * pps, width: Math.max(8, (s.words[s.words.length - 1].e - s.words[0].s) * pps - 2) }}>Person cutout</div>
          )))}
          {segments.map((s, si) => (
            <div key={'l' + si} onClick={() => { setSel({ si, wi: 0 }); onSeek(s.words[0].s + 0.001) }} title={s.words.map((w) => w.w).join(' ')}
              className="absolute top-[52px] h-[26px] cursor-pointer truncate rounded-md bg-amber-200/85 px-2 text-[11px] font-medium leading-[26px] text-amber-950 hover:bg-amber-200"
              style={{ left: s.words[0].s * pps, width: Math.max(8, (s.words[s.words.length - 1].e - s.words[0].s) * pps - 2) }}>
              {s.words.map((w) => w.w).join(' ')}
            </div>
          ))}          {/* word lane */}
          <div className="absolute inset-x-0 top-[84px] h-[44px]" onPointerDown={(e) => { if (e.target === e.currentTarget) { setSel(null); scrub(e) } }}>
            {words.map((w) => {
              const key = w.si + ':' + w.wi
              const isSel = sel && sel.si === w.si && sel.wi === w.wi
              const isEd = editing && editing.si === w.si && editing.wi === w.wi
              const wpx = Math.max(10, (w.e - w.s) * pps - 2)
              return (
                <div
                  key={key}
                  onPointerDown={(e) => { e.stopPropagation(); setSel({ si: w.si, wi: w.wi }); onSeek(w.s + 0.001) }}
                  onDoubleClick={() => setEditing({ si: w.si, wi: w.wi, text: w.w })}
                  className={cn(
                    'group absolute top-0 flex h-full cursor-pointer items-center justify-center overflow-hidden rounded-md border text-xs font-medium transition-colors',
                    activeKey === key ? 'border-white bg-white text-black' : isSel ? 'border-primary bg-primary/70 text-white' : 'border-blue-400/30 bg-blue-500/70 text-white hover:bg-blue-500',
                  )}
                  style={{ left: w.s * pps, width: wpx }}
                  title={`${w.w}  (${w.s.toFixed(2)}s – ${w.e.toFixed(2)}s)`}
                >
                  {isEd ? (
                    <input
                      autoFocus value={editing.text} onChange={(e) => setEditing({ ...editing, text: e.target.value })}
                      onBlur={commitText} onKeyDown={(e) => { if (e.key === 'Enter') commitText(); if (e.key === 'Escape') setEditing(null); e.stopPropagation() }}
                      className="h-full w-full bg-black/70 px-1 text-center text-xs text-white outline-none" style={{ minWidth: 60 }}
                    />
                  ) : <span className="truncate px-1">{w.w}</span>}
                  <div onPointerDown={(e) => dragEdge(e, w.si, w.wi, 'l')} className="absolute left-0 top-0 h-full w-1.5 cursor-ew-resize bg-white/0 hover:bg-white/60" />
                  <div onPointerDown={(e) => dragEdge(e, w.si, w.wi, 'r')} className="absolute right-0 top-0 h-full w-1.5 cursor-ew-resize bg-white/0 hover:bg-white/60" />
                </div>
              )
            })}
          </div>
          {/* playhead */}
          <div className="pointer-events-none absolute top-0 z-10 h-full w-px bg-white" style={{ left: t * pps }}>
            <div className="absolute -left-[5px] top-0 h-0 w-0 border-x-[5px] border-t-[8px] border-x-transparent border-t-white" />
          </div>
        </div>
      </div>
    </div>
  )
}



