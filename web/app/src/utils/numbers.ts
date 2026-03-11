/**
 * Parson një string numerik duke lejuar edhe presje si ndarës dhjetor (p.sh. "1,5" → 1.5).
 * I përshtatshëm për fushat e faturës, ofertës, kontratës etj.
 */
export function parseDecimal(value: string | number | null | undefined): number {
    if (value === '' || value === null || value === undefined) return 0
    const s = String(value).trim().replace(',', '.')
    const n = parseFloat(s)
    return Number.isFinite(n) ? n : 0
}
