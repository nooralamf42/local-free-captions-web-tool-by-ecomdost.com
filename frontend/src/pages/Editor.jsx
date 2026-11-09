import * as React from 'react'
import { ArrowLeft, Loader2, Paintbrush, SlidersHorizontal, Rocket, AlertTriangle, Download } from 'lucide-react'
import { Button, Dialog, DialogContent, Select, Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui'
import CaptionsPanel from '@/components/CaptionsPanel'
import LayoutBoxes from '@/components/LayoutBoxes'
import PreviewPlayer from '@/components/PreviewPlayer'
import Timeline from '@/components/Timeline'
import StylePanel from '@/components/StylePanel'
import CustomizePanel from '@/components/CustomizePanel'
import { ExportPanel } from '@/components/SidePanels'
import { useStore } from '@/store'
import { api, getJSON, qs, send } from '@/lib/api'

const SHORTCUTS = [['Space','Play / pause'],['K / L','Pause / play'],['J','Back 2 seconds'],['← / →','Previous / next frame'],['Shift + ← / →','5 frames'],['↑ / ↓','Previous / next word'],['Home / End','Start / end'],['Q','Trim LEFT of playhead (selected or current word)'],['E  or  W','Trim RIGHT of playhead'],['Ctrl + B','Split caption line at playhead'],['Delete','Delete selected word'],['[  /  ]','Select previous / next word'],['Ctrl + Z','Undo'],['Ctrl + Shift + Z  or  Ctrl + Y','Redo'],['Ctrl + + / Ctrl + −','Zoom timeline'],['Ctrl + 0  or  Shift + Z','Fit timeline'],['Ctrl + scroll','Zoom timeline with the wheel'],['Scroll','Scroll timeline sideways'],['N','Toggle snapping'],['Double-click word','Edit its text'],['Drag word edge','Retime (snaps to neighbours / playhead)'],['?','This list']]

export default function Editor({ id }) {
  const { state, styles, fonts, design, setDesign } = useStore()
  const job = state.jobs.find((j) => j.id === id)
  const videoRef = React.useRef(null)
  const [t, setT] = React.useState(0)
  const [segments, setSegmentsState] = React.useState(null)
  const segRef = React.useRef(null)
  const hist = React.useRef({ past: [], future: [] })
  const [, force] = React.useReducer((x) => x + 1, 0)
  const [saved, setSaved] = React.useState(0)
  const [assPair, setAssPair] = React.useState({ front: '', behind: null })
  const [lines, setLinesState] = React.useState(1)
  const [peaks, setPeaks] = React.useState([])
  const [safeGuide, setSafeGuide] = React.useState(false)
  const [tab, setTab] = React.useState('style')
  const [exporting, setExporting] = React.useState(false)
  // The header's Export renders the template that is showing, now, and the Export tab shows its progress and the finished file.
  const exportNow = async () => {
    setExporting(true)
    setTab('export')
    try {
      await send(`/api/jobs/${id}/run`, 'POST', { kind: 'render', styles: [design.style], overrides: design.ov, by_style: { [design.style]: design.ov }, fit: design.fit || 'auto', offset: design.offset || 0, quality: design.quality || '1080p', fps: design.fps || 'source' })
    } catch (e) { /* the panel shows the job's own error */ }
    setExporting(false)
  }
  const saveTimer = React.useRef()
  const [sel, setSel] = React.useState(null)       // selected word {si, wi}
  const [pps, setPps] = React.useState(110)        // timeline zoom (px per second)
  const [snap, setSnap] = React.useState(true)
  const [playing, setPlaying] = React.useState(false)
  const [keys, setKeys] = React.useState(false)
  const [toast, setToast] = React.useState('')
  const toastTimer = React.useRef()

  const setSegs = (v) => { segRef.current = v; setSegmentsState(v) }

  // ---- load transcript + waveform
  React.useEffect(() => {
    getJSON(`/api/jobs/${id}/transcript`).then((tr) => setSegs((tr.segments || []).map((s) => ({ words: s.words, ...(s.behind === false ? { behind: false } : {}) })))).catch(() => setSegs([]))
    getJSON(`/api/jobs/${id}/peaks`).then(setPeaks).catch(() => {})
  }, [id])

  // ---- make sure a preview copy exists
  React.useEffect(() => {
    if (job && (!job.proxy || job.proxy === 'error')) send(`/api/jobs/${id}/proxy`, 'POST', { fit: design.fit || 'auto' }).catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [job?.id, job?.proxy])
  const lastFit = React.useRef(design.fit || 'auto')
  React.useEffect(() => {
    const f = design.fit || 'auto'
    if (f !== lastFit.current) { lastFit.current = f; send(`/api/jobs/${id}/proxy`, 'POST', { fit: f }).catch(() => {}) }
  }, [design.fit, id])

  // ---- edit helpers (history + debounced save)
  const scheduleSave = () => {
    clearTimeout(saveTimer.current)
    saveTimer.current = setTimeout(async () => {
      try { await send(`/api/jobs/${id}/segments`, 'PUT', { segments: segRef.current }); setSaved((n) => n + 1) } catch { /* shown by missing refresh */ }
    }, 350)
  }
  const begin = () => { hist.current.past.push(JSON.parse(JSON.stringify(segRef.current))); hist.current.future = []; force() }
  const update = (fn, save) => { if (fn) setSegs(fn(segRef.current)); if (save) scheduleSave() }
  const undo = () => { const p = hist.current.past.pop(); if (!p) return; hist.current.future.push(segRef.current); setSegs(p); scheduleSave(); force() }
  const redo = () => { const n = hist.current.future.pop(); if (!n) return; hist.current.past.push(segRef.current); setSegs(n); scheduleSave(); force() }
  const editLine = async (i, text) => {
    const texts = segRef.current.map(() => null); texts[i] = text
    begin()
    await send(`/api/jobs/${id}/transcript`, 'PUT', { texts })
    const tr = await getJSON(`/api/jobs/${id}/transcript`)
    setSegs((tr.segments || []).map((s) => ({ words: s.words, ...(s.behind === false ? { behind: false } : {}) }))); setSaved((n) => n + 1)
  }

  // ---- live ASS from the server (identical to what the export burns in)
  const ovKey = JSON.stringify([design.style, design.ov, design.offset || 0])
  React.useEffect(() => {
    if (!segments) return
    const h = setTimeout(async () => {
      try {
        const r = await (await api(`/api/jobs/${id}/ass?style=${design.style}&ov=${qs(design.ov)}&offset=${design.offset || 0}&split=1`)).json()
        setAssPair({ front: r.front, behind: r.is_behind ? r.behind : null })
      } catch { /* transcript not saved yet */ }
    }, 120)
    return () => clearTimeout(h)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ovKey, saved, !!segments, id])

  const seek = (s) => { const v = videoRef.current; if (v) { v.currentTime = Math.max(0, Math.min(job?.duration || s, s)); setT(v.currentTime) } }
  const toggle = () => { const v = videoRef.current; if (v) (v.paused ? v.play() : v.pause()) }

  // ---- CapCut-style editing actions ------------------------------------------------------------
  const flat = () => (segRef.current || []).flatMap((s, si) => s.words.map((w, wi) => ({ ...w, si, wi })))
  const curT = () => videoRef.current?.currentTime ?? 0
  const targetWord = () => {
    const f = flat(), now = curT()
    return (sel && f.find((w) => w.si === sel.si && w.wi === sel.wi)) || f.find((w) => now >= w.s && now < w.e)
  }
  const flash = (m) => { setToast(m); clearTimeout(toastTimer.current); toastTimer.current = setTimeout(() => setToast(''), 1600) }
  const mapWord = (si, wi, fn) => (segs) => segs.map((s, i) => (i === si ? { ...s, words: s.words.map((w, j) => (j === wi ? fn(w) : w)) } : s))
  const trimLeft = () => {            // Q: cut the part of the selected/current word that is LEFT of the playhead
    const w = targetWord(), now = curT()
    if (!w || now <= w.s + 0.03 || now >= w.e - 0.03) return flash('Put the playhead inside a word, then press Q')
    begin(); update(mapWord(w.si, w.wi, (x) => ({ ...x, s: now })), true); setSel({ si: w.si, wi: w.wi }); flash('Trimmed left')
  }
  const trimRight = () => {           // E / W: cut the part RIGHT of the playhead
    const w = targetWord(), now = curT()
    if (!w || now <= w.s + 0.03 || now >= w.e - 0.03) return flash('Put the playhead inside a word, then press E')
    begin(); update(mapWord(w.si, w.wi, (x) => ({ ...x, e: now })), true); setSel({ si: w.si, wi: w.wi }); flash('Trimmed right')
  }
  const splitLine = () => {           // Ctrl+B: start a new caption line at the playhead
    const f = flat(), now = curT()
    const w = f.find((x) => now >= x.s && now < x.e) || f.find((x) => x.s >= now)
    if (!w || w.wi === 0) return flash('Nothing to split here')
    begin()
    update((segs) => segs.flatMap((s, i) => (i === w.si ? [{ words: s.words.slice(0, w.wi) }, { words: s.words.slice(w.wi) }] : [s])), true)
    flash('Split caption line')
  }
  const delWord = () => {
    const w = targetWord(); if (!w) return
    begin()
    update((segs) => segs.map((s, i) => (i === w.si ? { ...s, words: s.words.filter((_, j) => j !== w.wi) } : s)).filter((s) => s.words.length), true)
    setSel(null); flash('Deleted word')
  }
  const addWord = () => {
    const f = flat(), now = curT()
    const at = targetWord() || f.find((x) => x.e > now) || f[f.length - 1]
    if (!at) return
    const s0 = Math.max(at.e, now >= at.e ? now : at.e), e0 = Math.min(job.duration, s0 + 0.4)
    begin()
    update((segs) => segs.map((sg, i) => (i === at.si ? { ...sg, words: [...sg.words.slice(0, at.wi + 1), { w: 'word', s: s0, e: e0 }, ...sg.words.slice(at.wi + 1)] } : sg)), true)
    setSel({ si: at.si, wi: at.wi + 1 }); flash('Added word — double-click it to type')
  }
  const jumpWord = (dir) => {         // Up/Down: previous/next word start (CapCut: previous/next cut)
    const f = flat(), now = curT()
    const nxt = dir > 0 ? f.find((w) => w.s > now + 0.02) : [...f].reverse().find((w) => w.s < now - 0.02)
    if (nxt) { seek(nxt.s + 0.001); setSel({ si: nxt.si, wi: nxt.wi }) }
  }
  const stepSel = (dir) => {          // [ / ]: select previous / next word
    const f = flat(); const i = sel ? f.findIndex((w) => w.si === sel.si && w.wi === sel.wi) : -1
    const n = f[Math.max(0, Math.min(f.length - 1, i < 0 ? 0 : i + dir))]; if (n) { setSel({ si: n.si, wi: n.wi }); seek(n.s + 0.001) }
  }
  const actions = { trimLeft, trimRight, split: splitLine, add: addWord, del: delWord }

  // Keyboard (capture phase so focused buttons / tabs don't swallow Space and arrows). Same keys as CapCut for PC.
  React.useEffect(() => {
    const FR = 1 / 30
    const k = (e) => {
      const tag = e.target?.tagName
      if (/INPUT|TEXTAREA|SELECT/.test(tag) || e.target?.isContentEditable || document.querySelector('[role=dialog]')) return
      const key = e.key, ctrl = e.ctrlKey || e.metaKey, shift = e.shiftKey
      const use = (fn) => { e.preventDefault(); e.stopPropagation(); fn() }
      if (key === ' ') use(toggle)
      else if (key.toLowerCase() === 'k' && !ctrl) use(() => videoRef.current?.pause())
      else if (key.toLowerCase() === 'l' && !ctrl) use(() => videoRef.current?.play())
      else if (key.toLowerCase() === 'j' && !ctrl) use(() => seek(curT() - 2))
      else if (key === 'ArrowLeft') use(() => seek(curT() - (shift ? 5 : 1) * FR))
      else if (key === 'ArrowRight') use(() => seek(curT() + (shift ? 5 : 1) * FR))
      else if (key === 'ArrowUp') use(() => jumpWord(-1))
      else if (key === 'ArrowDown') use(() => jumpWord(1))
      else if (key === 'Home') use(() => seek(0))
      else if (key === 'End') use(() => seek(job?.duration || 0))
      else if (ctrl && key.toLowerCase() === 'b') use(splitLine)
      else if (!ctrl && key.toLowerCase() === 'q') use(trimLeft)
      else if (!ctrl && (key.toLowerCase() === 'e' || key.toLowerCase() === 'w')) use(trimRight)
      else if (key === 'Delete' || key === 'Backspace') use(delWord)
      else if (ctrl && key.toLowerCase() === 'z') use(shift ? redo : undo)
      else if (ctrl && key.toLowerCase() === 'y') use(redo)
      else if (ctrl && (key === '=' || key === '+')) use(() => setPps((p) => Math.min(400, Math.round(p * 1.25))))
      else if (ctrl && key === '-') use(() => setPps((p) => Math.max(30, Math.round(p / 1.25))))
      else if ((ctrl && key === '0') || (shift && key.toLowerCase() === 'z')) use(() => setPps(Math.max(30, Math.min(400, ((window.innerWidth - 410) / Math.max(1, job?.duration || 1))))))
      else if (!ctrl && key.toLowerCase() === 'n') use(() => { setSnap((s) => !s) })
      else if (key === '[') use(() => stepSel(-1))
      else if (key === ']') use(() => stepSel(1))
      else if (key === '?' || (shift && key === '/')) use(() => setKeys(true))
      else if (key === 'Escape') setSel(null)
    }
    window.addEventListener('keydown', k, true)
    return () => window.removeEventListener('keydown', k, true)
  })
  const style = styles.find((s) => s.id === design.style) || styles[0]
  const setOv = (fn) => setDesign((d) => ({ ...d, ov: typeof fn === 'function' ? fn(d.ov) : fn }))
  const setStyle = (sid) => setDesign((d) => {
    const keep = {}; for (const k of ['x', 'y', 'safe', 'words', 'max_chars']) if (d.ov[k] !== undefined) keep[k] = d.ov[k]
    return { ...d, style: sid, ov: keep }
  })

  // ---- ops used by the Captions panel / timeline ------------------------------------------------------------
  const behindStyle = !!style?.behind && design.ov.behind !== false
  const ops = {
    toggleBehind: (si) => { begin(); update((segs) => segs.map((s, i) => (i === si ? (s.behind === false ? { words: s.words } : { ...s, behind: false }) : s)), true) },
    toggleHero: (si, wi) => {
      begin()
      update((segs) => segs.map((s, i) => (i === si ? { ...s, words: s.words.map((w, j) => (j === wi ? { ...w, hero: !w.hero } : w)) } : s)), true)
    },
    rename: (si, wi, text) => {
      const t2 = text.trim(); begin()
      if (!t2) update((segs) => segs.map((s, i) => (i === si ? { ...s, words: s.words.filter((_, j) => j !== wi) } : s)).filter((s) => s.words.length), true)
      else update((segs) => segs.map((s, i) => (i === si ? { ...s, words: s.words.map((w, j) => (j === wi ? { ...w, w: t2 } : w)) } : s)), true)
    },
  }
  actions.toggleBehind = ops.toggleBehind
  const setLines = (n) => {
    setLinesState(n)
    setDesign((d) => { const ov = { ...d.ov }; if (n === 2) { ov.words = 6; ov.max_chars = 44 } else { delete ov.words; delete ov.max_chars } return { ...d, ov } })
  }
  // the person cut-out is made on demand the first time a "behind you" template is used
  const needMatte = !!style?.behind && design.ov.behind !== false
  const matteFresh = job?.matte === 'ready' && (job?.matte_fit || 'auto') === (design.fit || 'auto')
  React.useEffect(() => {
    if (needMatte && job && job.proxy === 'ready' && !matteFresh && !['making', 'error'].includes(job.matte || '') &&
        !['queued', 'transcribing', 'rendering'].includes(job.status)) {
      send(`/api/jobs/${id}/run`, 'POST', { kind: 'matte', fit: design.fit || 'auto' }).catch(() => {})
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [needMatte, matteFresh, job?.proxy, job?.status, job?.matte])

  if (!job) return <div className="flex h-full items-center justify-center text-muted-foreground">Video not found. <a className="ml-2 text-primary" href="#/">Back</a></div>
  const proxyReady = job.proxy === 'ready'
  const src = proxyReady ? `/api/jobs/${id}/proxy.mp4?v=${job.fit || 'auto'}` : null
  const matteSrc = needMatte && matteFresh ? `/api/jobs/${id}/matte.mp4?v=${job.matte_fit}` : null
  const mattePending = needMatte && !matteFresh
    ? (job.matte === 'error' ? 'Person cut-out failed — see Activity log' : `Cutting out the person… ${job.status === 'transcribing' && job.step === 'matte' ? Math.round((job.progress || 0) * 100) + '%' : ''}`)
    : null

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <header className="flex items-center gap-3 border-b px-4 py-2">
        <Button variant="ghost" size="sm" onClick={() => (location.hash = '#/')}><ArrowLeft className="h-4 w-4" />Videos</Button>
        <div className="min-w-0 truncate text-sm font-semibold" title={job.name}>{job.name}</div>
        {job.tinfo && <span className="hidden text-xs text-muted-foreground lg:inline">{job.language} · {job.tinfo}</span>}
        <div className="flex-1" />
        <a href={`/api/jobs/${id}/srt`} className="inline-flex h-8 cursor-pointer items-center gap-1.5 rounded-lg border bg-muted px-3 text-xs font-medium hover:bg-accent"><Download className="h-3.5 w-3.5" />SRT</a>
        <div className="w-28"><Select value={design.quality || '1080p'} onValueChange={(v) => setDesign((d) => ({ ...d, quality: v }))} options={[{ value: '2k', label: '2K (1440×2560)' }, { value: '1080p', label: '1080p' }, { value: '720p', label: '720p' }]} className="h-8 text-xs" /></div>
        <div className="w-24"><Select value={design.fps || 'source'} onValueChange={(v) => setDesign((d) => ({ ...d, fps: v }))} options={[{ value: '60', label: '60 FPS' }, { value: '30', label: '30 FPS' }, { value: 'source', label: 'Source FPS' }]} className="h-8 text-xs" /></div>
        <Button onClick={exportNow} disabled={exporting || ['queued', 'transcribing', 'rendering'].includes(job.status)}>{exporting || ['queued', 'transcribing', 'rendering'].includes(job.status) ? <Loader2 className="h-4 w-4 animate-spin" /> : <Rocket className="h-4 w-4" />}{['queued', 'transcribing', 'rendering'].includes(job.status) ? 'Exporting…' : 'Export'}</Button>
      </header>

      <div className="grid min-h-0 flex-1 grid-cols-[300px_minmax(0,1fr)_380px]">
        <aside className="min-h-0 border-r bg-card/30">
          {segments && <CaptionsPanel segments={segments} t={t} sel={sel} setSel={setSel} seek={seek} behindStyle={!!style?.behind} ops={ops} lines={lines} setLines={setLines} />}
        </aside>

        <main className="min-h-0 min-w-0 p-3">
          {src ? (
            <PreviewPlayer src={src} matteSrc={matteSrc} assFront={assPair.front} assBehind={matteSrc ? assPair.behind : null} fonts={fonts} videoRef={videoRef} t={t} setT={setT}
              duration={job.duration} safeGuide={safeGuide} setSafeGuide={setSafeGuide} playing={playing} setPlaying={setPlaying}
              onShortcuts={() => setKeys(true)} toggle={toggle} mattePending={mattePending}>
              {!playing && style && <LayoutBoxes style={style} ov={design.ov} setOv={setOv} behind={needMatte} />}
            </PreviewPlayer>
          ) : (
            <div className="flex h-full flex-col items-center justify-center gap-2 text-sm text-muted-foreground">
              {job.proxy === 'error' ? <><AlertTriangle className="h-6 w-6 text-destructive" />Preview copy failed — see the Activity log on the first page.</> : <><Loader2 className="h-6 w-6 animate-spin" />Preparing a fast preview of your video…</>}
            </div>
          )}
        </main>

        <aside className="flex min-h-0 flex-col border-l bg-card/30">
          <Tabs value={tab} onValueChange={setTab} className="flex min-h-0 flex-1 flex-col">
            <div className="p-3 pb-2">
              <TabsList>
                <TabsTrigger value="style"><Paintbrush className="h-3.5 w-3.5" />Templates</TabsTrigger>
                <TabsTrigger value="customize"><SlidersHorizontal className="h-3.5 w-3.5" />Customize</TabsTrigger>
                <TabsTrigger value="export"><Rocket className="h-3.5 w-3.5" />Export</TabsTrigger>
              </TabsList>
            </div>
            <div className="min-h-0 flex-1 overflow-auto px-3 pt-1">
              <TabsContent value="style" className="h-full"><StylePanel styles={styles} design={design} setStyle={setStyle} setDesign={setDesign} /></TabsContent>
              <TabsContent value="customize">{style && <CustomizePanel style={style} design={design} setOv={setOv} setDesign={setDesign} fonts={fonts} reset={() => setDesign((d) => ({ ...d, ov: {}, offset: 0 }))} />}</TabsContent>
              <TabsContent value="export"><ExportPanel job={job} styles={styles} design={design} setDesign={setDesign} /></TabsContent>
            </div>
          </Tabs>
        </aside>
      </div>

      {segments && (
        <Timeline
          segments={segments} duration={job.duration} t={t} playing={playing} peaks={peaks} sel={sel} setSel={setSel} pps={pps} setPps={setPps}
          snap={snap} setSnap={setSnap} actions={actions} styleBehind={behindStyle}
          onSeek={seek} begin={begin} update={update} undo={undo} redo={redo}
          canUndo={hist.current.past.length > 0} canRedo={hist.current.future.length > 0}
        />
      )}

      {toast && <div className="pointer-events-none fixed bottom-48 left-1/2 z-40 -translate-x-1/2 rounded-full bg-foreground px-4 py-1.5 text-sm font-medium text-background shadow-lg">{toast}</div>}
      <Dialog open={keys} onOpenChange={setKeys}>
        <DialogContent title="Keyboard shortcuts" description="Same keys as CapCut for PC. Click the video or timeline first so the keys go to the editor.">
          <div className="grid gap-x-8 gap-y-1 text-sm sm:grid-cols-2">
            {SHORTCUTS.map(([k, d]) => <div key={k} className="flex items-center justify-between gap-3 border-b py-1.5"><span className="text-muted-foreground">{d}</span><kbd className="rounded bg-muted px-2 py-0.5 text-xs font-semibold">{k}</kbd></div>)}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

