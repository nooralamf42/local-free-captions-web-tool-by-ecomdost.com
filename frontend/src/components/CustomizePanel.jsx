import * as React from 'react'
import { RotateCcw } from 'lucide-react'
import { Button, Label, Section, Select, Slider, Switch, ToggleGroup, ToggleItem } from '@/components/ui'
import { cn } from '@/lib/utils'

const ANIMS = [['pop', 'Pop'], ['bounce', 'Bounce'], ['fade', 'Fade'], ['slide', 'Slide up'], ['none', 'None']].map(([value, label]) => ({ value, label }))

/** Phone-shaped map: drag the dot (or tap a grid point) to place captions anywhere. */
function PlacementMap({ x, y, safe, onChange }) {
  const ref = React.useRef()
  const set = (e) => {
    const r = ref.current.getBoundingClientRect()
    const nx = Math.min(100, Math.max(0, ((e.clientX - r.left) / r.width) * 100))
    const ny = Math.min(100, Math.max(0, ((e.clientY - r.top) / r.height) * 100))
    onChange(Math.round(nx), Math.round(ny))
  }
  const down = (e) => {
    e.currentTarget.setPointerCapture(e.pointerId); set(e)
    const mv = (ev) => set(ev), up = () => { window.removeEventListener('pointermove', mv); window.removeEventListener('pointerup', up) }
    window.addEventListener('pointermove', mv); window.addEventListener('pointerup', up)
  }
  const pts = []
  for (const py of [12, 30, 50, 66, 78]) for (const px of [18, 50, 82]) pts.push([px, py])
  return (
    <div className="flex items-center gap-4">
      <div ref={ref} onPointerDown={down} className="relative h-[236px] w-[133px] shrink-0 cursor-crosshair touch-none overflow-hidden rounded-xl border bg-muted">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-[12%] bg-red-500/15" />
        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-[22%] bg-red-500/15" />
        <div className="pointer-events-none absolute bottom-[22%] right-0 top-[48%] w-[12%] bg-red-500/15" />
        {pts.map(([px, py]) => <div key={px + '-' + py} className="pointer-events-none absolute h-1 w-1 -translate-x-1/2 -translate-y-1/2 rounded-full bg-white/25" style={{ left: px + '%', top: py + '%' }} />)}
        <div className="pointer-events-none absolute h-3 w-[60px] -translate-x-1/2 -translate-y-1/2 rounded-sm bg-primary/30 ring-1 ring-primary" style={{ left: x + '%', top: y + '%' }} />
        <div className="pointer-events-none absolute h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-primary shadow" style={{ left: x + '%', top: y + '%' }} />
      </div>
      <div className="space-y-2 text-xs text-muted-foreground">
        <div>Left/right <b className="text-foreground">{Math.round(x)}%</b></div>
        <div>Top/bottom <b className="text-foreground">{Math.round(y)}%</b></div>
        <div className="flex flex-wrap gap-1">
          {[['Top', 50, 18], ['Middle', 50, 50], ['Lower', 50, 66], ['Bottom', 50, 76]].map(([n, px, py]) => (
            <Button key={n} size="xs" variant="secondary" onClick={() => onChange(px, py)}>{n}</Button>
          ))}
        </div>
        <div className="flex items-center gap-2 pt-1"><Switch checked={safe} onCheckedChange={(v) => onChange(null, null, v)} /><span>Stay inside Instagram safe area</span></div>
        <p className="text-[10px] leading-snug">Red = covered by Instagram buttons/text. Turn the switch off to place captions anywhere.</p>
      </div>
    </div>
  )
}

const Row = ({ label, value, children }) => (
  <div className="space-y-1.5">
    <div className="flex items-center justify-between"><Label>{label}</Label><span className="text-[11px] tabular-nums text-muted-foreground">{value}</span></div>
    {children}
  </div>
)
const Swatch = ({ label, value, onChange }) => (
  <div className="flex flex-1 flex-col items-center gap-1">
    <input type="color" value={value} onChange={(e) => onChange(e.target.value)} className="h-9 w-full" />
    <span className="text-[11px] text-muted-foreground">{label}</span>
  </div>
)

