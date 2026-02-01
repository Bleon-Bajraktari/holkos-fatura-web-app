/**
 * Vercel Serverless Function - Dërgon bulk email (disa fatura/oferta) me SMTP nga Cilësimet.
 * Render bllokon SMTP, ndaj bulk-email bëhet nga Vercel.
 */
import nodemailer from 'nodemailer'

const BACKEND_URL = (process.env.BACKEND_URL || 'https://holkos-fatura-api.onrender.com').replace(/\/$/, '')

export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ detail: 'Method not allowed' })
    }
    try {
        const {
            dest_email,
            document_type,
            document_ids,
            smtp_server,
            smtp_port,
            smtp_user,
            smtp_password,
            company_name
        } = req.body

        if (!dest_email || !smtp_user || !smtp_password) {
            return res.status(400).json({
                detail: 'Mungojnë: dest_email, smtp_user ose smtp_password nga Cilësimet.'
            })
        }
        const ids = Array.isArray(document_ids) ? document_ids : []
        if (ids.length === 0) {
            return res.status(400).json({ detail: 'Zgjidhni të paktën një dokument.' })
        }

        const isOffer = document_type === 'offer'
        const basePath = isOffer ? 'offers' : 'invoices'
        const numKey = isOffer ? 'offer_number' : 'invoice_number'
        const results = await Promise.all(ids.map(async (id) => {
            let docNum = String(id)
            let docDate = ''
            let pdfBuffer = null
            const [docRes, pdfRes] = await Promise.all([
                fetch(`${BACKEND_URL}/${basePath}/${id}`),
                fetch(`${BACKEND_URL}/${basePath}/${id}/pdf`, { headers: { Accept: 'application/pdf' } })
            ])
            if (docRes.ok) {
                const doc = await docRes.json()
                const raw = String(doc[numKey] || '')
                const nrMatch = raw.match(/NR\.\s*(\d+)/i) || raw.match(/(\d+)/)
                docNum = nrMatch ? nrMatch[1] : raw || docNum
                if (doc.date) {
                    const d = new Date(doc.date)
                    docDate = d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
                }
            }
            if (pdfRes.ok) {
                const arrayBuffer = await pdfRes.arrayBuffer()
                pdfBuffer = Buffer.from(arrayBuffer)
            }
            return { docNum, docDate, pdfBuffer, id }
        }))
        const docLabel = isOffer ? 'Oferta' : 'Faturat'
        const docLines = results.map(r => `${isOffer ? 'Ofertë' : 'Fatura'} nr. ${r.docNum} - ${r.docDate}`)
        const attachments = results.filter(r => r.pdfBuffer).map(r => ({
            filename: `${isOffer ? 'oferta' : 'fatura'} nr.${r.docNum}.pdf`,
            content: r.pdfBuffer
        }))

        const port = parseInt(smtp_port || '587', 10)
        const secure = port === 465
        const transporter = nodemailer.createTransport({
            host: smtp_server || 'smtp.gmail.com',
            port,
            secure,
            auth: { user: smtp_user, pass: smtp_password },
            requireTLS: port === 587,
            connectionTimeout: 15000,
            greetingTimeout: 10000
        })

        const bodyText = docLines.join('\n')

        const mailOptions = {
            from: `"${(company_name || 'Holkos').replace(/"/g, '')}" <${smtp_user}>`,
            to: dest_email,
            subject: `${docLabel} - ${(company_name || 'Holkos').replace(/"/g, '')}`,
            text: bodyText,
            attachments
        }

        await transporter.sendMail(mailOptions)
        return res.status(200).json({ message: 'Email u dërgua me sukses!', success: ids.length, failed: 0, errors: [] })
    } catch (error) {
        console.error('SMTP bulk error:', error)
        return res.status(500).json({
            detail: error.message || 'Gabim gjatë dërgimit të email-it.'
        })
    }
}
