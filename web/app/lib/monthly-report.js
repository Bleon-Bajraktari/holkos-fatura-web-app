const splitEmails = value => String(value || '').split(/[;,]/).map(x => x.trim()).filter(Boolean)

export function createMonthlyHandler({ createTransport, fetchImpl = fetch, env = process.env, now = Date.now, log = console }) {
    return async function handler(req, res) {
        if (!['GET', 'POST'].includes(req.method)) return res.status(405).json({ detail: 'Method not allowed' })
        const body = req.method === 'POST' ? req.body || {} : {}
        const manual = req.method === 'POST' && body.manual === true
        const authorization = req.headers.authorization || ''
        if (!manual && (!env.CRON_SECRET || authorization !== `Bearer ${env.CRON_SECRET}`)) {
            return res.status(env.CRON_SECRET ? 401 : 503).json({ detail: 'Cron authorization is missing or invalid.' })
        }
        if (manual && !authorization) return res.status(401).json({ detail: 'Hyni sërish në aplikacion.' })
        const base = (env.BACKEND_URL || 'https://holkos-fatura-api.onrender.com').replace(/\/$/, '')
        const deadline = now() + 42000 // Reserve time for independent alert + ledger release within 60s.
        let auth = authorization
        let report
        let stage = 'login'
        const budget = () => {
            const remaining = deadline - now()
            if (remaining < 2500) throw new Error('Koha e përpunimit u tejkalua; do të riprovohet.')
            return Math.min(12000, remaining)
        }
        async function backend(path, data, pdf = false, cleanup = false) {
            const signal = AbortSignal.timeout(cleanup ? 3000 : budget())
            const response = await fetchImpl(`${base}${path}`, {
                method: data === undefined ? 'GET' : 'POST', signal,
                headers: { Authorization: auth, 'Content-Type': 'application/json', Accept: pdf ? 'application/pdf' : 'application/json' },
                ...(data === undefined ? {} : { body: JSON.stringify(data) })
            })
            if (!response.ok) {
                const error = new Error(`Backend ${path}: HTTP ${response.status}`)
                error.status = response.status
                // Backend error details are deliberately not logged; they can contain credentials.
                throw error
            }
            if (pdf) {
                const bytes = Buffer.from(await response.arrayBuffer())
                if (bytes.subarray(0, 5).toString() !== '%PDF-') throw new Error('Backend ktheu përmbajtje që nuk është PDF.')
                return bytes
            }
            return response.json()
        }
        const checkpoint = (action, channel, error) => backend(`/monthly-reports/${encodeURIComponent(report.key)}/transition`, {
            token: report.token, action, channel, error
        }, false, action === 'release')
        function transport(smtp, alert = false) {
            if (!smtp.smtp_user || !smtp.smtp_password || !smtp.smtp_server) throw new Error('Mungon konfigurimi SMTP.')
            const port = Number(smtp.smtp_port || 587)
            return createTransport({ host: smtp.smtp_server, port, secure: port === 465,
                requireTLS: port !== 465, auth: { user: smtp.smtp_user, pass: smtp.smtp_password },
                connectionTimeout: alert ? 3000 : 5000, greetingTimeout: 3000, socketTimeout: alert ? 4000 : 8000 })
        }
        async function boundedSend(mailer, message, milliseconds) {
            let timer
            try {
                return await Promise.race([mailer.sendMail(message), new Promise((_, reject) => {
                    timer = setTimeout(() => {
                        mailer.close()
                        reject(new Error('SMTP total timeout; delivery is uncertain'))
                    }, milliseconds)
                })])
            } finally { clearTimeout(timer) }
        }
        async function sendTracked(mailer, channel, message) {
            if (report[`${channel}_state`] === 'sent' || report[`${channel}_state`] === 'empty') return
            // Do not start an SMTP side effect unless there is time to record its result.
            if (deadline - now() < 13000) throw new Error('Koha e pamjaftueshme për SMTP; do të riprovohet.')
            await checkpoint('begin', channel)
            let result
            try {
                result = await boundedSend(mailer, message, 9000)
            } catch (error) {
                // Explicit server rejection is retryable. Connection loss after DATA is ambiguous.
                const rejected = ['EAUTH', 'EENVELOPE'].includes(error.code) ||
                    (Number(error.responseCode) >= 400 && Number(error.responseCode) < 600)
                const state = rejected ? 'failed' : 'uncertain'
                const detail = `SMTP ${channel}: ${error.code || 'ERROR'}${error.responseCode ? ' ' + error.responseCode : ''}`
                await checkpoint(state, channel, detail)
                throw new Error(detail)
            }
            if ((result.rejected || []).length || !(result.accepted || []).length) {
                await checkpoint('uncertain', channel, 'SMTP pranoi vetëm një pjesë ose asnjë marrës; kërkohet verifikim.')
                throw new Error('Dërgim i pjesshëm: kërkohet verifikim para riprovimit.')
            }
            await checkpoint('sent', channel)
            report[`${channel}_state`] = 'sent'
        }
        async function alertFailure(detail) {
            const to = splitEmails(env.REPORT_ALERT_TO)
            if (!to.length) throw new Error('REPORT_ALERT_TO mungon')
            const mailer = transport({ smtp_server: env.REPORT_ALERT_SMTP_HOST,
                smtp_port: env.REPORT_ALERT_SMTP_PORT, smtp_user: env.REPORT_ALERT_SMTP_USER,
                smtp_password: env.REPORT_ALERT_SMTP_PASSWORD }, true)
            try {
                const result = await boundedSend(mailer, { from: env.REPORT_ALERT_SMTP_USER, to,
                    subject: '[DËSHTIM] Raporti mujor i faturave',
                    text: `Raporti: ${report?.key || 'nuk u arrit backend-i'}\nFaza: ${stage}\nGabimi: ${detail}\n` +
                        'Kontrolloni historikun. Dështimet e sigurta riprovohen në kontrollin ditor; dërgimet e paqarta kërkojnë verifikim.' }, 6000)
                if (!(result.accepted || []).length || (result.rejected || []).length) throw new Error('Alert recipients rejected')
            } finally { mailer.close() }
        }
        try {
            if (!manual) {
                // Validate independent alert setup before starting an unattended report.
                if (!env.REPORT_ALERT_TO || !env.REPORT_ALERT_SMTP_HOST || !env.REPORT_ALERT_SMTP_USER || !env.REPORT_ALERT_SMTP_PASSWORD) {
                    throw new Error('Konfiguroni REPORT_ALERT_* në Vercel para aktivizimit të cron-it.')
                }
                if (!env.BACKEND_USERNAME || !env.BACKEND_PASSWORD) throw new Error('Mungojnë kredencialet e login-it automatik.')
                const token = await backend('/auth/login', { username: env.BACKEND_USERNAME, password: env.BACKEND_PASSWORD })
                if (!token.access_token) throw new Error('Backend nuk ktheu token.')
                auth = `Bearer ${token.access_token}`
            }
            stage = 'claim'
            report = await backend('/monthly-reports/claim', { manual,
                ...(manual ? { month: body.month, invoices_email: body.invoices_email, status_email: body.status_email } : {}) })
            if (report.skipped) return res.status(200).json({ ...report, invoices_email_sent: report.invoices_state === 'sent',
                status_email_sent: report.confirmation_state === 'sent', invoices_count: report.snapshot?.invoices?.length })
            stage = 'configuration'
            const company = await backend('/company')
            const smtp = manual ? { ...company, ...Object.fromEntries(Object.entries(body).filter(([k, v]) => k.startsWith('smtp_') && v)) } : company
            const list = report.snapshot.invoices
            const label = report.month
            const attachments = []
            stage = 'pdf'
            // Bounded parallelism avoids overwhelming a waking backend.
            let index = 0
            let attachmentBytes = 0
            await Promise.all(Array.from({ length: Math.min(3, list.length) }, async () => {
                while (index < list.length) {
                    const inv = list[index++]
                    const bytes = await backend(`/invoices/${inv.id}/pdf`, undefined, true)
                    attachmentBytes += bytes.length
                    if (attachmentBytes > 18 * 1024 * 1024) throw new Error('PDF-të tejkalojnë 18 MB; raporti kërkon ndarje në pjesë.')
                    attachments.push({ filename: `fatura-${inv.id}.pdf`, content: bytes })
                }
            }))
            const mailer = transport(smtp)
            const lines = list.map(i => `${i.invoice_number} - ${i.date}`).join('\n') || '(Nuk ka fatura.)'
            const from = { name: company.name || 'Holkos', address: smtp.smtp_user }
            try {
                stage = 'invoices'
                await sendTracked(mailer, 'invoices', { from, to: splitEmails(report.snapshot.invoices_email),
                    subject: `Faturat e muajit ${label} - ${company.name || 'Holkos'}`,
                    text: `Përshëndetje,\n\nFaturat e muajit ${label} (${list.length}):\n${lines}\n\nMe respekt,\n${company.name || 'Holkos'}`, attachments })
                stage = 'confirmation'
                await sendTracked(mailer, 'confirmation', { from, to: splitEmails(report.snapshot.status_email),
                    subject: `[${list.length ? 'SUKSES' : 'PA FATURA'}] Konfirmim — Faturat e muajit ${label}`,
                    text: `Raporti ${label}: ${list.length ? 'Faturat u pranuan nga serveri SMTP.' : 'Nuk ka fatura për këtë muaj.'}\n${lines}`, attachments })
            } finally { mailer.close() }
            stage = 'complete'
            await checkpoint('release')
            return res.status(200).json({ month: label, invoices_count: list.length,
                invoices_email: report.snapshot.invoices_email, status_email: report.snapshot.status_email,
                invoices_email_sent: report.invoices_state === 'sent', status_email_sent: report.confirmation_state === 'sent',
                status: list.length ? 'SUKSES' : 'PA FATURA' })
        } catch (error) {
            const detail = error.message || 'Raporti mujor dështoi.'
            log.error('monthly-report failed', { key: report?.key, stage, detail })
            if (report?.token && !report.skipped) {
                try { await checkpoint('release', undefined, `${stage}: ${detail}`) }
                catch { log.error('monthly-report ledger unavailable; lease recovery required') }
            }
            let alertSent = false
            // Unauthenticated manual calls must not be able to generate alert spam.
            if (!manual) {
                try { await alertFailure(detail); alertSent = true }
                catch { log.error('monthly-report independent alert failed; check REPORT_ALERT_* / SMTP') }
            }
            return res.status(error.status === 409 ? 409 : 503).json({ detail, alert_sent: alertSent })
        }
    }
}
