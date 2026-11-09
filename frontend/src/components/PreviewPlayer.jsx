import * as React from 'react'
import JASSUB from 'jassub'
import { Play, Pause, Volume2, VolumeX, RotateCcw, Shield, Keyboard, Loader2, Move, Maximize, Minimize } from 'lucide-react'
import { Button } from '@/components/ui'
import { cn, fmtTP } from '@/lib/utils'

const MIN_ASS = '[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Cap,Poppins ExtraBold,80,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,4,0,5,40,40,40,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'

/** libass (WASM) renderer drawing into a hidden canvas that we copy from. */
function makeSub(fonts, firstAss) {
  const abs = (u) => new URL(u, location.href).href
  const availableFonts = Object.fromEntries(fonts.map((f) => [f.family.toLowerCase(), abs('/fonts/' + f.file)]))
  const canvas = document.createElement('canvas')
  canvas.width = 540; canvas.height = 960
  canvas.style.cssText = 'position:fixed;left:-10000px;top:0;width:270px;height:480px;pointer-events:none'
  document.body.appendChild(canvas)   // must live in the document or the worker's frames are never committed
  const inst = new JASSUB({
    canvas, subContent: firstAss || MIN_ASS, fonts: Object.values(availableFonts), availableFonts,
    defaultFont: 'poppins extrabold', queryFonts: false,
  })
  const o = { inst, canvas, ready: false, has: false, destroy() { try { inst.destroy() } catch { /* ignore */ } canvas.remove() } }
  inst.ready.then(() => { o.ready = true }).catch((e) => console.error('JASSUB', e))
  return o
}

/** 9:16 preview. Everything — video, captions behind the person, the person cut-out, captions in front — is composited
 *  into ONE canvas by us (no transparent overlays on a hardware video layer, which went black on some GPUs). */
