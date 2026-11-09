import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwind from '@tailwindcss/vite'
import path from 'node:path'

// builds straight into ../web, which Flask serves; `npm run dev` proxies the API to the running Flask server
export default defineConfig({
  plugins: [react(), tailwind()],
  base: './',
  resolve: { alias: { '@': path.resolve(import.meta.dirname, 'src') } },
  build: { outDir: '../web', emptyOutDir: true, assetsInlineLimit: 0 },
  server: { proxy: { '/api': 'http://127.0.0.1:8765', '/fonts': 'http://127.0.0.1:8765', '/outputs': 'http://127.0.0.1:8765' } },
})
