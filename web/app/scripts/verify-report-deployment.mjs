import nodemailer from 'nodemailer'

// Production secrets are intentionally unavailable to `vercel env pull`.
// Validate them in the deployment environment without logging their values.
if (process.env.VERCEL_ENV === 'production') {
    const env = process.env
    for (const key of ['BACKEND_USERNAME', 'BACKEND_PASSWORD', 'CRON_SECRET', 'REPORT_ALERT_TO',
        'REPORT_ALERT_SMTP_HOST', 'REPORT_ALERT_SMTP_USER', 'REPORT_ALERT_SMTP_PASSWORD']) {
        if (!env[key]) throw new Error(`Missing production configuration: ${key}`)
    }
    const base = (env.BACKEND_URL || 'https://holkos-fatura-api.onrender.com').replace(/\/$/, '')
    async function request(path, options = {}) {
        const response = await fetch(base + path, { ...options, signal: AbortSignal.timeout(90000) })
        if (!response.ok) throw new Error(`Report readiness ${path}: HTTP ${response.status}`)
        return response
    }
    const login = await (await request('/auth/login', { method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: env.BACKEND_USERNAME, password: env.BACKEND_PASSWORD })
    })).json()
    if (!login.access_token) throw new Error('Report readiness: login returned no token')
    console.log('Report readiness: production login OK')
    const headers = { Authorization: `Bearer ${login.access_token}` }
    const history = await (await request('/monthly-reports/history', { headers })).json()
    if (!Array.isArray(history)) throw new Error('Report readiness: invalid ledger response')
    console.log('Report readiness: authenticated history OK')
    const invoices = await (await request('/invoices', { headers })).json()
    if (!Array.isArray(invoices)) throw new Error('Report readiness: invalid invoice response')
    if (invoices.length) {
        const pdf = Buffer.from(await (await request(`/invoices/${invoices[0].id}/pdf`, { headers })).arrayBuffer())
        if (pdf.subarray(0, 5).toString() !== '%PDF-') throw new Error('Report readiness: invalid PDF')
        console.log('Report readiness: real invoice PDF OK')
    }
    const port = Number(env.REPORT_ALERT_SMTP_PORT || 587)
    const mailer = nodemailer.createTransport({ host: env.REPORT_ALERT_SMTP_HOST, port, secure: port === 465,
        requireTLS: port !== 465, auth: { user: env.REPORT_ALERT_SMTP_USER, pass: env.REPORT_ALERT_SMTP_PASSWORD },
        connectionTimeout: 10000, greetingTimeout: 10000, socketTimeout: 15000 })
    try {
        await mailer.verify()
        console.log('Report readiness: independent SMTP authentication OK')
        // Explicit one-time deployment test only. Never attaches invoices or mails clients.
        if (env.REPORT_DEPLOY_SMOKE_TEST === '1') {
            const to = env.REPORT_ALERT_TO.split(/[;,]/).map(value => value.trim()).filter(Boolean)
            const result = await mailer.sendMail({ from: env.REPORT_ALERT_SMTP_USER, to,
                subject: '[TEST] Verifikimi i njoftimeve Holkos Fatura',
                text: 'Ky është një test i kontrolluar i konfigurimit pas publikimit. Login-i i backend-it, historiku dhe PDF-ja u verifikuan. Ky email nuk përmban fatura dhe nuk është raporti mujor.' })
            if (!(result.accepted || []).length || (result.rejected || []).length) throw new Error('Report readiness: test recipients not fully accepted')
            console.log('Report readiness: one-time test email accepted by SMTP')
        }
    } finally { mailer.close() }
}