export default function PreviewPlayer({ src, matteSrc, assFront, assBehind, fonts, videoRef, t, setT, duration, safeGuide, setSafeGuide,
  playing, setPlaying, onShortcuts, toggle, mattePending, children }) {
  const [muted, setMuted] = React.useState(false)
  const shown = React.useRef(null)
  const matteRef = React.useRef(null)
  const subs = React.useRef({ front: null, behind: null })
  const latest = React.useRef({ assFront, assBehind, matteSrc })
  const dirty = React.useRef(true)
  latest.current = { assFront, assBehind, matteSrc }

  React.useEffect(() => {
    const video = videoRef.current, out = shown.current
    if (!video || !out || !fonts.length) return
    const front = makeSub(fonts, latest.current.assFront)
    const behind = makeSub(fonts, null)
    subs.current = { front, behind }
    const cut = document.createElement('canvas'), mask = document.createElement('canvas')   // person cut-out scratch canvases
    const g = out.getContext('2d')
    let dead = false, raf, lastT = -1, lastW = 0
    const loop = () => {
      raf = requestAnimationFrame(loop)
      if (dead) return
      const dpr = Math.min(2, window.devicePixelRatio || 1)
      const w = Math.max(2, Math.round(out.clientWidth * dpr)), h = Math.max(2, Math.round(out.clientHeight * dpr))
      if (out.width !== w || out.height !== h) { out.width = w; out.height = h }
      const mt = video.currentTime
      const m = matteRef.current
      if (m && m.src) {   // keep the matte video on the same frame as the main video
        if (video.paused !== m.paused) video.paused ? m.pause() : m.play().catch(() => {})
        if (Math.abs(m.currentTime - mt) > 0.12 || (video.paused && Math.abs(m.currentTime - mt) > 0.02)) m.currentTime = mt
      }
      if (dirty.current || mt !== lastT || w !== lastW) {
        lastT = mt; lastW = w; dirty.current = false
        for (const s of [front, behind]) if (s.ready && s.has) s.inst.manualRender({ expectedDisplayTime: performance.now(), width: w, height: h, mediaTime: mt })
      }
      g.fillStyle = '#000'; g.fillRect(0, 0, w, h)
      if (video.readyState >= 2) g.drawImage(video, 0, 0, w, h)
      if (behind.ready && behind.has) g.drawImage(behind.canvas, 0, 0, w, h)
      if (latest.current.assBehind && m && m.src && m.readyState >= 2 && video.readyState >= 2) {
        if (cut.width !== w || cut.height !== h) { cut.width = mask.width = w; cut.height = mask.height = h }
        const c1 = cut.getContext('2d'), c2 = mask.getContext('2d')
        c2.clearRect(0, 0, w, h); c2.filter = 'url(#lum2alpha)'; c2.drawImage(m, 0, 0, w, h); c2.filter = 'none'   // luminance -> alpha
        c1.globalCompositeOperation = 'source-over'; c1.clearRect(0, 0, w, h); c1.drawImage(video, 0, 0, w, h)
        c1.globalCompositeOperation = 'destination-in'; c1.drawImage(mask, 0, 0)
        g.drawImage(cut, 0, 0)
      }
      if (front.ready && front.has) g.drawImage(front.canvas, 0, 0, w, h)
    }
    raf = requestAnimationFrame(loop)
    return () => { dead = true; cancelAnimationFrame(raf); front.destroy(); behind.destroy(); subs.current = {} }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fonts.length, src])

  // push new ASS text to the renderers
  React.useEffect(() => {
    const { front, behind } = subs.current
    if (front && assFront) { front.inst.ready.then(() => { front.inst.renderer.setTrack(assFront); front.has = true; dirty.current = true }).catch(() => {}) }
    if (behind) {
      if (assBehind) behind.inst.ready.then(() => { behind.inst.renderer.setTrack(assBehind); behind.has = true; dirty.current = true }).catch(() => {})
      else { behind.has = false; dirty.current = true }
    }
  }, [assFront, assBehind, fonts.length, src])

  // video clock -> React state, play state
  React.useEffect(() => {
    const v = videoRef.current
    if (!v) return
    let raf
    const loop = () => { setT(v.currentTime); raf = requestAnimationFrame(loop) }
    const onPlay = () => { setPlaying(true); cancelAnimationFrame(raf); raf = requestAnimationFrame(loop) }
    const onPause = () => { setPlaying(false); cancelAnimationFrame(raf); setT(v.currentTime) }
    const onSeek = () => { setT(v.currentTime); dirty.current = true }
    v.addEventListener('play', onPlay); v.addEventListener('pause', onPause); v.addEventListener('seeked', onSeek); v.addEventListener('ended', onPause)
    if (!v.paused) onPlay()
    return () => { cancelAnimationFrame(raf); v.removeEventListener('play', onPlay); v.removeEventListener('pause', onPause); v.removeEventListener('seeked', onSeek); v.removeEventListener('ended', onPause) }
  }, [videoRef, setT, setPlaying, src])

  const wrapRef = React.useRef(null)
  const [full, setFull] = React.useState(false)
  // real browser full screen where it is allowed; otherwise the player fills the window (a webview may refuse the API)
  const toggleFull = async () => {
    if (document.fullscreenElement) { document.exitFullscreen(); return }
    if (full) { setFull(false); dirty.current = true; return }
    try { await wrapRef.current.requestFullscreen() } catch { setFull(true); dirty.current = true }
  }
  React.useEffect(() => {
    const on = () => { setFull(document.fullscreenElement === wrapRef.current); dirty.current = true }
    const key = (e) => {
      if (/INPUT|TEXTAREA|SELECT/.test(e.target.tagName) || e.ctrlKey || e.metaKey) return
      if (e.key === 'f' || e.key === 'F') toggleFull()
      else if (e.key === 'Escape') setFull((f) => { if (f && !document.fullscreenElement) dirty.current = true; return document.fullscreenElement ? f : false })
    }
    document.addEventListener('fullscreenchange', on); window.addEventListener('keydown', key)
    return () => { document.removeEventListener('fullscreenchange', on); window.removeEventListener('keydown', key) }
  })

  return (
    <div ref={wrapRef} className={cn('flex h-full min-h-0 flex-col items-center gap-2', full && 'fixed inset-0 z-50 bg-black p-3')}>
      <svg width="0" height="0" className="absolute" aria-hidden>
        <filter id="lum2alpha" colorInterpolationFilters="sRGB">
          <feColorMatrix type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  1 0 0 0 0" />
        </filter>
      </svg>
      <div className="relative min-h-0 flex-1 overflow-hidden rounded-xl border bg-black" style={{ aspectRatio: '9 / 16', maxWidth: '100%' }}>
        <video ref={videoRef} src={src} playsInline muted={muted} className="pointer-events-none absolute inset-0 h-full w-full opacity-0" />
        {matteSrc && <video ref={matteRef} src={matteSrc} muted playsInline preload="auto" className="pointer-events-none absolute h-px w-px opacity-0" />}
        <canvas ref={shown} onClick={toggle} className="absolute inset-0 h-full w-full cursor-pointer" />
        {safeGuide && (
          <div className="pointer-events-none absolute inset-0">
            <div className="absolute inset-x-0 top-0 h-[12%] bg-red-500/20" />
            <div className="absolute inset-x-0 bottom-0 h-[22%] bg-red-500/20" />
            <div className="absolute bottom-[22%] right-0 top-[48%] w-[12%] bg-red-500/20" />
            <div className="absolute left-1 top-1 rounded bg-black/60 px-1.5 py-0.5 text-[10px] text-red-300">Instagram UI zone</div>
          </div>
        )}
        {children}
        {mattePending && (
          <div className="pointer-events-none absolute inset-x-2 top-2 flex items-center gap-2 rounded-lg bg-black/70 px-3 py-2 text-xs text-white">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />{mattePending}
          </div>
        )}
        {!playing && (
          <button onClick={toggle} className="absolute left-1/2 top-1/2 flex h-14 w-14 -translate-x-1/2 -translate-y-1/2 cursor-pointer items-center justify-center rounded-full bg-black/50 text-white backdrop-blur hover:bg-black/70">
            <Play className="ml-1 h-6 w-6" />
          </button>
        )}
      </div>
      <div className="flex w-full max-w-[420px] items-center gap-1 rounded-lg border bg-card px-2 py-1.5">
        <Button size="icon" variant="ghost" onClick={() => { videoRef.current.currentTime = 0 }} title="Restart (Home)"><RotateCcw className="h-4 w-4" /></Button>
        <Button size="icon" variant="ghost" onClick={toggle} title="Play / pause (Space)">{playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}</Button>
        <span className="min-w-[88px] text-xs tabular-nums text-muted-foreground">{fmtTP(t)} / {fmtTP(duration)}</span>
        <div className="flex-1" />
        <Button size="icon" variant="ghost" onClick={() => setMuted((m) => !m)} title="Mute">{muted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}</Button>
        <Button size="icon" variant="ghost" className={cn(safeGuide && 'bg-accent text-red-300')} onClick={() => setSafeGuide(!safeGuide)} title="Instagram safe-area guide"><Shield className="h-4 w-4" /></Button>
        <Button size="icon" variant="ghost" onClick={toggleFull} title="Full screen (F)">{full ? <Minimize className="h-4 w-4" /> : <Maximize className="h-4 w-4" />}</Button>
        <Button size="icon" variant="ghost" onClick={onShortcuts} title="Keyboard shortcuts (?)"><Keyboard className="h-4 w-4" /></Button>
      </div>
    </div>
  )
}
