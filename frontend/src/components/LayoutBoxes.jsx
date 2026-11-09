import * as React from 'react'
import { cn } from '@/lib/utils'

/** Draggable "Title" (big word behind you) and "Caption" boxes over the preview, like other caption editors. Percent coordinates. */
export default function LayoutBoxes({ style, ov, setOv, behind }) {
  const ref = React.useRef()
  const v = (k) => (ov[k] !== undefined ? ov[k] : style[k])
  const drag = (kx, ky) => (e) => {
    e.preventDefault(); e.stopPropagation()
    const r = ref.current.getBoundingClientRect()
    const mv = (ev) => {
      const x = Math.round(Math.min(95, Math.max(5, ((ev.clientX - r.left) / r.width) * 100)))
      const y = Math.round(Math.min(97, Math.max(3, ((ev.clientY - r.top) / r.height) * 100)))
      setOv((o) => ({ ...o, [kx]: x, [ky]: y, ...(ky === 'y' ? { safe: false } : {}) }))
    }
    const up = () => { window.removeEventListener('pointermove', mv); window.removeEventListener('pointerup', up) }
    window.addEventListener('pointermove', mv); window.addEventListener('pointerup', up)
  }
  const box = (label, kx, ky, wPct, hPct, tone) => (
    <div
      onPointerDown={drag(kx, ky)}
      className={cn('absolute -translate-x-1/2 -translate-y-1/2 cursor-move rounded border border-dashed text-[10px] font-semibold', tone)}
      style={{ left: v(kx) + '%', top: v(ky) + '%', width: wPct + '%', height: hPct + '%' }}
    >
      <span className="absolute -top-4 left-0 rounded bg-black/70 px-1.5 py-0.5 text-white">{label}</span>
    </div>
  )
  const capH = Math.max(4, (v('size') * 1.35 * (style.words > 3 ? 1.6 : 1)) / 19.2)
  const heroH = Math.max(6, (v('hero_size') * 1.1) / 19.2)
  return (
    <div ref={ref} className="absolute inset-0 touch-none">
      {behind && box('Title (behind you)', 'hero_x', 'hero_y', 84, heroH, 'border-yellow-400/80 bg-yellow-400/5')}
      {box('Caption', 'x', 'y', 72, capH, 'border-white/70 bg-white/5')}
    </div>
  )
}
