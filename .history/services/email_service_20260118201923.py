"""
Shërbimi për dërgimin e email-eve - v1.0.0
"""
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from models.company import Company

class EmailService:
    @staticmethod
    def send_invoice(invoice, dest_email, pdf_path, is_to_company=True):
        """Dërgon faturën me email te kompania ose klienti"""
        company = Company()
        if not company.load():
            return False, "Nuk u ngarkuan të dhënat e kompanisë."
            
        if not company.smtp_user or not company.smtp_password:
            return False, "Cilësimet e email-it (SMTP) nuk janë konfiguruar në Cilësime."
            
        if not dest_email:
            return False, "Adresa e email-it marrës nuk është caktuar."
            
        try:
            # Krijo mesazhin
            msg = MIMEMultipart()
            msg['From'] = f"{company.name} <{company.smtp_user}>"
            msg['To'] = dest_email
            msg['Subject'] = f"Faturë e re: {invoice.invoice_number} - {company.name}"

            if is_to_company:
                body = f"""
Pershendetje Holkos,

Kjo është një faturë e re e sapo gjeneruar nga sistemi.

Detajet:
- Numri: {invoice.invoice_number}
- Data: {invoice.date.strftime('%d.%m.%Y')}
- Klienti: {invoice.client_name if hasattr(invoice, 'client_name') else 'I specifikuar ne PDF'}
- Totali: {float(invoice.total):,.2f} €

Skedari PDF është i bashkëngjitur.
"""
            else:
                body = f"""
I/E dashur klient,

Ju lutem gjeni të bashkëngjitur faturën tuaj të re me numër {invoice.invoice_number}.

Detajet e faturës:
- Numri: {invoice.invoice_number}
- Data: {invoice.date.strftime('%d.%m.%Y')}
- Totali: {float(invoice.total):,.2f} €

Ju faleminderit për bashkëpunimin!

Me respekt,
{company.name}
{company.phone}
"""
            msg.attach(MIMEText(body, 'plain'))

            # Bashkëngjit PDF
            with open(pdf_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {os.path.basename(pdf_path)}",
            )
            msg.attach(part)

            # Dërgo email
            # Dërgo email
            # Përdor SSL direkt (Port 465) nëse porti është 465
            if int(company.smtp_port) == 465:
                server = smtplib.SMTP_SSL(company.smtp_server, company.smtp_port)
            else:
                server = smtplib.SMTP(company.smtp_server, company.smtp_port)
                server.starttls()

            server.login(company.smtp_user, company.smtp_password)
            text = msg.as_string()
            server.sendmail(company.smtp_user, dest_email, text)
            server.quit()
            
            return True, "Email u dërgua me sukses!"
        except Exception as e:
            return False, f"Gabim gjatë dërgimit: {str(e)}"

    @staticmethod
    def send_bulk_invoices(invoice_pdf_pairs, dest_email):
        """
        Dërgon shumë fatura në një email të vetëm.
        invoice_pdf_pairs: List e tuples (invoice, pdf_path)
        """
        company = Company()
        if not company.load():
            return False, "Nuk u ngarkuan të dhënat e kompanisë."
            
        if not company.smtp_user or not company.smtp_password:
            return False, "Cilësimet e email-it (SMTP) nuk janë konfiguruar."
            
        try:
            msg = MIMEMultipart()
            msg['From'] = f"{company.name} <{company.smtp_user}>"
            msg['To'] = dest_email
            msg['Subject'] = f"Faturat ({len(invoice_pdf_pairs)}) - {company.name}"

            # Ndërto trupin e email-it vetëm me data dhe numra
            body_lines = []
            for inv, _ in invoice_pdf_pairs:
                date_str = inv.date.strftime('%d.%m.%Y')
                line = f"{date_str} - {inv.invoice_number}"
                body_lines.append(line)
            
            body = "\n".join(body_lines)
            msg.attach(MIMEText(body, 'plain'))

            # Bashkëngjit të gjitha PDF-të
            for inv, pdf_path in invoice_pdf_pairs:
                if os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as attachment:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    filename = f"{inv.invoice_number}.pdf"
                    # Pastro filename nga karaktere të palejueshme nëse ka
                    filename = "".join([c for c in filename if c.isalnum() or c in (' ', '.', '-', '_')])
                    
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename= {filename}",
                    )
                    msg.attach(part)

            # Dërgo email
            # Dërgo email
            # Përdor SSL direkt (Port 465) nëse porti është 465
            if int(company.smtp_port) == 465:
                server = smtplib.SMTP_SSL(company.smtp_server, company.smtp_port)
            else:
                server = smtplib.SMTP(company.smtp_server, company.smtp_port)
                server.starttls()

            server.login(company.smtp_user, company.smtp_password)
            text = msg.as_string()
            server.sendmail(company.smtp_user, dest_email, text)
            server.quit()
            
            return True, "Email u dërgua me sukses!"

        except Exception as e:
            return False, f"Gabim gjatë dërgimit: {str(e)}"
