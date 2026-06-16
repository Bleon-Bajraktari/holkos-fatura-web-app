/**
 * Vercel Serverless Function — Raporti mujor automatik i faturave.
 *
 * Në fund të muajit (cron, datë 1 të muajit pasardhës) mblidhen të gjitha faturat
 * e muajit dhe dërgohen:
 *   1) Te adresa "marrësi i faturave"  -> të gjitha PDF-të + listë.
 *   2) Te adresa "marrësi i konfirmimit" -> status SUKSES/DËSHTIM + listë + PDF-të,
 *      që të dihet saktësisht cilat fatura u dërguan.
 *
 * Render bllokon SMTP, prandaj dërgimi bëhet nga Vercel me nodemailer
 * (njësoj si send-bulk-email-smtp.js).
 *
 * Trigger:
 *   - Cron (GET): kërkon header `Authorization: Bearer ${CRON_SECRET}` ose `?key=${CRON_SECRET}`.
 *     Merr cilësimet (dy emailat) + SMTP nga backend-i. Muaji = muaji paraardhës.
 *   - Manual nga app (POST): trupi me { manual:true, month, invoices_email, status_email,
 *     smtp_*, company_name }. Përdoret nga butoni "Dërgo tani (test)" në Cilësime.
 *
 * Env vars (Vercel): CRON_SECRET (i detyrueshëm për cron), BACKEND_URL (opsional).
 */
import nodemailer from 'nodemailer'

// Render-i falas mund të jetë "fjetur" + gjenerimi i shumë PDF-ve zgjat;
// rrit kohëzgjatjen max të funksionit (Hobby lejon deri 60s).
export const config = { maxDuration: 60 }

const BACKEND_URL = (process.env.BACKEND_URL || 'https://holkos-fatura-api.onrender.com').replace(/\/$/, '')

const MONTHS_SQ = [
    'Janar', 'Shkurt', 'Mars', 'Prill', 'Maj', 'Qershor',
    'Korrik', 'Gusht', 'Shtator', 'Tetor', 'Nëntor', 'Dhjetor'
]

function pad2(n) {
    return String(n).padStart(2, '0')
}

/** Kthen { year, month0, from, to, label } për një muaj të dhënë (ose paraardhësin). */
function resolveMonth(monthParam, useCurrent) {
    let year, month0 // month0 = 0..11
    const m = typeof monthParam === 'string' ? monthParam.match(/^(\d{4})-(\d{1,2})$/) : null
    if (m) {
        year = parseInt(m[1], 10)
        month0 = parseInt(m[2], 10) - 1
    } else {
        const now = new Date()
        year = now.getFullYear()
        month0 = now.getMonth()
        if (!useCurrent) {
            // Muaji paraardhës (cron-i nis në datë 1 të muajit pasardhës).
            month0 -= 1
            if (month0 < 0) {
                month0 = 11
                year -= 1
            }
        }
    }
    const from = `${year}-${pad2(month0 + 1)}-01`
    const lastDay = new Date(year, month0 + 1, 0).getDate()
    const to = `${year}-${pad2(month0 + 1)}-${pad2(lastDay)}`
    const label = `${MONTHS_SQ[month0]} ${year}`
    return { year, month0, from, to, label }
}

function nrForFilename(inv) {
    const s = String(inv.invoice_number || '')
    const mm = s.match(/NR\.\s*(\d+)/i) || s.match(/(\d+)/)
    return mm ? mm[1] : inv.id
}

