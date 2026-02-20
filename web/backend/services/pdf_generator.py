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
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from PIL import Image as PILImage, ImageOps
import json
try:
    import vercel
except ImportError:
    vercel = None

# We'll use absolute paths or relative to the backend project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
os.makedirs(EXPORTS_DIR, exist_ok=True)
_LOGO_CACHE = {}  # Cache for processed logo paths: { (original_path, height): (processed_path, width, height) }

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

    def format_date_spaces(self, date_obj):
        """DD MM YYYY (e.g. 01 01 2026) for contract Neni 4."""
        if date_obj:
            if isinstance(date_obj, str):
                try:
                    date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
                except: pass
            return date_obj.strftime("%d %m %Y")
        return ""

    def process_logo(self, logo_path, logo_height=32*mm):
        """Perpunon logon duke hequr pjeset e bardha (me caching dhe optimizim)"""
        if not logo_path:
            logo_path = os.path.join(BASE_DIR, "..", "assets", "images", "logo.png")
            if not os.path.exists(logo_path):
                return None, 0

        # Resolve path
        resolved_path = logo_path
        if not os.path.isabs(logo_path):
            candidate = os.path.join(BASE_DIR, logo_path)
            if os.path.exists(candidate):
                resolved_path = candidate
            else:
                repo_candidate = os.path.abspath(os.path.join(BASE_DIR, "..", logo_path))
                if os.path.exists(repo_candidate):
                    resolved_path = repo_candidate

        if not os.path.exists(resolved_path):
            return None, 0

        # Check Cache
        cache_key = (resolved_path, logo_height)
        if cache_key in _LOGO_CACHE:
            path, width, height = _LOGO_CACHE[cache_key]
            if os.path.exists(path):
                return Image(path, width, height), height

        try:
            pil_img = PILImage.open(resolved_path)
            if pil_img.mode != 'RGBA':
                pil_img = pil_img.convert('RGBA')
            
            # Optimized cropping of white background
            # 1. Convert to grayscale and threshold
            # 2. Invert so background is black (0) and logo is white (>0)
            # 3. getbbox() correctly finds the non-black area
            grayscale = pil_img.convert('L')
            # Pixels >= 250 (almost white) become 255 (white)
            threshold = 250
            mask = grayscale.point(lambda p: 255 if p < threshold else 0)
            bbox = mask.getbbox()
            
            if bbox:
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
            
            # Register for cleanup at exit
            atexit.register(lambda: os.unlink(path) if os.path.exists(path) else None)
            
            _LOGO_CACHE[cache_key] = (path, logo_width, logo_height)
            return Image(path, logo_width, logo_height), logo_height
        except Exception as e:
            print(f"Error processing logo: {e}")
            return None, 0

    def _get_storage_path(self, doc_type, date_obj, filename):
        """Krijon dhe kthen rrugën e ruajtjes sipas vitit dhe muajit"""
        year = str(date_obj.year)
        month = f"{date_obj.month:02d}"
        
        # exports/fatura/2026/01/filename.pdf
        folder_path = os.path.join(EXPORTS_DIR, doc_type, year, month)
        os.makedirs(folder_path, exist_ok=True)
        return os.path.join(folder_path, filename)

    def _handle_post_generation(self, local_path, doc_type, date_obj, filename):
        """Me ndihmën e këtij funksioni skedarët ngarkohen në Vercel Blob nëse token-i ekziston"""
        token = os.environ.get("BLOB_READ_WRITE_TOKEN")
        if token and vercel:
            try:
                cloud_path = f"{doc_type}/{date_obj.year}/{date_obj.month:02d}/{filename}"
                with open(local_path, "rb") as f:
                    blob = vercel.blob.put(cloud_path, f.read(), token=token)
                if os.path.exists(local_path):
                    os.remove(local_path)
                return blob.url
            except Exception as e:
                print(f"Cloud upload failed: {e}")
                return local_path
        return local_path

    def generate_invoice_pdf(self, invoice, company, client):
        year = invoice.date.year if hasattr(invoice.date, 'year') else datetime.now().year
        filename = f"Fatura_{invoice.invoice_number.replace(' ', '_')}_{year}.pdf"
        filepath = self._get_storage_path("faturat", invoice.date, filename)
        
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
        
        # Items Table (vetem rreshtat e artikujve)
        items_data = [["PERSHKRIMI", "M²", "CMIMI", "NENTOTALI"]]
        for item in invoice.items:
            items_data.append([
                item.description,
                self.format_number(item.quantity),
                self.format_number(item.unit_price, True),
                self.format_number(item.quantity * item.unit_price, True)
            ])
        while len(items_data) < 6:
            items_data.append(["", "", "", ""])

        items_table = Table(items_data, colWidths=[85*mm, 25*mm, 35*mm, 40*mm])
        items_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))

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
            ("VALIGN", (0, 0), (0, 0), "TOP"),
            ("VALIGN", (1, 0), (2, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (0, 0), 2),
            ("BOTTOMPADDING", (0, 0), (0, 0), 2),
            ("FONTNAME", (1, 3), (2, 3), "Helvetica-Bold"),
            ("FONTSIZE", (2, 3), (2, 3), 13),
            ("TOPPADDING", (1, 0), (2, 2), 6),
            ("BOTTOMPADDING", (1, 0), (2, 2), 6),
            ("TOPPADDING", (2, 3), (2, 3), 4),
            ("BOTTOMPADDING", (2, 3), (2, 3), 8),
            ("TOPPADDING", (1, 3), (1, 3), 6),
            ("BOTTOMPADDING", (1, 3), (1, 3), 6),
        ]))

        # Tabela e vetme: artikujt + totalet, pa hapesire ndermjet
        combined = Table([[items_table], [totals_table]], colWidths=[185*mm])
        combined.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(combined)
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
        return self._handle_post_generation(filepath, "faturat", invoice.date, filename)

    def generate_offer_pdf(self, offer, company, client, manual_font_size=None):
        """Gjeneron PDF për një ofertë - identike me desktop app (optimized)"""
        filename = f"Oferta_{offer.offer_number.replace(' ', '_')}.pdf"
        filepath = self._get_storage_path("ofertat", offer.date, filename)
        
        doc = SimpleDocTemplate(
            filepath, pagesize=A4,
            leftMargin=15*mm, rightMargin=15*mm, topMargin=12*mm, bottomMargin=12*mm
        )
        
        story = []
        
        # -------------------------------
        # HEADER (Standard Invoice Header)
        # -------------------------------
        buyer_style = ParagraphStyle("buyer", fontSize=11, alignment=TA_RIGHT)
        buyer_bold_style = ParagraphStyle("buyer_bold", fontSize=12, fontName="Helvetica-Bold", alignment=TA_RIGHT)
        
        company_data = []
        logo_img, logo_h = self.process_logo(company.logo_path)
        logo_height = logo_h if logo_h > 0 else 0
        if logo_img:
            company_data.append([logo_img])
        else:
            company_data.append([Paragraph(f"<b>{company.name}</b>", self.bold_style)])
            
        company_data += [
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
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (0, 0), 10),
        ]))
        
        buyer_data = [
            [Spacer(1, logo_height)],
            [Paragraph("<b>PERFITUESI</b>", buyer_bold_style)],
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
        header_container.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (0, 0), "LEFT"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("LEFTPADDING", (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ]))
        story.append(header_container)
        story.append(Spacer(1, 12*mm))

        # -------------------------------
        # OFFER BODY (Titulli, Punimet, Totali, Shenimet)
        # -------------------------------
        
        # Title and Date Row
        title_text = offer.subject if offer.subject else "OFERTË"
        date_text = f"Data: {self.format_date(offer.date)}" if offer.date else ""
        
        offer_title_style = ParagraphStyle(
            "OfferTitle",
            fontSize=15,
            textColor=colors.black,
            fontName="Helvetica-Bold",
            leftIndent=0,
            firstLineIndent=0,
            spaceAfter=0
        )
        
        offer_date_style = ParagraphStyle(
            "OfferDate",
            fontSize=12,
            textColor=colors.black,
            fontName="Helvetica",
            alignment=TA_RIGHT,
            leftIndent=0,
            firstLineIndent=0,
            spaceAfter=0
        )
        
        title_para = Paragraph(title_text, offer_title_style)
        date_para = Paragraph(date_text, offer_date_style)
        
        # Table with 2 columns: Title (Left) - Date (Right)
        title_table = Table([[title_para, date_para]], colWidths=[140*mm, 50*mm])
        title_table.setStyle(TableStyle([
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ]))
        story.append(title_table) 
        
        story.append(Spacer(1, 10*mm))
        
        if offer.items:
            # Sort items by order_index
            sorted_items = sorted(offer.items, key=lambda x: getattr(x, 'order_index', 0))
            
            # DYNAMIC SCALING: Detect content density
            content_sample = " ".join([getattr(item, 'description', '') or '' for item in sorted_items])
            total_len = len(content_sample)
            count = len(sorted_items)
            
            # Decide base font
            if manual_font_size and manual_font_size != "Auto":
                try:
                    base_font = float(manual_font_size)
                    leading = base_font * 1.4
                except:
                    base_font, leading = 11.5, 16 
            elif count < 7 and total_len < 400:
                base_font, leading = 13.5, 19
            elif count < 12 and total_len < 800:
                base_font, leading = 11.5, 16
            else:
                base_font, leading = 10, 14
            
            # Specialized Styles
            r_style = ParagraphStyle("RNormal", parent=self.normal_style, fontSize=base_font, leading=leading, leftIndent=0, firstLineIndent=0)
            r_note = ParagraphStyle("RNote", parent=self.note_style, fontSize=base_font, leading=leading, leftIndent=0, firstLineIndent=0)
            r_header = ParagraphStyle("RHead", parent=self.normal_style, fontSize=15, leading=18, fontName="Helvetica-Bold", textColor=colors.black, leftIndent=0, firstLineIndent=0)
            r_calc = ParagraphStyle("RCalc", parent=self.right_style, fontSize=base_font, leading=leading, leftIndent=0, firstLineIndent=0)

            # Pre-process items into flowables with metadata
            render_items = []

            for item in sorted_items:
                row_type = getattr(item, 'row_type', 'item') or 'item'
                
                # Parse custom_attributes for border
                custom_attr_raw = getattr(item, 'custom_attributes', None)
                has_border = True  # Default
                modules_list = []
                
                if custom_attr_raw:
                    if isinstance(custom_attr_raw, str):
                        try:
                            custom_attr_raw = json.loads(custom_attr_raw)
                        except:
                            custom_attr_raw = None
                    
                    if isinstance(custom_attr_raw, dict):
                        has_border = custom_attr_raw.get('has_border', True)
                        modules_list = custom_attr_raw.get('modules', [])
                    elif isinstance(custom_attr_raw, list):
                        modules_list = custom_attr_raw
                
                flowable = None
                
                if row_type == 'header':
                    desc_text = (getattr(item, 'description', '') or '').strip()
                    if desc_text:
                        data = [[Paragraph(desc_text, r_header)]]
                        t = Table(data, colWidths=[190*mm])
                        style_cmds = [
                            ('VALIGN', (0,0), (-1,-1), 'TOP'),
                            ('LEFTPADDING', (0,0), (-1,-1), 0),
                            ('RIGHTPADDING', (0,0), (-1,-1), 0),
                            ('TOPPADDING', (0,0), (-1,-1), 0),
                            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                        ]
                        if has_border:
                            style_cmds.extend([
                                ('BOX', (0,0), (-1,-1), 1, colors.Color(0.85, 0.85, 0.85)),
                                ('LEFTPADDING', (0,0), (-1,-1), 6),
                                ('RIGHTPADDING', (0,0), (-1,-1), 6),
                                ('TOPPADDING', (0,0), (-1,-1), 6),
                                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                                ('BACKGROUND', (0,0), (-1,-1), colors.Color(0.97, 0.97, 0.97))
                            ])
                        t.setStyle(TableStyle(style_cmds))
                        flowable = t
                
                elif row_type == 'text':
                    desc_text = (getattr(item, 'description', '') or '').strip()
                    lines = desc_text.split('\n')
                    paras = []
                    for line in lines:
                        if line.strip():
                            paras.append(Paragraph(line, r_note if line.strip().startswith("*") else r_style))
                    
                    if paras:
                        data = [[paras]]
                        t = Table(data, colWidths=[190*mm])
                        style_cmds = [
                            ('VALIGN', (0,0), (-1,-1), 'TOP'),
                            ('LEFTPADDING', (0,0), (-1,-1), 0),
                            ('RIGHTPADDING', (0,0), (-1,-1), 0),
                            ('TOPPADDING', (0,0), (-1,-1), 0),
                            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                        ]
                        if has_border:
                            style_cmds.extend([
                                ('BOX', (0,0), (-1,-1), 1, colors.Color(0.85, 0.85, 0.85)),
                                ('LEFTPADDING', (0,0), (-1,-1), 6),
                                ('RIGHTPADDING', (0,0), (-1,-1), 6),
                                ('TOPPADDING', (0,0), (-1,-1), 4),
                                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                            ])
                        t.setStyle(TableStyle(style_cmds))
                        flowable = t

                else:  # ITEM
                    desc_text = (getattr(item, 'description', '') or '').strip()
                    
                    # Calc Logic
                    calc_segments = []
                    has_any_val = False
                    if isinstance(modules_list, list):
                        has_any_val = any(str(attr.get('value', '')).strip() for attr in modules_list)
                        if has_any_val:
                            for idx, attr in enumerate(modules_list):
                                v, u = str(attr.get('value', '')).strip(), str(attr.get('unit', '')).strip().replace("m2", "m²").replace("m3", "m³")
                                if v:
                                    if any(s.startswith("<b>") for s in calc_segments):
                                        calc_segments.append("<font color='#666666'>x</font>")
                                    calc_segments.append(f"<b>{v}</b> {u}")
                                elif u:
                                    calc_segments.append(u)
                    
                    formula_html = " ".join(calc_segments).strip() if has_any_val else ""
                    
                    data = None
                    if desc_text and formula_html:
                        data = [[Paragraph(desc_text, r_style), Paragraph(f"<font color='#666666'>=</font> {formula_html}", r_calc)]]
                    elif desc_text:
                        data = [[Paragraph(desc_text, r_style), ""]]
                    elif formula_html:
                        data = [["", Paragraph(f"<font color='#666666'>=</font> {formula_html}", r_calc)]]
                    
                    if data:
                        t = Table(data, colWidths=[130*mm, 60*mm])
                        style_cmds = [
                            ('ALIGN', (0,0), (0,0), 'LEFT'),
                            ('ALIGN', (1,0), (1,0), 'RIGHT'),
                            ('VALIGN', (0,0), (-1,-1), 'TOP'),
                            ('LEFTPADDING', (0,0), (-1,-1), 0),
                            ('RIGHTPADDING', (0,0), (-1,-1), 0),
                            ('TOPPADDING', (0,0), (-1,-1), 0),
                            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                        ]
                        if has_border:
                            style_cmds.extend([
                                ('BOX', (0,0), (-1,-1), 1, colors.Color(0.85, 0.85, 0.85)),
                                ('LEFTPADDING', (0,0), (-1,-1), 6),
                                ('RIGHTPADDING', (0,0), (-1,-1), 6),
                                ('TOPPADDING', (0,0), (-1,-1), 4),
                                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                            ])
                        t.setStyle(TableStyle(style_cmds))
                        flowable = t

                if flowable:
                    render_items.append({'obj': flowable, 'has_border': has_border})

            # Append to story with smart spacing
            for i, item in enumerate(render_items):
                story.append(item['obj'])
                
                next_item = render_items[i+1] if i + 1 < len(render_items) else None
                
                if next_item and item['has_border'] and next_item['has_border']:
                    pass  # No spacer when both have borders
                else:
                    story.append(Spacer(1, 6*mm))

            story.append(Spacer(1, 5*mm))
        
        # -------------------------------
        # SIGNATURES
        # -------------------------------
        story.append(Spacer(1, 20*mm))
        signatures = [
            ["Holkos", ""],
            ["____________________", ""]
        ]
        signatures_table = Table(signatures, colWidths=[92.5*mm, 92.5*mm])
        signatures_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("TOPPADDING", (0, 0), (-1, -1), 15),
            ("LEFTPADDING", (0, 0), (0, -1), 50),  
            ("RIGHTPADDING", (1, 0), (1, -1), 50), 
        ]))
        story.append(signatures_table)
        
        doc.build(story)
        return self._handle_post_generation(filepath, "ofertat", offer.date, filename)

    def generate_contract_pdf(self, contract, company):
        """Kontratë pune – 2 faqe, pjesët në kllapa të vogla dhe të përqendruara."""
        from datetime import date as date_type
        sig_date = contract.signing_date
        if hasattr(sig_date, 'year'):
            date_for_path = sig_date
        else:
            try:
                date_for_path = datetime.strptime(str(sig_date), '%Y-%m-%d').date()
            except Exception:
                date_for_path = date_type.today()
        safe_name = (contract.employee_name or "Kontrate").replace(" ", "_")[:50]
        filename = f"Kontrate_{safe_name}_{date_for_path.year}.pdf"
        filepath = self._get_storage_path("kontratat", date_for_path, filename)

        doc = SimpleDocTemplate(
            filepath, pagesize=A4,
            leftMargin=16*mm, rightMargin=16*mm, topMargin=12*mm, bottomMargin=12*mm
        )

        def esc(s):
            return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        emp = contract.employee_name or ""
        pers_num = contract.personal_number or ""
        res = contract.residence or ""
        salary_val = float(contract.gross_salary) if contract.gross_salary is not None else 0
        salary_str = f"{int(round(salary_val))}" if salary_val == round(salary_val) else f"{salary_val:,.2f}".replace(",", " ")
        dt = self.format_date(contract.contract_start_date)

        comp_name = (company.name if company else "Holkos Metal").strip()
        comp_nf = getattr(company, 'fiscal_number', None) or getattr(company, 'unique_number', None) or "600610093"
        comp_addr = (company.address or "").strip()
        comp_rep_fixed = "Mustafë Bajraktari"

        # Tekst normal: 9pt, leading i vogël që të hyjë në 2 faqe
        contract_style = ParagraphStyle("contract", fontSize=9, leading=11, alignment=TA_LEFT, fontName="Helvetica")
        # Pjesët në kllapa: më të vogla, të përqendruara në mes të rreshtit
        paren_style = ParagraphStyle("contract_paren", fontSize=7, leading=9, alignment=TA_CENTER, fontName="Helvetica", textColor=colors.gray)
        title_contract = ParagraphStyle("contract_title", fontSize=12, alignment=TA_CENTER, fontName="Helvetica-Bold", spaceAfter=3)
        header_style = ParagraphStyle("contract_header", fontSize=10, alignment=TA_LEFT, fontName="Helvetica-Bold", spaceAfter=2)

        def p(t):
            return Paragraph(t, contract_style)
        def paren(t):
            return Paragraph(esc(t), paren_style)

        story = []
        spacer_small = 1.5*mm

        story.append(Paragraph("Kontratë e Re.", header_style))
        story.append(Spacer(1, 2*mm))
        story.append(p("Në bazë të nenit 10 paragrafi 2, pikat 2.1 dhe 2.2. dhe nenit 11 të Ligjit të Punës Nr. 03/L-212 i shpallur në Gazetën Zyrtare të Republikës së Kosovës me dt.01.12.2010, Punëdhënësi dhe i Punësuari, si subjekte të mardhënies juridike të punës lidhin:"))
        story.append(Spacer(1, 3*mm))
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph("KONTRATË PUNE PËR KOHË TË PACAKTUAR", title_contract))
        story.append(Spacer(1, 3*mm))
        story.append(Spacer(1, 3*mm))

        n1_employer = f'NTP "{esc(comp_name)}" përfaqësuar nga {esc(comp_rep_fixed)}, NF {esc(comp_nf)}' + (f'-{esc(comp_addr)}' if comp_addr else ', pn-Istog') + '.'
        n1_employee = f'<b><u>{esc(emp)}</u></b> NP <b><u>{esc(pers_num)}</u></b> – shkollim i mesem, me banim <b><u>{esc(res)}</u></b>'
        story.append(p("<b>Neni 1</b><br/>Me këtë kontratë: " + n1_employer))
        story.append(paren("(Emri/emërtimi, NRB, NF dhe adresa e punëdhënësit)"))
        story.append(p("Në tekstin e metejmë Punëdhënësi lidhë kontratë pune me:"))
        story.append(p(n1_employee))
        story.append(paren("(Emri dhe mbiemri, kualifikimi, adresa dhe numri personal)"))
        story.append(Spacer(1, spacer_small))
        story.append(p("<b>Neni 2</b><br/>I Punësuari do të kryej këto detyra të punës: Punetor"))
        story.append(paren("(Emërtimi, natyra, lloji i punës dhe përshkrimi i detyrave të punës)"))
        story.append(Spacer(1, spacer_small))
        story.append(p('<b>Neni 3</b><br/>I Punësuari do të kryej punët në: Terren sipas nevojes se NTP "' + esc(comp_name) + '"'))
        story.append(paren("(vendi i punës ku do të kryhet puna apo në lokacione të ndryshme)"))
        story.append(Spacer(1, spacer_small))
        story.append(p("<b>Neni 4</b><br/>I Punësuari themelon mardhënie pune në kohë të pacaktuar që nga data: <b><u>" + esc(dt) + "</u></b>."))
        story.append(Spacer(1, spacer_small))
        story.append(p("<b>Neni 5</b><br/>I Punësuari është i detyruar të filloj punën me: <b><u>" + esc(dt) + "</u></b>. Nëse i punësuari nuk e fillon punën në ditën e caktuar sipas kësaj kontrate, do të konsiderohet se nuk ka themeluar mardhanie pune, përvec nëse është penguar për shkaqe të arsyeshme."))
        story.append(Spacer(1, spacer_small))
        story.append(p("<b>Neni 6</b><br/>Ditë pune janë nga e hëna në të premte me nga 8 orë pune, gjithsej 40 orë në javë."))
        story.append(Spacer(1, spacer_small))
        story.append(p("<b>Neni 7</b><br/>Të punësuarit i caktohet paga bazë për punën të cilën e kryen për punëdhënësin, në lartësi prej Bruto <b><u>" + esc(salary_str) + " euro</u></b>, së paku një herë në muaj e cila nuk mund të jetë më e vogël se paga minimale."))
        story.append(Spacer(1, spacer_small))
        story.append(p("<b>Neni 8</b><br/>I punësuari ka të drejtë në pagë shtesë në përqindje të pagës bazë:<br/>1) 20 % në orë kujdestari;<br/>2) 30 % në orë për punë gjatë natës;<br/>3) 30 % në orë për punë jashtë orarit;<br/>4) 50 % në orë për punë gjatë ditëve të festave, dhe<br/>5) 50 % në orë për punë gjatë fundjavës."))
        story.append(Spacer(1, spacer_small))
        story.append(p("<b>Neni 9</b><br/>I punësuari ka të drejtë në kompezim të pagës pa u angazhuar në punë, në rastet në vijim:<br/>1) gjatë ditëve të festive në të cilat nuk punohet;<br/>2) gjatë kohës së shfrytëzimit të pushimit vjetor;<br/>3) gjatë aftësimit dhe përsosjes profesionale për të cilën është dërguar, dhe<br/>4) gjatë ushtrimit të funksioneve publike për të cilat nuk paguhet."))
        story.append(Spacer(1, spacer_small))
        story.append(p("<b>Neni 10</b><br/>I punësuari ka të drejtë në kompensim të pushimit mjekësor të pagës bazë, prej:<br/>1) 100% në rast të shfrytëzimit të pushimit mjekësor të rregullt, mbi bazën deri në 20 ditë pune brenda një (1) viti;<br/>2) 70% në rast të shfrytëzimit të pushimit mjekësore si pasojë e lëndimit në punë ose sëmundjes profesionale, e cila ndërlidhet me kryerjen e punëve dhe shërbimeve për punëdhënësin, në kohëzgjatje prej dhjetë (10) deri në nëntëdhjetë (90) ditë pune."))
        story.append(Spacer(1, spacer_small))
        story.append(p("<b>Neni 11</b><br/>I punësuari ka të drejtë në pushim, dhe atë;<br/>1) pushim gjatë ditës në kohëzgjatje prej se paku 30 minutash, në përputhje me organizimin e orarit të punës me punëdhënësin.<br/>2) pushim ditor në kohëzgjatje prej së paku dymbdhjetë (12) orë pandërprerë, midis dy (2) ditëve të njëpasnjëshme të punës.<br/>3) pushim javor në kohezgjatje prej njëzetekatër (24) orë pandërprerë.<br/>4) pushim vjetor në kohëzgjatje së paku 4 javë.<br/>5) i punësuari i cili përkundër masave mbrojtëse nuk mund të mbrohet nga ndikimet e jashtme, ka te drejtë në pushim vjetor shtesë edhe për dy (2) ditë të tjera.<br/>6) nëna me fëmijë deri ne tre (3) vjec, prindi vetushqyes dhe personat me aftësi të kufizuara kanë të drejtë në pushim vjetor shtesë edhe për dy (2) ditë të tjera."))
        story.append(Spacer(1, spacer_small))
        story.append(p("<b>Neni 12</b><br/>I punësuari i cili për herë të parë themelon mardhënie pune ose i cili nuk ka ndërprerje më tepër se pesë (5) ditë pune, ka të drejtën e shfrytezimit të pushimit vjetor pas gjashtë (6) muajve të punës së pandërprerë."))
        story.append(Spacer(1, spacer_small))
        story.append(p("<b>Neni 13</b><br/>I punësuari ka të drejtë së paku një ditë e gjysmë (1.5) të pushimit, për cdo muaj kalendarik të kaluar në punë, nësë:<br/>1) në vitin kalendarik në të cilin për herë të parë ka themeluar mardhënie pune, nuk i ka gjashtë (6) muaj të punës së pandërprerë.<br/>2) në vitin kalendarik nuk e ka fituar të drejtën për shfrytëzimin e pushimit vjetor për shkak të ndërprejes së mardhënies së punës."))
        story.append(Spacer(1, spacer_small))
        story.append(p("<b>Neni 14</b><br/>I punësuari është përgjegjës për kompenzimin e dëmit për punën ose me lidhje me punën, nëse me qëllim ose nga pakujdesia i ka shkaktuar dëm punëdhënësit. I punësuari është përgjegjës edhe për kompenzimin e dëmit, nëse me fajin e tij i ka shkaktuar dëm palës së tretë, dëm të cilin punëdhënësi duhet t'a kompenzoj."))
        story.append(Spacer(1, spacer_small))
        story.append(p("<b>Neni 15</b><br/>Të punësuarit i ndërprehet mardhënia e punës nga punëdhënësi, nëse:<br/>1) ndërpreja e tillë arsyetohet për arsye ekonomike, teknike ose organizative;<br/>2) i punësuari nuk është më i aftë të kryej detyrat e punës;<br/>3) në rastet e rënda të sjelljes së keqe të të punësuarit;<br/>4) për shkak të mospërmbushjes së detyrave të punës, dhe<br/>5) për rastet e tjera të cilat janë të përcaktuara me Ligjin e Punës."))
        story.append(Spacer(1, spacer_small))
        story.append(p("<b>Neni 16</b><br/>Punëdhënësi obligohet të siguroj dhe të zbatoj mjetet dhe masat e mbrojtjes në punë, sipas legjislacionit në fuqi. I punësuari është i detyruar t'iu përmbahet masave të mbrojtjes në punë."))
        story.append(Spacer(1, spacer_small))
        story.append(p("<b>Neni 17</b><br/>Punëdhënësi obligohet t'i paguaj kontributet prej 5% për skemën pensionale të obligueshme dhe skemat tjera të përcaktuara me ligj."))
        story.append(Spacer(1, spacer_small))
        story.append(p("<b>Neni 18</b><br/>Punëdhënësi dhe i punësuari i pranojnë të gjitha të drejtat, detyrimet dhe përgjegjësitë e caktuara me Ligj, me Kontratë Kolektive dhe me këtë Kontratë."))
        story.append(Spacer(1, spacer_small))
        story.append(p("<b>Neni 19</b><br/>Për kontestet eventuale të moszbatimit të kësaj kontrate, palët kontraktuese e pranojnë kompetencën e Gjykatës Komunale në Peje."))
        story.append(Spacer(1, spacer_small))
        story.append(p("<b>Neni 20</b><br/>Secila palë mund t'a shkëputë këtë Kontratë në mënyrë të njëanëshme, sipas kushteve dhe rasteve të caktuara me Ligj dhe me Kontratën Kolektive."))
        story.append(Spacer(1, spacer_small))
        story.append(p("<b>Neni 21</b><br/>Në asnjë rast, dispozitat e kësaj Kontratë nuk mund të jenë me pak të favorshme për të punësuarin dhe punëdhënësin, së dispozitat e Ligjit të Punës ose të Kontratës Kolektive, për sa u përket të drejtave dhe kushteve nga mardhënia juridike e punës. Për të drejtat dhe detyrimet të cilat nuk janë përcaktuar me këtë Kontratë, zbatohen drejtëpërdrejtë dispozitat e Ligjit të Punës dhe të Kontratës Kolektive."))
        story.append(Spacer(1, spacer_small))
        story.append(p("<b>Neni 22</b><br/>Pas njoftimit me përmbajtjen e Kontratës, kjo Kontratë nga palët kontraktuese u nënshkrua me <b><u>" + esc(dt) + "</u></b>.<br/>Në Peje dhe atë në 5 kopje autentike, nga të cilat secilës palë i mbeten nga dy (2) kopje."))
        story.append(Spacer(1, 6*mm))

        sig_style = ParagraphStyle("sig", fontSize=9, fontName="Helvetica-Bold")
        sig_style_right = ParagraphStyle("sig_right", fontSize=9, fontName="Helvetica-Bold", alignment=TA_RIGHT)
        contract_style_right = ParagraphStyle("contract_sig_right", fontSize=9, leading=11, alignment=TA_RIGHT, fontName="Helvetica")
        sig_table = Table([
            [Paragraph("Punëdhenesi:", sig_style), Paragraph("I Punësuari:", sig_style_right)],
            [Paragraph(esc(comp_name), contract_style), Paragraph(esc(emp), contract_style_right)],
            [Paragraph(esc(comp_rep_fixed), contract_style), Paragraph("", contract_style)],
            ["", ""],
            [".......................................................................................V.V.......................................................................................", ""]
        ], colWidths=[90*mm, 90*mm])
        sig_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        story.append(sig_table)

        doc.build(story)
        return self._handle_post_generation(filepath, "kontratat", date_for_path, filename)
