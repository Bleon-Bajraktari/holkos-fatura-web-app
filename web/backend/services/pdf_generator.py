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
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (1, 3), (2, 3), "Helvetica-Bold"),
            ("FONTSIZE", (2, 3), (2, 3), 13),
            ("TOPPADDING", (1, 0), (2, 2), 6),
            ("BOTTOMPADDING", (1, 0), (2, 2), 6),
            # Special alignment for the final TOTAL row (PER PAGESE)
            # Value Column (Right)
            ("TOPPADDING", (2, 3), (2, 3), 4),
            ("BOTTOMPADDING", (2, 3), (2, 3), 8),
            # Label Column (PER PAGESE) 
            ("TOPPADDING", (1, 3), (1, 3), 6),
            ("BOTTOMPADDING", (1, 3), (1, 3), 6),
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
