import test from 'node:test'
import assert from 'node:assert/strict'
import { createMonthlyHandler } from '../app/lib/monthly-report.js'

function fixture(options = {}) {
    const calls = [], sent = []
    const env = { CRON_SECRET: 'test', BACKEND_USERNAME: 'test', BACKEND_PASSWORD: 'test',
        REPORT_ALERT_TO: 'alert@example.test', REPORT_ALERT_SMTP_HOST: 'alert.test',
        REPORT_ALERT_SMTP_USER: 'sender@example.test', REPORT_ALERT_SMTP_PASSWORD: 'test' }
    const report = { key: 'monthly:2026-09', month: '2026-09', token: 'lease',
        invoices_state: options.invoiceState || 'pending', confirmation_state: 'pending',
        snapshot: { invoices_email: 'invoices@example.test', status_email: 'status@example.test',
            invoices: [{ id: 1, invoice_number: 'NR.1', date: '2026-09-01' }] } }
    const handler = createMonthlyHandler({ env, log: { error() {} },
        fetchImpl: async (url, init) => {
            const path = new URL(url).pathname
            const data = init.body && JSON.parse(init.body)
            calls.push({ path, data })
            if (options.offline) throw new Error('backend unavailable')
            let value = {}
            if (path === '/auth/login') value = { access_token: 'jwt' }
            if (path === '/monthly-reports/claim') value = options.skipped ? { skipped: true } : report
            if (path === '/company') value = { name: 'Test', smtp_server: 'smtp.test', smtp_user: 'sender@example.test', smtp_password: 'test' }
            if (path.endsWith('/pdf')) return new Response(options.badPdf ? '<html>error</html>' : '%PDF-test')
            if (options.checkpointFails && data?.action === 'sent') return new Response('', { status: 503 })
            return Response.json(value)
        },
        createTransport: config => ({ close() {}, sendMail: async message => {
            sent.push({ host: config.host, message })
            if (config.host !== 'alert.test' && options.reject) {
                const error = new Error('SMTP rejected'); error.responseCode = 535; error.code = 'EAUTH'; throw error
            }
            return { accepted: message.to, rejected: options.partial && config.host !== 'alert.test' ? ['one@example.test'] : [] }
        } })
    })
    const response = { statusCode: 0, body: null, status(code) { this.statusCode = code; return this }, json(body) { this.body = body; return this } }
    return { calls, sent, response, run: (headers = { authorization: 'Bearer test' }) => handler({ method: 'GET', headers }, response) }
}

test('backend unavailable sends independent alert and returns failure', async () => {
    const f = fixture({ offline: true }); await f.run()
    assert.equal(f.response.statusCode, 503)
    assert.equal(f.sent[0].host, 'alert.test')
    assert.equal(f.response.body.alert_sent, true)
})
test('success checkpoints each channel before completion', async () => {
    const f = fixture(); await f.run()
    assert.equal(f.response.statusCode, 200)
    assert.equal(f.sent.length, 2)
    assert.deepEqual(f.calls.filter(c => c.data?.action).map(c => c.data.action), ['begin', 'sent', 'begin', 'sent', 'release'])
})
test('confirmation retry does not resend invoices', async () => {
    const f = fixture({ invoiceState: 'sent' }); await f.run()
    assert.equal(f.sent.length, 1)
    assert.deepEqual(f.sent[0].message.to, ['status@example.test'])
})
test('already completed report sends nothing', async () => {
    const f = fixture({ skipped: true }); await f.run()
    assert.equal(f.sent.length, 0)
    assert.equal(f.response.statusCode, 200)
})
test('missing PDF aborts before any invoice mail', async () => {
    const f = fixture({ badPdf: true }); await f.run()
    assert.equal(f.response.statusCode, 503)
    assert.ok(f.sent.every(s => s.host === 'alert.test'))
})
test('SMTP rejection is recorded and returns non-200', async () => {
    const f = fixture({ reject: true }); await f.run()
    assert.equal(f.response.statusCode, 503)
    assert.ok(f.calls.some(c => c.data?.action === 'failed'))
})
test('partial delivery is uncertain and not reported successful', async () => {
    const f = fixture({ partial: true }); await f.run()
    assert.equal(f.response.statusCode, 503)
    assert.ok(f.calls.some(c => c.data?.action === 'uncertain'))
})
test('checkpoint failure does not send confirmation or repeat SMTP', async () => {
    const f = fixture({ checkpointFails: true }); await f.run()
    assert.equal(f.sent.filter(s => s.host === 'smtp.test').length, 1)
    assert.equal(f.response.statusCode, 503)
})
test('unauthorized cron cannot send alerts or query backend', async () => {
    const f = fixture(); await f.run({})
    assert.equal(f.response.statusCode, 401)
    assert.equal(f.calls.length, 0)
    assert.equal(f.sent.length, 0)
})
