import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
export const cn = (...a) => twMerge(clsx(a))
export const fmtT = (s) => { s = Math.max(0, s || 0); const m = Math.floor(s / 60); return m + ':' + String(Math.floor(s % 60)).padStart(2, '0') }
export const fmtTP = (s) => { s = Math.max(0, s || 0); return s.toFixed(1) + 's' }
