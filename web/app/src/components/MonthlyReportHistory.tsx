import { useEffect, useState } from 'react'
import { MonthlyReportService } from '../services/api'

type Report = {
    key: string; month: string; scope: string; attempts: number; last_error?: string;
    invoices_state: string; confirmation_state: string;
}
const labels: Record<string, string> = {
    pending: 'Në pritje', failed: 'Dështoi — do të riprovohet', sent: 'Dërguar',
    sending: 'Në dërgim', uncertain: 'Kërkon verifikim', empty: 'Pa fatura'
}

export default function MonthlyReportHistory() {
    const [rows, setRows] = useState<Report[]>([])
    const [error, setError] = useState('')
    const [busy, setBusy] = useState(false)
    const [events, setEvents] = useState<{ action: string; detail: string; at: string }[]>([])
    const load = async () => {
        setBusy(true)
        try { setRows(await MonthlyReportService.history()); setError('') }
        catch { setError('Historiku nuk u ngarkua. Kontrolloni backend-in dhe provoni sërish.') }
        finally { setBusy(false) }
    }
    useEffect(() => { void load() }, [])
    const resolve = async (row: Report, channel: string, delivered: boolean) => {
        const note = window.prompt('Pasi të kontrolloni email-in ose log-et SMTP, shënoni si e verifikuat dërgimin:')
        if (!note?.trim()) return
        if (!window.confirm(delivered ? 'Shëno këtë email si të dërguar?' : 'Lejo riprovimin? Nëse email-i është dërguar më parë, marrësi do ta marrë përsëri.')) return
        setBusy(true)
        try { await MonthlyReportService.resolve(row.key, channel, delivered, note); await load() }
        catch { setError('Statusi nuk u ndryshua. Ekzekutimi mund të jetë ende aktiv.'); setBusy(false) }
    }
    return <div className="pt-4 border-t border-border space-y-3">
        <div className="flex items-center justify-between gap-3">
            <h4 className="font-bold text-sm">Historiku i raporteve mujore</h4>
            <button type="button" disabled={busy} onClick={() => void load()} className="text-sm text-primary disabled:opacity-50">{busy ? 'Duke ngarkuar…' : 'Rifresko'}</button>
        </div>
        {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
        {!rows.length && !busy && !error && <p className="text-sm text-muted-foreground">Nuk ka ende ekzekutime të regjistruara.</p>}
        {rows.map(row => <div key={row.key} className="rounded-xl border border-border p-3 text-sm space-y-2">
            <p className="font-semibold">{row.month}{row.scope === 'test' ? ' (test)' : ''} · {row.attempts} përpjekje</p>
            {(['invoices', 'confirmation'] as const).map(channel => {
                const state = row[`${channel}_state`]
                return <div key={channel}>
                    <span>{channel === 'invoices' ? 'Faturat' : 'Konfirmimi'}: {labels[state] || state}</span>
                    {['uncertain', 'sending'].includes(state) && <div className="flex flex-wrap gap-3 mt-1">
                        <button type="button" disabled={busy} className="text-primary" onClick={() => void resolve(row, channel, true)}>Verifikova: është dërguar</button>
                        <button type="button" disabled={busy} className="text-primary" onClick={() => void resolve(row, channel, false)}>Verifikova: nuk është dërguar</button>
                    </div>}
                </div>
            })}
            {row.last_error && <p className="text-red-600 break-words">{row.last_error}</p>}
            <button type="button" className="text-primary" onClick={async () => {
                try { setEvents(await MonthlyReportService.events(row.key)) }
                catch { setError('Detajet nuk u ngarkuan.') }
            }}>Shiko përpjekjet</button>
        </div>)}
        {!!events.length && <div className="text-xs space-y-1 max-h-48 overflow-auto" aria-label="Përpjekjet e raportit">
            {events.map((e, i) => <p key={i}>{e.at} UTC — {e.action}: {e.detail}</p>)}
        </div>}
    </div>
}
