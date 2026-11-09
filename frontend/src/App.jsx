import * as React from 'react'
import Home from './pages/Home'
import Editor from './pages/Editor'

function useHash() {
  const [h, setH] = React.useState(location.hash)
  React.useEffect(() => { const f = () => setH(location.hash); window.addEventListener('hashchange', f); return () => window.removeEventListener('hashchange', f) }, [])
  return h
}

export default function App() {
  const hash = useHash()
  const m = hash.match(/^#\/edit\/(\w+)/)
  return m ? <Editor key={m[1]} id={m[1]} /> : <Home />
}