function fmtDate(d) {
    if (!d) return '(pa datë)'
    const dt = new Date(d)
    if (isNaN(dt.getTime())) return String(d)
    return dt.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function fmtMoney(v) {
    const n = Number(v || 0)
    return n.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €'
}

export default async function handler(req, res) {
    const isPost = req.method === 'POST'
    if (req.method !== 'GET' && !isPost) {
        return res.status(405).json({ detail: 'Method not allowed' })
    }

    const body = isPost && req.body ? req.body : {}
    const manual = isPost && body.manual === true
    const monthParam = body.month || (req.query && req.query.month) || null

    try {
        // --- Autorizimi ---
        // Cron/automatik: kërkon CRON_SECRET. Manual nga app: lejohet me trup të plotë.
        if (!manual) {
            const secret = process.env.CRON_SECRET
            if (!secret) {
                return res.status(500).json({ detail: 'CRON_SECRET nuk është konfiguruar në Vercel.' })
            }
            const authHeader = req.headers.authorization || req.headers.Authorization || ''
            const provided = authHeader.replace(/^Bearer\s+/i, '') || (req.query && req.query.key) || ''
            if (provided !== secret) {
                return res.status(401).json({ detail: 'I paautorizuar.' })
            }
        }

        // --- Token për backend-in (kërkon JWT për çdo path jo-publik) ---
        // Manual: përcjell token-in e userit nga app-i.
        // Cron: bëj login me kredencialet nga env (BACKEND_USERNAME/BACKEND_PASSWORD).
        let backendAuth = ''
        if (manual) {
            backendAuth = req.headers.authorization || req.headers.Authorization || ''
            if (!backendAuth) {
                return res.status(401).json({ detail: 'Mungon token-i. Hyni sërish në aplikacion dhe provoni.' })
            }
        } else {
            const u = process.env.BACKEND_USERNAME
            const p = process.env.BACKEND_PASSWORD
            if (!u || !p) {
                return res.status(500).json({ detail: 'Mungojnë BACKEND_USERNAME/BACKEND_PASSWORD në Vercel për login automatik.' })
            }
            const loginRes = await fetch(`${BACKEND_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
                body: JSON.stringify({ username: u, password: p })
            })
            if (!loginRes.ok) {
                return res.status(502).json({ detail: `Login në backend dështoi (${loginRes.status}).` })
            }
            const tok = await loginRes.json()
            backendAuth = `Bearer ${tok.access_token}`
        }
        const beHeaders = (accept) => ({ Accept: accept, Authorization: backendAuth })

        // --- Cilësimet (dy emailat) + SMTP ---
        let invoicesEmail = body.invoices_email
        let statusEmail = body.status_email
        let enabled = true
        let smtp = {
            server: body.smtp_server,
            port: body.smtp_port,
            user: body.smtp_user,
            password: body.smtp_password,
            company_name: body.company_name
        }

        if (!manual) {
            const [settingsRes, companyRes] = await Promise.all([
                fetch(`${BACKEND_URL}/settings/monthly-report`, { headers: beHeaders('application/json') }),
                fetch(`${BACKEND_URL}/company`, { headers: beHeaders('application/json') })
            ])
            if (settingsRes.ok) {
                const s = await settingsRes.json()
                enabled = !!s.enabled
                invoicesEmail = s.invoices_email
                statusEmail = s.status_email
            }
            if (companyRes.ok) {
                const c = await companyRes.json()
                smtp = {
                    server: c.smtp_server,
                    port: c.smtp_port,
                    user: c.smtp_user,
                    password: c.smtp_password,
                    company_name: c.name
                }
            }
        }

        if (!manual && !enabled) {
            return res.status(200).json({ skipped: true, reason: 'Raporti mujor është i çaktivizuar.' })
        }
        if (!invoicesEmail || !statusEmail) {
            return res.status(400).json({ detail: 'Mungojnë adresat e email-it (marrësi i faturave dhe/ose i konfirmimit) te Cilësimet.' })
        }
        if (!smtp.user || !smtp.password) {
            return res.status(400).json({ detail: 'Mungojnë kredencialet SMTP te Cilësimet.' })
        }

        // --- Muaji + faturat ---
        const period = resolveMonth(monthParam, manual)
        const invRes = await fetch(
            `${BACKEND_URL}/invoices?date_from=${period.from}&date_to=${period.to}`,
            { headers: beHeaders('application/json') }
        )
        if (!invRes.ok) {
            return res.status(502).json({ detail: `Backend nuk i ktheu faturat (${invRes.status}).` })
        }
        const invoices = await invRes.json()
        const list = Array.isArray(invoices) ? invoices : []

        const companyName = (smtp.company_name || 'Holkos').replace(/"/g, '')

        // Lejo disa adresa (ndara me presje ose pikëpresje) — sidomos për konfirmimin.
        const splitEmails = (s) => String(s || '').split(/[;,]/).map(x => x.trim()).filter(Boolean)
        const invoicesTo = splitEmails(invoicesEmail)
        const statusTo = splitEmails(statusEmail)

        const port = parseInt(smtp.port || '587', 10)
        const transporter = nodemailer.createTransport({
            host: smtp.server || 'smtp.gmail.com',
            port,
            secure: port === 465,
            auth: { user: smtp.user, pass: smtp.password },
            requireTLS: port === 587,
            connectionTimeout: 15000,
            greetingTimeout: 10000
        })

        // Listë e thjeshtë e faturave (për konfirmim): "NUMRI - DATA".
        const linesText = list.length
            ? list.map(inv => `${inv.invoice_number || 'Faturë ' + inv.id} - ${fmtDate(inv.date)}`).join('\n')
            : '(Nuk ka fatura për këtë muaj.)'
        const totalSum = list.reduce((acc, inv) => acc + Number(inv.total || 0), 0)

        // --- Shkarko PDF-të ---
        const attachments = []
        const failedPdf = []
        await Promise.all(list.map(async (inv) => {
            try {
                const r = await fetch(`${BACKEND_URL}/invoices/${inv.id}/pdf`, { headers: beHeaders('application/pdf') })
                if (r.ok) {
                    const ab = await r.arrayBuffer()
                    attachments.push({
                        filename: `fatura nr.${nrForFilename(inv)}.pdf`,
                        content: Buffer.from(ab)
                    })
                } else {
                    failedPdf.push(inv.invoice_number || `#${inv.id}`)
                }
            } catch (e) {
                failedPdf.push(inv.invoice_number || `#${inv.id}`)
            }
        }))

        // --- 1) Email te marrësi i faturave ---
        let invoicesSent = false
        let invoicesError = ''
        if (list.length > 0) {
            try {
                await transporter.sendMail({
                    from: `"${companyName}" <${smtp.user}>`,
                    to: invoicesTo,
                    subject: `Faturat e muajit ${period.label} - ${companyName}`,
                    text: `Faturat e muajit ${period.label} (${list.length}):\n\n${linesText}`,
                    attachments
                })
                invoicesSent = true
            } catch (e) {
                invoicesError = e.message || String(e)
            }
        }

        // --- 2) Email konfirmimi (status + listë + PDF-të) ---
        const statusLabel = list.length === 0
            ? 'PA FATURA'
            : (invoicesSent ? 'SUKSES' : 'DËSHTIM')
        let statusEmailSent = false
        let statusError = ''
        try {
            const lines = []
            lines.push('Përshëndetje,')
            lines.push('')
            lines.push(`Ky është konfirmimi automatik për faturat e muajit ${period.label}.`)
            lines.push('')

            if (list.length === 0) {
                lines.push('Statusi: PA FATURA')
                lines.push('Nuk u gjet asnjë faturë për këtë muaj, ndaj nuk u dërgua asgjë te marrësi i faturave.')
            } else if (invoicesSent) {
                lines.push('Statusi: ✓ DËRGIMI SUKSES')
                lines.push(`U dërguan me sukses ${list.length} fatura te ${invoicesTo.join(', ')}.`)
                lines.push(`Totali i faturave: ${fmtMoney(totalSum)}.`)
            } else {
                lines.push('Statusi: ✗ DËRGIMI DËSHTOI')
                lines.push(`Dërgimi i ${list.length} faturave te ${invoicesTo.join(', ')} dështoi.`)
                lines.push(`Arsyeja: ${invoicesError}`)
                lines.push('Faturat e listuara më poshtë NUK u dërguan te marrësi.')
            }

            if (failedPdf.length) {
                lines.push('')
                lines.push(`Kujdes: nuk u gjenerua PDF për: ${failedPdf.join(', ')}`)
            }

            lines.push('')
            lines.push(`Faturat e muajit (${list.length}):`)
            lines.push(linesText)
            lines.push('')
            lines.push('PDF-të e faturave janë bashkëngjitur këtu për dokumentim.')
            lines.push('')
            lines.push(`— ${companyName} (mesazh automatik)`)

            await transporter.sendMail({
                from: `"${companyName}" <${smtp.user}>`,
                to: statusTo,
                subject: `[${statusLabel}] Konfirmim — Faturat e muajit ${period.label}`,
                text: lines.join('\n'),
                attachments
            })
            statusEmailSent = true
        } catch (e) {
            statusError = e.message || String(e)
        }

        return res.status(200).json({
            month: period.label,
            range: { from: period.from, to: period.to },
            invoices_count: list.length,
            total: totalSum,
            invoices_email: invoicesEmail,
            status_email: statusEmail,
            invoices_email_sent: invoicesSent,
            invoices_email_error: invoicesError || undefined,
            status_email_sent: statusEmailSent,
            status_email_error: statusError || undefined,
            pdf_failed: failedPdf,
            status: statusLabel
        })
    } catch (error) {
        console.error('monthly-invoices-report error:', error)
        return res.status(500).json({ detail: error.message || 'Gabim gjatë gjenerimit të raportit mujor.' })
    }
}
