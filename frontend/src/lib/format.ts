/** Indian digit grouping: 2570000 -> "₹25,70,000". */
export function inr(n: number | null | undefined, fallback = '—'): string {
  if (n === null || n === undefined || Number.isNaN(n)) return fallback
  const sign = n < 0 ? '−' : ''
  return `${sign}₹${Math.round(Math.abs(n)).toLocaleString('en-IN')}`
}

/** Compact lakh / crore: 220000 -> "₹2.20L". */
export function lakh(n: number | null | undefined, fallback = '—'): string {
  if (n === null || n === undefined || Number.isNaN(n)) return fallback
  const abs = Math.abs(n)
  const sign = n < 0 ? '−' : ''
  if (abs >= 1_00_00_000) return `${sign}₹${(abs / 1_00_00_000).toFixed(2)} Cr`
  if (abs >= 1_00_000) return `${sign}₹${(abs / 1_00_000).toFixed(2)} L`
  if (abs >= 1_000) return `${sign}₹${(abs / 1_000).toFixed(1)} K`
  return `${sign}₹${abs.toFixed(0)}`
}

export function humanize(s: string): string {
  return s.replaceAll('_', ' ')
}

export const CATEGORY_COLOR: Record<string, string> = {
  sanction_letter: 'var(--gold)',
  stock_statement: 'var(--teal)',
  debtor_ledger: 'var(--violet)',
  creditor_ledger: 'var(--blue)',
  bank_statement: 'var(--red)',
  other: 'var(--mut)',
}

export function categoryColor(c: string): string {
  return CATEGORY_COLOR[c] ?? CATEGORY_COLOR.other
}
