/**
 * Vercel Serverless Function - Dërgon email me SMTP nga Cilësimet (company)
 * Përdor të dhënat SMTP nga Cilësimet (Gmail, Outlook, etj.) - Vercel lejon SMTP (jo portën 25)
 */
const nodemailer = require('nodemailer')

const BACKEND_URL = (process.env.BACKEND_URL || 'https://holkos-fatura-api.onrender.com').replace(/\/$/, '')

export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ detail: 'Method not allowed' })
    }
    try {
        const {
            dest_email,
            document_type,
            document_id,
            smtp_server,
            smtp_port,
            smtp_user,
            smtp_password,
            company_name,
            doc_number,
            doc_date,
            doc_total,
            subject
        } = req.body

        if (!dest_email || !smtp_user || !smtp_password) {
            return res.status(400).json({
                detail: 'Mungojnë: dest_email, smtp_user ose smtp_password nga Cilësimet.'
            })
        }

        const isOffer = document_type === 'offer'
        const pdfPath = isOffer ? `offers/${document_id}/pdf` : `invoices/${document_id}/pdf`
        const pdfUrl = `${BACKEND_URL}/${pdfPath}`

        let pdfBuffer = null
        try {
            const pdfRes = await fetch(pdfUrl, { headers: { 'Accept': 'application/pdf' } })
            if (pdfRes.ok) {
                const arrayBuffer = await pdfRes.arrayBuffer()
                pdfBuffer = Buffer.from(arrayBuffer)
            }
        } catch (e) {
            console.error('PDF fetch error:', e.message)
        }

        const port = parseInt(smtp_port || '587', 10)
        const secure = port === 465
        const transporter = nodemailer.createTransport({
            host: smtp_server || 'smtp.gmail.com',
            port,
            secure,
            auth: {
                user: smtp_user,
                pass: smtp_password
            }
        })

        const docType = isOffer ? 'Ofertë' : 'Faturë'
        const bodyText = doc_number
            ? `I/E dashur klient,

Ju lutem gjeni të bashkëngjitur ${docType.toLowerCase()}n tuaj të re me numër ${doc_number}.

Detajet:
- Numri: ${doc_number}
- Data: ${doc_date || ''}
- Totali: ${doc_total || ''} €

Ju faleminderit për bashkëpunimin!

Me respekt,
${company_name || 'Holkos'}`
            : `Dokumenti i bashkëngjitur.`

        const mailOptions = {
            from: `"${(company_name || 'Holkos').replace(/"/g, '')}" <${smtp_user}>`,
            to: dest_email,
            subject: subject || `${docType} - ${company_name || 'Holkos'}`,
            text: bodyText
        }
        if (pdfBuffer) {
            mailOptions.attachments = [{
                filename: `Dokumenti_${doc_number || document_id}.pdf`,
                content: pdfBuffer
            }]
        }

        await transporter.sendMail(mailOptions)
        return res.status(200).json({ message: 'Email u dërgua me sukses!' })
    } catch (error) {
        console.error('SMTP error:', error)
        return res.status(500).json({
            detail: error.message || 'Gabim gjatë dërgimit të email-it.'
        })
    }
}
