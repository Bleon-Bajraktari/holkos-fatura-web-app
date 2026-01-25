import os
import tempfile
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
        self.title_style = ParagraphStyle(
            "title", fontSize=22, alignment=TA_CENTER, fontName="Helvetica-Bold"
        )
        self.subtitle_style = ParagraphStyle(
            "subtitle", fontSize=12, alignment=TA_CENTER, fontName="Helvetica"
        )
        self.bold_style = ParagraphStyle(
            "bold", fontSize=10, fontName="Helvetica-Bold"
        )
        self.normal_style = ParagraphStyle(
            "normal", fontSize=10
        )
        self.right_style = ParagraphStyle(
            "right", fontSize=10, alignment=TA_RIGHT
        )

    def format_number(self, number, with_currency=False):
        if isinstance(number, (Decimal, float)):
            formatted = f"{float(number):,.2f}".replace(",", " ").replace(".", ",")
            return f"{formatted} €" if with_currency else formatted
        return str(number)

    def generate_invoice_pdf(self, invoice, company, client):
        filename = f"Invoice_{invoice.invoice_number}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        filepath = os.path.join(EXPORTS_DIR, filename)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=15*mm,
            rightMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=15*mm
        )
        
        story = []
        
        # Title
        story.append(Paragraph(f"FATURË NR. {invoice.invoice_number}", self.title_style))
        story.append(Spacer(1, 10*mm))
        
        # Header Info (Company & Client)
        data = [
            [
                Paragraph(f"<b>{company.name}</b><br/>{company.address}<br/>Tel: {company.phone}<br/>Email: {company.email}", self.normal_style),
                Paragraph(f"<b>BLERËSI:</b><br/>{client.name}<br/>{client.address}<br/>Nr. Unik: {client.unique_number}", self.normal_style)
            ]
        ]
        header_table = Table(data, colWidths=[90*mm, 90*mm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 15*mm))
        
        # Table of items
        items_data = [["PËRSHKRIMI", "SASIA", "ÇMIMI", "TOTALI"]]
        for item in invoice.items:
            items_data.append([
                item.description,
                self.format_number(item.quantity),
                self.format_number(item.unit_price, True),
                self.format_number(item.quantity * item.unit_price, True)
            ])
            
        items_table = Table(items_data, colWidths=[80*mm, 30*mm, 35*mm, 35*mm])
        items_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 10*mm))
        
        # Totals
        totals_data = [
            ["", "Nëntotali:", self.format_number(invoice.subtotal, True)],
            ["", f"TVSH ({invoice.vat_percentage}%):", self.format_number(invoice.vat_amount, True)],
            ["", "TOTALI:", self.format_number(invoice.total, True)],
        ]
        totals_table = Table(totals_data, colWidths=[100*mm, 45*mm, 35*mm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
            ('FONTNAME', (2,2), (2,2), 'Helvetica-Bold'),
            ('FONTSIZE', (2,2), (2,2), 12),
        ]))
        story.append(totals_table)
        
        doc.build(story)
        return filepath

    def generate_offer_pdf(self, offer, company, client):
        filename = f"Offer_{offer.offer_number}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        filepath = os.path.join(EXPORTS_DIR, filename)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=15*mm,
            rightMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=15*mm
        )
        
        story = []
        
        # Title
        story.append(Paragraph(f"OFERTË NR. {offer.offer_number}", self.title_style))
        story.append(Spacer(1, 10*mm))
        
        # Header Info (Company & Client)
        data = [
            [
                Paragraph(f"<b>{company.name}</b><br/>{company.address}<br/>Tel: {company.phone}<br/>Email: {company.email}", self.normal_style),
                Paragraph(f"<b>PËRFITUESI:</b><br/>{client.name}<br/>{client.address}<br/>Nr. Unik: {client.unique_number}", self.normal_style)
            ]
        ]
        header_table = Table(data, colWidths=[90*mm, 90*mm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 15*mm))

        # Subject
        story.append(Paragraph(f"<b>Subjekti:</b> {offer.subject}", self.bold_style))
        story.append(Spacer(1, 10*mm))
        
        # Table of items
        items_data = [["PËRSHKRIMI", "SASIA", "ÇMIMI", "TOTALI"]]
        for item in offer.items:
            items_data.append([
                item.description,
                self.format_number(item.quantity),
                self.format_number(item.unit_price, True),
                self.format_number(item.quantity * item.unit_price, True)
            ])
            
        items_table = Table(items_data, colWidths=[80*mm, 30*mm, 35*mm, 35*mm])
        items_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 10*mm))
        
        # Totals
        totals_data = [
            ["", "Nëntotali:", self.format_number(offer.subtotal, True)],
            ["", f"TVSH ({offer.vat_percentage}%):", self.format_number(offer.vat_amount, True)],
            ["", "TOTALI:", self.format_number(offer.total, True)],
        ]
        totals_table = Table(totals_data, colWidths=[100*mm, 45*mm, 35*mm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
            ('FONTNAME', (2,2), (2,2), 'Helvetica-Bold'),
            ('FONTSIZE', (2,2), (2,2), 12),
        ]))
        story.append(totals_table)
        
        doc.build(story)
        return filepath
