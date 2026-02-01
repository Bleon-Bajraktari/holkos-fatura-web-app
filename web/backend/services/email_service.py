import smtplib
import os
import ssl
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


def _send_via_resend(document_or_docs, company, dest_email, pdf_paths, is_offer=False):
    """
    Dërgon email me Resend API (funksionon në Render free tier - SMTP është i bllokuar).
    """
    api_key = os.getenv("RESEND_API_KEY")
    from_addr = (
        os.getenv("RESEND_FROM")
        or (company.smtp_user if company and company.smtp_user else None)
        or "onboarding@resend.dev"
    )
    if not api_key:
        return False, "Vendos RESEND_API_KEY në Render Environment."
    try:
        import resend
        resend.api_key = api_key
    except ImportError:
        return False, "Instalo resend: pip install resend"

    # Format from: "Company Name <email@domain.com>"
    company_name = (company and company.name) or "Holkos"
    from_str = from_addr if "<" in from_addr else f"{company_name} <{from_addr}>"

    if isinstance(pdf_paths, str):
        pdf_paths = [pdf_paths]
    docs = document_or_docs if isinstance(document_or_docs, list) else [document_or_docs]

    doc_type = "Ofertë" if is_offer else "Faturë"
    doc_type_pl = "Oferta" if is_offer else "Faturat"

    if len(docs) == 1:
        doc = docs[0]
        doc_number = doc.offer_number if is_offer else doc.invoice_number
        subject = f"{doc_type} e re: {doc_number} - {company.name}"
        body = f"""
I/E dashur klient,

Ju lutem gjeni të bashkëngjitur {doc_type.lower()}n tuaj të re me numër {doc_number}.

Detajet:
- Numri: {doc_number}
- Data: {doc.date.strftime('%d.%m.%Y')}
- Totali: {float(doc.total):,.2f} €

Ju faleminderit për bashkëpunimin!

Me respekt,
{company.name}
{company.phone or ''}
"""
    else:
        subject = f"{doc_type_pl} - {company.name}"
        lines = [
            f"{doc.offer_number if is_offer else doc.invoice_number} - {doc.date.strftime('%d.%m.%Y')}"
            for doc in docs
        ]
        body = "\n".join(lines)

    attachments = []
    for pdf_path in pdf_paths:
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                attachments.append({
                    "filename": os.path.basename(pdf_path),
                    "content": base64.b64encode(f.read()).decode("utf-8"),
                })

    params = {
        "from": from_str,
        "to": [dest_email],
        "subject": subject,
        "text": body.strip(),
    }
    if attachments:
        params["attachments"] = attachments

    try:
        resend.Emails.send(params)
        return True, "Email u dërgua me sukses!"
    except Exception as e:
        return False, f"Gabim Resend: {str(e)}"


class WebEmailService:
    @staticmethod
    def send_document(document, company, dest_email, pdf_path, is_offer=False):
        """Dërgon faturën ose ofertën me email"""
        if not dest_email:
            return False, "Adresa e email-it marrës nuk është caktuar."

        # Resend API (funksionon në Render free tier - SMTP bllokohet)
        if os.getenv("RESEND_API_KEY"):
            return _send_via_resend(document, company, dest_email, pdf_path, is_offer)

        if not company or not company.smtp_user or not company.smtp_password:
            return False, "Cilësimet e email-it (SMTP) nuk janë konfiguruar. Ose vendos RESEND_API_KEY në Render."
            
        doc_type = "Ofertë" if is_offer else "Faturë"
        doc_number = document.offer_number if is_offer else document.invoice_number
        
        try:
            msg = MIMEMultipart()
            msg['From'] = f"{company.name} <{company.smtp_user}>"
            msg['To'] = dest_email
            msg['Subject'] = f"{doc_type} e re: {doc_number} - {company.name}"

            body = f"""
I/E dashur klient,

Ju lutem gjeni të bashkëngjitur {doc_type.lower()}n tuaj të re me numër {doc_number}.

Detajet:
- Numri: {doc_number}
- Data: {document.date.strftime('%d.%m.%Y')}
- Totali: {float(document.total):,.2f} €

Ju faleminderit për bashkëpunimin!

Me respekt,
{company.name}
{company.phone}
"""
            msg.attach(MIMEText(body, 'plain'))

            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename= {os.path.basename(pdf_path)}")
                msg.attach(part)

            text = msg.as_string()
            context = ssl.create_default_context()
            
            try:
                if int(company.smtp_port) == 465:
                    server = smtplib.SMTP_SSL(company.smtp_server, 465, context=context, timeout=15)
                else:
                    server = smtplib.SMTP(company.smtp_server, company.smtp_port, timeout=15)
                    server.starttls(context=context)
                
                server.login(company.smtp_user, company.smtp_password)
                server.sendmail(company.smtp_user, dest_email, text)
                server.quit()
                return True, "Email u dërgua me sukses!"
            except Exception as e:
                return False, f"Gabim SMTP: {str(e)}. Render free tier bllokon SMTP - përdor Resend (shiko DEPLOY.md)."

        except Exception as e:
            return False, f"Gabim gjatë përgatitjes: {str(e)}"

    @staticmethod
    def send_bulk_documents(documents, company, dest_email, pdf_paths, is_offer=False):
        """Dërgon disa fatura ose oferta me një email të vetëm"""
        if not dest_email:
            return False, "Adresa e email-it marrës nuk është caktuar."

        if os.getenv("RESEND_API_KEY"):
            return _send_via_resend(documents, company, dest_email, pdf_paths, is_offer)

        if not company or not company.smtp_user or not company.smtp_password:
            return False, "Cilësimet e email-it (SMTP) nuk janë konfiguruar. Ose vendos RESEND_API_KEY në Render."

        try:
            msg = MIMEMultipart()
            msg['From'] = f"{company.name} <{company.smtp_user}>"
            msg['To'] = dest_email
            doc_type = "Oferta" if is_offer else "Faturat"
            msg['Subject'] = f"{doc_type} - {company.name}"

            lines = [
                f"{doc.offer_number if is_offer else doc.invoice_number} - {doc.date.strftime('%d.%m.%Y')}"
                for doc in documents
            ]
            body = "\n".join(lines)
            msg.attach(MIMEText(body, 'plain'))

            for pdf_path in pdf_paths:
                if os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as attachment:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename= {os.path.basename(pdf_path)}")
                    msg.attach(part)

            text = msg.as_string()
            context = ssl.create_default_context()

            try:
                if int(company.smtp_port) == 465:
                    server = smtplib.SMTP_SSL(company.smtp_server, 465, context=context, timeout=15)
                else:
                    server = smtplib.SMTP(company.smtp_server, company.smtp_port, timeout=15)
                    server.starttls(context=context)

                server.login(company.smtp_user, company.smtp_password)
                server.sendmail(company.smtp_user, dest_email, text)
                server.quit()
                return True, "Email u dërgua me sukses!"
            except Exception as e:
                return False, f"Gabim SMTP: {str(e)}. Render free tier bllokon SMTP - përdor Resend (shiko DEPLOY.md)."

        except Exception as e:
            return False, f"Gabim gjatë përgatitjes: {str(e)}"
