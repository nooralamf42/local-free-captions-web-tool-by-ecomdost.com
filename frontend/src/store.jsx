import * as React from 'react'
import { getJSON } from '@/lib/api'

const Ctx = React.createContext(null)
export const useStore = () => React.useContext(Ctx)

const ls = {
  get(k, d) { try { const v = localStorage.getItem('lc2_' + k); return v == null ? d : JSON.parse(v) } catch { return d } },
  set(k, v) { try { localStorage.setItem('lc2_' + k, JSON.stringify(v)) } catch { /* private mode */ } },
}
export { ls }

export function StoreProvider({ children }) {
  const [state, setState] = React.useState({ jobs: [], log: [], now: 0, gpu: null, nvenc: null })
  const [styles, setStyles] = React.useState([])
  const [fonts, setFonts] = React.useState([])
  const [design, setDesignRaw] = React.useState(() => ls.get('design', { style: 'hormozi', ov: {} }))
  const [speech, setSpeechRaw] = React.useState(() => ls.get('speech', { lang: 'auto', mode: 'roman', model: 'apex' }))
  const [online, setOnline] = React.useState(true)

  const refresh = React.useCallback(async () => {
    try { setState(await getJSON('/api/state')); setOnline(true) } catch { setOnline(false) }
  }, [])
  React.useEffect(() => { refresh(); const t = setInterval(refresh, 1000); return () => clearInterval(t) }, [refresh])
  React.useEffect(() => {
    getJSON('/api/styles').then(setStyles).catch(() => {})
    getJSON('/api/fonts').then(setFonts).catch(() => {})
  }, [])

  const setDesign = React.useCallback((fn) => {
    setDesignRaw((d) => { const n = typeof fn === 'function' ? fn(d) : fn; ls.set('design', n); return n })
  }, [])
  const setSpeech = React.useCallback((fn) => {
    setSpeechRaw((d) => { const n = typeof fn === 'function' ? fn(d) : fn; ls.set('speech', n); return n })
  }, [])

  const value = { state, refresh, styles, fonts, design, setDesign, speech, setSpeech, online }
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}
