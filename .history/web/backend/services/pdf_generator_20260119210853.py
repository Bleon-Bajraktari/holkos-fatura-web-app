import os
import tempfile
import atexit
from decimal import Decimal
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, Image
)
from PIL import Image as PILImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# We'll use absolute paths or relative to the backend project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
os.makedirs(EXPORTS_DIR, exist_ok=True)

class WebPDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_styles()
    
    def setup_styles(self):
        """Konfiguron stilet për PDF sipas desktop app"""
        self.title_style = ParagraphStyle(
            "title", fontSize=24, alignment=TA_CENTER, fontName="Helvetica-Bold"
        )
        self.subtitle_style = ParagraphStyle(
            "subtitle", fontSize=13, alignment=TA_CENTER, fontName="Helvetica"
        )
        self.bold_style = ParagraphStyle(
            "bold", fontSize=11, fontName="Helvetica-Bold"
        )
        self.normal_style = ParagraphStyle(
            "normal", fontSize=11
        )
        self.right_style = ParagraphStyle(
            "right", fontSize=11, alignment=TA_RIGHT
        )
        self.note_style = ParagraphStyle(
            "note", fontSize=10, fontName="Helvetica-Oblique", alignment=TA_LEFT, leftIndent=0
        )

    def format_number(self, number, with_currency=False):
        """Formaton numrin me hapesire si separator dhe presje per decimale"""
        if isinstance(number, (Decimal, float)):
            formatted = f"{float(number):,.2f}".replace(",", " ").replace(".", ",")
            return f"{formatted} €" if with_currency else formatted
        return str(number)

    def format_date(self, date_obj):
        if date_obj:
            if isinstance(date_obj, str):
                try:
                    date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
                except: pass
            return date_obj.strftime("%d.%m.%Y")
        return ""

    def process_logo(self, logo_path, logo_height=32*mm):
        """Perpunon logon duke hequr pjeset e bardha (portuar nga desktop)"""
        if not logo_path or not os.path.exists(logo_path):
            return None, 0
            
        try:
            pil_img = PILImage.open(logo_path)
            if pil_img.mode != 'RGBA':
                pil_img = pil_img.convert('RGBA')
            
            bbox = pil_img.getbbox()
            if not bbox or bbox == (0, 0, pil_img.width, pil_img.height):
                rgb_img = pil_img.convert('RGB')
                width, height = rgb_img.size
                left, top, right, bottom = width, height, 0, 0
                found_content = False
                for y in range(height):
                    for x in range(width):
                        r, g, b = rgb_img.getpixel((x, y))
                        if not (r >= 250 and g >= 250 and b >= 250):
                            top = y
                            found_content = True
                            break
                    if found_content: break
                
                if found_content:
                    found_content = False
                    for y in range(height - 1, top - 1, -1):
                        for x in range(width):
                            r, g, b = rgb_img.getpixel((x, y))
                            if not (r >= 250 and g >= 250 and b >= 250):
                                bottom = y
                                found_content = True
                                break
                        if found_content: break
                    left = width
                    right = 0
                    for y in range(top, bottom + 1):
                        for x in range(width):
                            r, g, b = rgb_img.getpixel((x, y))
                            if not (r >= 250 and g >= 250 and b >= 250):
                                left = min(left, x)
                                right = max(right, x)
                    if left < width and right >= left:
                        bbox = (left, top, right + 1, bottom + 1)
                        pil_img = pil_img.crop(bbox)
            elif bbox:
                pil_img = pil_img.crop(bbox)
            
            img_width, img_height = pil_img.size
            aspect_ratio = img_width / img_height
            logo_width = logo_height * aspect_ratio
            if logo_width > 50*mm:
                logo_width = 50*mm
                logo_height = logo_width / aspect_ratio
            
            temp_logo = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            pil_img.save(temp_logo.name, 'PNG')
            path = temp_logo.name
            temp_logo.close()
            
            atexit.register(lambda: os.unlink(path) if os.path.exists(path) else None)
            return Image(path, logo_width, logo_height), logo_height
        except:
            return None, 0

    def generate_invoice_pdf(self, invoice, company, client):
        filename = f"Fatura_{invoice.invoice_number.replace(' ', '_')}_{invoice.date.year if hasattr(invoice.date, 'year') else datetime.now().year}.pdf"
        filepath = os.path.join(EXPORTS_DIR, filename)
        
        doc = SimpleDocTemplate(
            filepath, pagesize=A4,
            leftMargin=15*mm, rightMargin=15*mm, topMargin=12*mm, bottomMargin=12*mm
        )
        
        story = []
        
        # Title
        inv_num = invoice.invoice_number.upper()
        if "NR." in inv_num: inv_num = inv_num.split("NR.")[-1].strip()
        year = invoice.date.year if hasattr(invoice.date, 'year') else datetime.now().year
        story.append(Paragraph(f"FATURË {inv_num}/{year}", self.title_style))
        story.append(Spacer(1, 6*mm))
        story.append(Paragraph(f"Data: {self.format_date(invoice.date)}", self.subtitle_style))
        story.append(Spacer(1, 15*mm))
        
        # Header (Company & Client)
        logo_img, logo_h = self.process_logo(company.logo_path)
        company_data = [
            [logo_img] if logo_img else [Paragraph(f"<b>{company.name}</b>", self.bold_style)],
            [Paragraph("Fasada ventiluese", self.normal_style)],
            [Paragraph(f"Tel: {company.phone}", self.normal_style)],
            [Paragraph(company.email, self.normal_style)],
            [Paragraph(company.address, self.normal_style)],
            [Paragraph(f"Numër unik: {company.unique_number}", self.normal_style)],
            [Paragraph(f"Numër fiskal: {company.fiscal_number}", self.normal_style)],
            [Paragraph(f"<b>Llogaria: NLB {company.account_nib}</b>", self.bold_style)]
        ]
        company_table = Table(company_data, colWidths=[100*mm])
        company_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (0, 0), 10),
        ]))

        buyer_style = ParagraphStyle("buyer", fontSize=11, alignment=TA_RIGHT)
        buyer_bold_style = ParagraphStyle("buyer_bold", fontSize=12, fontName="Helvetica-Bold", alignment=TA_RIGHT)
        
        buyer_data = [
            [Spacer(1, logo_h if logo_h > 0 else 10*mm)],
            [Paragraph("<b>BLERESI</b>", buyer_bold_style)],
            [Paragraph(f"Emri: {client.name}", buyer_style)],
            [Paragraph(f"Adresa: {client.address or ''}", buyer_style)],
            [Paragraph(f"Numër unik: {client.unique_number or ''}", buyer_style)],
        ]
        buyer_table = Table(buyer_data, colWidths=[90*mm])
        buyer_table.setStyle(TableStyle([
            ("BOX", (0, 1), (-1, -1), 1, colors.black),
            ("LINEBELOW", (0, 1), (-1, 1), 1, colors.black),
            ("BACKGROUND", (0, 1), (-1, 1), colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 1), (-1, 1), 6),
            ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
        ]))
        
        header_container = Table([[company_table, buyer_table]], colWidths=[100*mm, 90*mm])
        header_container.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
        story.append(header_container)
        story.append(Spacer(1, 12*mm))

        # Payment Due Date
        if invoice.payment_due_date:
            due_data = [["AFATI I PAGESËS"], [self.format_date(invoice.payment_due_date)]]
            due_table = Table(due_data, colWidths=[60*mm])
            due_table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(Table([[due_table]], colWidths=[180*mm], style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]))
            story.append(Spacer(1, 10*mm))
        
        # Items Table
        items_data = [["PERSHKRIMI", "M²", "CMIMI", "NENTOTALI"]]
        for item in invoice.items:
            items_data.append([
                item.description,
                self.format_number(item.quantity),
                self.format_number(item.unit_price, True),
                self.format_number(item.quantity * item.unit_price, True)
            ])
        while len(items_data) < 6: items_data.append(["", "", "", ""])
            
        items_table = Table(items_data, colWidths=[85*mm, 25*mm, 35*mm, 40*mm])
        items_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(items_table)
        
        # Totals
        legal_p = ""
        if invoice.vat_percentage == 0:
            legal_p = Paragraph("<i>Ngarkesa e kundert, nenparagrafi 1.4.1 ose 1.4.2 i nenit 52 te ligjit per TVSH</i>", self.note_style)

        totals_data = [
            [legal_p, "TOTAL PA TVSH", self.format_number(invoice.subtotal, True)],
            ["", "TVSH %", f"{float(invoice.vat_percentage):.2f}%"],
            ["", "TVSH SHUMA", self.format_number(invoice.vat_amount, True)],
            ["", "PER PAGESE", self.format_number(invoice.total, True)],
        ]
        totals_table = Table(totals_data, colWidths=[95*mm, 50*mm, 40*mm])
        totals_table.setStyle(TableStyle([
            ("GRID", (2, 0), (2, -1), 1, colors.black),
            ("ALIGN", (1, 0), (2, -1), "RIGHT"),
            ("SPAN", (0, 0), (0, 3)),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTNAME", (1, 3), (2, 3), "Helvetica-Bold"),
            ("FONTSIZE", (2, 3), (2, 3), 13),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(totals_table)
        story.append(Spacer(1, 35*mm))
        
        # Signatures
        sig_data = [["Faturoi", "Pranoi"], ["____________________", "____________________"]]
        sig_table = Table(sig_data, colWidths=[90*mm, 90*mm])
        sig_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (0, -1), "LEFT"), ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("TOPPADDING", (0, 0), (-1, -1), 15),
            ("LEFTPADDING", (0, 0), (0, -1), 30), ("RIGHTPADDING", (1, 0), (1, -1), 30),
        ]))
        story.append(sig_table)

        doc.build(story)
        return filepath

    def generate_offer_pdf(self, offer, company, client):
        filename = f"Oferta_{offer.offer_number.replace(' ', '_')}.pdf"
        filepath = os.path.join(EXPORTS_DIR, filename)
        
        doc = SimpleDocTemplate(
            filepath, pagesize=A4,
            leftMargin=15*mm, rightMargin=15*mm, topMargin=12*mm, bottomMargin=12*mm
        )
        
        story = []
        
        # Header (similar to invoice)
        logo_img, logo_h = self.process_logo(company.logo_path)
        company_data = [
            [logo_img] if logo_img else [Paragraph(f"<b>{company.name}</b>", self.bold_style)],
            [Paragraph("Fasada ventiluese", self.normal_style)],
            [Paragraph(f"Tel: {company.phone}", self.normal_style)],
            [Paragraph(company.email, self.normal_style)],
            [Paragraph(company.address, self.normal_style)],
            [Paragraph(f"Numër unik: {company.unique_number}", self.normal_style)],
            [Paragraph(f"Numër fiskal: {company.fiscal_number}", self.normal_style)],
            [Paragraph(f"<b>Llogaria: NLB {company.account_nib}</b>", self.bold_style)]
        ]
        company_table = Table(company_data, colWidths=[100*mm])
        company_table.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("ALIGN", (0,0), (-1,-1), "LEFT"), ("LEFTPADDING", (0,0), (-1,-1), 0), ("BOTTOMPADDING", (0,0), (0,0), 10)]))

        buyer_style = ParagraphStyle("buyer", fontSize=11, alignment=TA_RIGHT)
        buyer_bold_style = ParagraphStyle("buyer_bold", fontSize=12, fontName="Helvetica-Bold", alignment=TA_RIGHT)
        buyer_data = [[Spacer(1, logo_h if logo_h > 0 else 10*mm)], [Paragraph("<b>PERFITUESI</b>", buyer_bold_style)], [Paragraph(f"Emri: {client.name}", buyer_style)], [Paragraph(f"Adresa: {client.address or ''}", buyer_style)], [Paragraph(f"Numër unik: {client.unique_number or ''}", buyer_style)]]
        buyer_table = Table(buyer_data, colWidths=[90*mm])
        buyer_table.setStyle(TableStyle([("BOX", (0, 1), (-1, -1), 1, colors.black), ("LINEBELOW", (0, 1), (-1, 1), 1, colors.black), ("BACKGROUND", (0, 1), (-1, 1), colors.lightgrey), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("ALIGN", (0, 0), (-1, -1), "RIGHT"), ("PADDING", (0, 0), (-1, -1), 3), ("TOPPADDING", (0, 1), (-1, 1), 6), ("BOTTOMPADDING", (0, 1), (-1, 1), 6)]))
        
        header_container = Table([[company_table, buyer_table]], colWidths=[100*mm, 90*mm])
        header_container.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
        story.append(header_container)
        story.append(Spacer(1, 12*mm))

        # Title & Date
        offer_title_s = ParagraphStyle("OfferTitle", fontSize=15, fontName="Helvetica-Bold")
        offer_date_s = ParagraphStyle("OfferDate", fontSize=12, alignment=TA_RIGHT)
        title_t = Table([[Paragraph(offer.subject or "OFERTË", offer_title_s), Paragraph(f"Data: {self.format_date(offer.date)}", offer_date_s)]], colWidths=[140*mm, 50*mm])
        title_t.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'BOTTOM'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0)]))
        story.append(title_t)
        story.append(Spacer(1, 10*mm))
        
        # Items Table
        items_data = [["PËRSHKRIMI", "M²", "ÇMIMI", "TOTALI"]]
        for item in offer.items:
            items_data.append([item.description, self.format_number(item.quantity), self.format_number(item.unit_price, True), self.format_number(item.quantity * item.unit_price, True)])
        while len(items_data) < 6: items_data.append(["", "", "", ""])
        
        items_table = Table(items_data, colWidths=[85*mm, 25*mm, 35*mm, 40*mm])
        items_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('ALIGN', (1,1), (-1,-1), 'RIGHT'), ('PADDING', (0,0), (-1,-1), 6)]))
        story.append(items_table)
        
        # Totals
        totals_data = [["", "Nëntotali:", self.format_number(offer.subtotal, True)], ["", f"TVSH ({offer.vat_percentage}%):", self.format_number(offer.vat_amount, True)], ["", "TOTALI:", self.format_number(offer.total, True)]]
        totals_table = Table(totals_data, colWidths=[110*mm, 45*mm, 35*mm])
        totals_table.setStyle(TableStyle([('ALIGN', (1,0), (-1,-1), 'RIGHT'), ('FONTNAME', (1,2), (2,2), 'Helvetica-Bold'), ('FONTSIZE', (2,2), (2,2), 12)]))
        story.append(totals_table)
        
        doc.build(story)
        return filepath