export default function CustomizePanel({ style, design, setOv, setDesign, fonts, reset }) {
  const ov = design.ov
  const val = (k) => (ov[k] !== undefined ? ov[k] : style[k])
  const wordsVal = ov.words !== undefined ? String(ov.words) : 'auto'
  return (
    <div className="space-y-3 pb-6">
      <Section title="Placement" hint="Where captions sit — drag anywhere.">
        <PlacementMap
          x={val('x') ?? 50} y={val('y')} safe={ov.safe !== false}
          onChange={(x, y, safe) => setOv((o) => ({ ...o, ...(x != null ? { x, y } : {}), ...(safe !== undefined ? { safe } : {}) }))}
        />
      </Section>

      {style.behind && (
        <Section title="Title · big word behind you" hint="The key word of each caption, shown huge BEHIND the person.">
          <div className="flex items-center justify-between rounded-lg border p-2.5 text-xs">
            <span>Put the big word behind the person</span>
            <Switch checked={ov.behind !== false} onCheckedChange={(v) => setOv((o) => ({ ...o, behind: v }))} />
          </div>
          <Row label="Big word size" value={Math.round(val('hero_size')) + ' px'}>
            <Slider min={60} max={420} step={5} value={[val('hero_size')]} onValueChange={(v) => setOv((o) => ({ ...o, hero_size: v[0] }))} />
          </Row>
          <Row label="Big word height on screen" value={Math.round(val('hero_y')) + '%'}>
            <Slider min={3} max={95} step={1} value={[val('hero_y')]} onValueChange={(v) => setOv((o) => ({ ...o, hero_y: v[0] }))} />
          </Row>
          <div className="flex gap-3">
            <Swatch label="Big word colour" value={val('hero_color')} onChange={(v) => setOv((o) => ({ ...o, hero_color: v }))} />
            <Swatch label="Its outline" value={val('hero_outline_color')} onChange={(v) => setOv((o) => ({ ...o, hero_outline_color: v }))} />
          </div>
          <div className="space-y-1.5"><Label>Big word font</Label>
            <Select value={val('hero_font')} onValueChange={(v) => setOv((o) => ({ ...o, hero_font: v }))} options={fonts.map((f) => ({ value: f.family, label: f.family }))} />
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex items-center justify-between rounded-lg border p-2"><span>UPPERCASE</span><Switch checked={val('hero_upper') !== false} onCheckedChange={(v) => setOv((o) => ({ ...o, hero_upper: v }))} /></div>
            <div className="flex items-center justify-between rounded-lg border p-2"><span>Filled</span><Switch checked={val('hero_fill') !== false} onCheckedChange={(v) => setOv((o) => ({ ...o, hero_fill: v }))} /></div>
          </div>
          <Row label="Big word outline" value={Math.round(val('hero_outline')) + ' px'}>
            <Slider min={0} max={20} step={1} value={[val('hero_outline')]} onValueChange={(v) => setOv((o) => ({ ...o, hero_outline: v[0] }))} />
          </Row>
          <div className="space-y-1.5"><Label>Show</Label>
            <ToggleGroup value={val('hero_mode')} onValueChange={(v) => v && setOv((o) => ({ ...o, hero_mode: v }))}>
              <ToggleItem value="word">Key word only</ToggleItem><ToggleItem value="phrase">Whole line big</ToggleItem>
            </ToggleGroup>
          </div>
          <div className="space-y-1.5"><Label>Big word motion</Label>
            <Select value={val('hero_anim')} onValueChange={(v) => setOv((o) => ({ ...o, hero_anim: v }))} options={ANIMS} />
          </div>
        </Section>
      )}
      <Section title="Size & words">
        <Row label="Caption size" value={Math.round(val('size')) + ' px'}>
          <Slider min={36} max={260} step={2} value={[val('size')]} onValueChange={(v) => setOv((o) => ({ ...o, size: v[0] }))} />
        </Row>
        <div className="space-y-1.5">
          <Label>Words on screen</Label>
          <ToggleGroup value={wordsVal} onValueChange={(v) => v && setOv((o) => { const n = { ...o }; if (v === 'auto') { delete n.words; delete n.max_chars } else { n.words = +v; n.max_chars = Math.max(14, +v * 9) } return n })}>
            {['auto', '1', '2', '3', '4', '5', '6'].map((x) => <ToggleItem key={x} value={x}>{x === 'auto' ? 'Style' : x}</ToggleItem>)}
          </ToggleGroup>
          <p className="text-[11px] text-muted-foreground">How many words appear together. “Style” keeps the template’s own number ({style.words}).</p>
        </div>
        <div className="space-y-1.5">
          <Label>Lines per caption</Label>
          <ToggleGroup value={ov.lines === undefined ? 'auto' : String(ov.lines)} onValueChange={(v) => v && setOv((o) => { const n = { ...o }; if (v === 'auto') { delete n.lines; delete n.words; delete n.max_chars } else { n.lines = +v; n.words = +v * 3; n.max_chars = +v * 22 } return n })}>
            {['auto', '1', '2', '3'].map((x) => <ToggleItem key={x} value={x}>{x === 'auto' ? 'Style' : x}</ToggleItem>)}
          </ToggleGroup>
        </div>
        <div className="space-y-1.5">
          <Label>Letter case</Label>
          <ToggleGroup value={ov.uppercase === undefined ? 'style' : ov.uppercase ? 'up' : 'normal'} onValueChange={(v) => v && setOv((o) => { const n = { ...o }; if (v === 'style') delete n.uppercase; else n.uppercase = v === 'up'; return n })}>
            <ToggleItem value="style">Style</ToggleItem><ToggleItem value="up">UPPERCASE</ToggleItem><ToggleItem value="normal">Normal</ToggleItem>
          </ToggleGroup>
        </div>
      </Section>

      <Section title="Colors & font">
        <div className="flex gap-3">
          <Swatch label="Text" value={val('color')} onChange={(v) => setOv((o) => ({ ...o, color: v }))} />
          <Swatch label="Highlight" value={val('active')} onChange={(v) => setOv((o) => ({ ...o, active: v }))} />
          <Swatch label="Outline" value={val('outline_color')} onChange={(v) => setOv((o) => ({ ...o, outline_color: v }))} />
          {style.box && <Swatch label="Box" value={val('box_color')} onChange={(v) => setOv((o) => ({ ...o, box_color: v }))} />}
        </div>
        <div className="space-y-1.5"><Label>Font</Label>
          <Select value={val('font')} onValueChange={(v) => setOv((o) => ({ ...o, font: v }))} options={fonts.map((f) => ({ value: f.family, label: f.family }))} />
        </div>
        <Row label="Outline thickness" value={Math.round(val('outline')) + ' px'}>
          <Slider min={0} max={24} step={1} value={[val('outline')]} onValueChange={(v) => setOv((o) => ({ ...o, outline: v[0] }))} />
        </Row>
        <Row label="Shadow" value={Math.round(val('shadow')) + ' px'}>
          <Slider min={0} max={14} step={1} value={[val('shadow')]} onValueChange={(v) => setOv((o) => ({ ...o, shadow: v[0] }))} />
        </Row>
      </Section>

      <Section title="Animation" hint="How captions come in and out, as in popular caption editors.">
        {style.mode === 'sweep'
          ? <p className="text-xs text-muted-foreground">Motion comes from the colour sweep across each word in this style.</p>
          : <div className="space-y-1.5"><Label>Words come in</Label><Select value={val('anim')} onValueChange={(v) => setOv((o) => ({ ...o, anim: v, support_motion: 'off' }))} options={ANIMS} /></div>}
        {style.mode !== 'sweep' && (
          <div className="flex items-center justify-between rounded-lg border p-2.5 text-xs">
            <span>Words appear one by one (off = whole line, the spoken word lights up)</span>
            <Switch checked={val('mode') === 'reveal'} onCheckedChange={(v) => setOv((o) => ({ ...o, mode: v ? 'reveal' : 'highlight' }))} />
          </div>
        )}
        {style.mode === 'reveal' && (
          <div className="space-y-1.5"><Label>Typing</Label>
            <ToggleGroup value={val('support_motion') === 'type' ? 'type' : 'off'} onValueChange={(v) => v && setOv((o) => ({ ...o, support_motion: v === 'type' ? 'type' : 'off' }))}>
              <ToggleItem value="off">Whole word</ToggleItem><ToggleItem value="type">Letter by letter</ToggleItem>
            </ToggleGroup>
          </div>
        )}
        <Row label="Caption fades in" value={(val('fade_in') || 0).toFixed(2) + ' s'}>
          <Slider min={0} max={0.6} step={0.05} value={[val('fade_in') || 0]} onValueChange={(v) => setOv((o) => ({ ...o, fade_in: v[0] }))} />
        </Row>
        <Row label="Caption fades out" value={(val('fade_out') || 0).toFixed(2) + ' s'}>
          <Slider min={0} max={0.6} step={0.05} value={[val('fade_out') || 0]} onValueChange={(v) => setOv((o) => ({ ...o, fade_out: v[0] }))} />
        </Row>
        {val('mode') === 'highlight' && (
          <>
            <div className="flex items-center justify-between rounded-lg border p-2.5 text-xs">
              <span>Keep said words highlighted</span>
              <Switch checked={!!val('keep_spoken')} onCheckedChange={(v) => setOv((o) => ({ ...o, keep_spoken: v }))} />
            </div>
            <div className="flex gap-3">
              <Swatch label="Said word" value={val('active')} onChange={(v) => setOv((o) => ({ ...o, active: v }))} />
              <Swatch label="Unsaid words" value={val('dim') || val('color')} onChange={(v) => setOv((o) => ({ ...o, dim: v }))} />
            </div>
            <Row label="Said word size" value={(val('active_scale') || 100) + '%'}>
              <Slider min={80} max={140} step={2} value={[val('active_scale') || 100]} onValueChange={(v) => setOv((o) => ({ ...o, active_scale: v[0] }))} />
            </Row>
          </>
        )}
        {style.emph && (
          <Row label="Key word glow" value={Math.round(val('emph_glow') || 0)}>
            <Slider min={0} max={40} step={1} value={[val('emph_glow') || 0]} onValueChange={(v) => setOv((o) => ({ ...o, emph_glow: v[0] }))} />
          </Row>
        )}
        {style.behind && (
          <>
            <div className="space-y-1.5"><Label>Big word enters with</Label>
              <Select value={val('hero_motion') || 'default'} onValueChange={(v) => setOv((o) => ({ ...o, hero_motion: v === 'default' ? style.hero_motion : v }))}
                options={[['default', 'Template default'], ['rise', 'Rise'], ['drop', 'Drop'], ['zoom', 'Zoom'], ['blur', 'Blur in'], ['wipe', 'Wipe'], ['type', 'Type'], ['stretch', 'Stretch'], ['skid', 'Skid'], ['flip', 'Flip'], ['stamp', 'Stamp'], ['flicker', 'Flicker'], ['pop', 'Pop']].map(([value, label]) => ({ value, label }))} />
              <p className="text-[11px] text-muted-foreground">Entrance motions, played on the key word that sits behind you.</p>
            </div>
            <Row label="Big word tilt" value={Math.round(val('hero_rot') || 0) + '°'}>
              <Slider min={-15} max={15} step={1} value={[val('hero_rot') || 0]} onValueChange={(v) => setOv((o) => ({ ...o, hero_rot: v[0] }))} />
            </Row>
            <Row label="Big word glow / softness" value={Math.round(val('hero_blur') || 0)}>
              <Slider min={0} max={20} step={1} value={[val('hero_blur') || 0]} onValueChange={(v) => setOv((o) => ({ ...o, hero_blur: v[0] }))} />
            </Row>
          </>
        )}
      </Section>

      <Section title="Timing & framing">
        <Row label="Captions earlier ⟵ ⟶ later" value={(design.offset || 0).toFixed(2) + ' s'}>
          <Slider min={-0.6} max={0.6} step={0.05} value={[design.offset || 0]} onValueChange={(v) => setDesign((d) => ({ ...d, offset: v[0] }))} />
        </Row>
        <div className="space-y-1.5"><Label>Video that isn’t 9:16</Label>
          <Select value={design.fit || 'auto'} onValueChange={(v) => setDesign((d) => ({ ...d, fit: v }))}
            options={[{ value: 'auto', label: 'Auto (blurred background fill)' }, { value: 'cover', label: 'Crop to fill' }, { value: 'contain', label: 'Black bars' }]} />
        </div>
      </Section>

      <Button variant="secondary" className="w-full" onClick={reset}><RotateCcw className="h-4 w-4" />Reset to style defaults</Button>
    </div>
  )
}

