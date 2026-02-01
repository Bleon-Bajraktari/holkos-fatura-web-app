import smtplib
import os
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


class WebEmailService:
    @staticmethod
    def send_document(document, company, dest_email, pdf_path, is_offer=False):
        """Dërgon faturën ose ofertën me email (SMTP nga Cilësimet)"""
        if not dest_email:
            return False, "Adresa e email-it marrës nuk është caktuar."

        if not company or not company.smtp_user or not company.smtp_password:
            return False, "Cilësimet e email-it (SMTP) nuk janë konfiguruar në Cilësimet."
            
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
{company.phone or ''}
"""
            msg.attach(MIMEText(body, 'plain'))

            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename= {os.path.basename(pdf_path)}")
                msg.attach(part)

            text = msg.as_string()
            context = ssl.create_default_context()
            
            try:
                port = int(company.smtp_port or 587)
                if port == 465:
                    server = smtplib.SMTP_SSL(company.smtp_server or "smtp.gmail.com", 465, context=context, timeout=15)
                else:
                    server = smtplib.SMTP(company.smtp_server or "smtp.gmail.com", port, timeout=15)
                    server.starttls(context=context)
                
                server.login(company.smtp_user, company.smtp_password)
                server.sendmail(company.smtp_user, dest_email, text)
                server.quit()
                return True, "Email u dërgua me sukses!"
            except Exception as e:
                return False, f"Gabim SMTP: {str(e)}"

        except Exception as e:
            return False, f"Gabim gjatë përgatitjes: {str(e)}"

    @staticmethod
    def send_bulk_documents(documents, company, dest_email, pdf_paths, is_offer=False):
        """Dërgon disa fatura ose oferta me një email të vetëm"""
        if not dest_email:
            return False, "Adresa e email-it marrës nuk është caktuar."

        if not company or not company.smtp_user or not company.smtp_password:
            return False, "Cilësimet e email-it (SMTP) nuk janë konfiguruar në Cilësimet."

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

            for pdf_path in (pdf_paths or []):
                if pdf_path and os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as attachment:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename= {os.path.basename(pdf_path)}")
                    msg.attach(part)

            text = msg.as_string()
            context = ssl.create_default_context()

            try:
                port = int(company.smtp_port or 587)
                if port == 465:
                    server = smtplib.SMTP_SSL(company.smtp_server or "smtp.gmail.com", 465, context=context, timeout=15)
                else:
                    server = smtplib.SMTP(company.smtp_server or "smtp.gmail.com", port, timeout=15)
                    server.starttls(context=context)

                server.login(company.smtp_user, company.smtp_password)
                server.sendmail(company.smtp_user, dest_email, text)
                server.quit()
                return True, "Email u dërgua me sukses!"
            except Exception as e:
                return False, f"Gabim SMTP: {str(e)}"

        except Exception as e:
            return False, f"Gabim gjatë përgatitjes: {str(e)}"
