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
    def send_invoice(invoice, client_email, pdf_path):
        """Dërgon faturën me email te klienti"""
        company = Company()
        if not company.load():
            return False, "Nuk u ngarkuan të dhënat e kompanisë."
            
        if not company.smtp_user or not company.smtp_password:
            return False, "Cilësimet e email-it (SMTP) nuk janë konfiguruar në Cilësime."
            
        if not client_email:
            return False, "Klienti nuk ka një adresë email."
            
        if not os.path.exists(pdf_path):
            return False, "Skedari PDF nuk u gjet."

        try:
            # Krijo mesazhin
            msg = MIMEMultipart()
            msg['From'] = f"{company.name} <{company.smtp_user}>"
            msg['To'] = client_email
            msg['Subject'] = f"Faturë e re: {invoice.invoice_number} - {company.name}"

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
            server = smtplib.SMTP(company.smtp_server, company.smtp_port)
            server.starttls()
            server.login(company.smtp_user, company.smtp_password)
            text = msg.as_string()
            server.sendmail(company.smtp_user, client_email, text)
            server.quit()
            
            return True, "Email u dërgua me sukses!"
        except Exception as e:
            return False, f"Gabim gjatë dërgimit: {str(e)}"
