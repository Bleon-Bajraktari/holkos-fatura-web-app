"""
Shërbimi për gjenerimin e PDF-ve të faturave
"""
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
from models.invoice import Invoice
from models.client import Client
from models.company import Company
from decimal import Decimal
import os
import tempfile
import atexit
from config.settings import EXPORTS_DIR, IMAGES_DIR

class PDFGenerator:
    """Klasa për gjenerimin e PDF-ve të faturave"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_styles()
    
    def setup_styles(self):
        """Konfiguron stilet për PDF"""
        self.title_style = ParagraphStyle(
            "title",
            fontSize=24, # Rritur nga 18
            alignment=TA_CENTER,
            fontName="Helvetica-Bold"
        )
        
        self.subtitle_style = ParagraphStyle(
            "subtitle",
            fontSize=13, # Rritur nga 11
            alignment=TA_CENTER,
            fontName="Helvetica"
        )
        
        self.bold_style = ParagraphStyle(
            "bold",
            fontSize=11, # Rritur nga 10
            fontName="Helvetica-Bold"
        )
        
        self.normal_style = ParagraphStyle(
            "normal",
            fontSize=11 # Rritur nga 10
        )
        
        self.right_style = ParagraphStyle(
            "right",
            fontSize=11,
            alignment=TA_RIGHT
        )
        
        self.note_style = ParagraphStyle(
            "note",
            fontSize=10,
            fontName="Helvetica-Oblique",
            alignment=TA_LEFT,
            leftIndent=0
        )
    
    def format_number(self, number, with_currency=False):
        """Formaton numrin me presje si separator"""
        if isinstance(number, Decimal):
            number = float(number)
        formatted = f"{number:,.2f}".replace(",", " ").replace(".", ",")
        if with_currency:
            return f"{formatted} €"
        return formatted
    
    def format_date(self, date_obj):
        """Formaton datën në format shqip"""
        if date_obj:
            return date_obj.strftime("%d.%m.%Y")
        return ""
    
    def generate(self, invoice: Invoice, output_path=None):
        """Gjeneron PDF për një fatura"""
        if not invoice.id:
            raise ValueError("Fatura duhet të jetë e ruajtur para se të gjenerohet PDF")
        
        # Përcakto rrugën e output
        if not output_path:
            filename = f"Fatura_{invoice.invoice_number.replace(' ', '_')}.pdf"
            output_path = os.path.join(EXPORTS_DIR, filename)
        
        # Ngarko të dhënat
        company = Company()
        company.load()
        
        client = Client.get_by_id(invoice.client_id)
        if not client:
            raise ValueError("Klienti nuk u gjet")
        
        # Krijo dokumentin
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=15*mm,
            rightMargin=15*mm,
            topMargin=12*mm,
            bottomMargin=12*mm
        )
        
        story = []
        
        # -------------------------------
        # TITULLI "FATURË NR. XX/VITI" NË KRYE
        # -------------------------------
        year = invoice.date.year
        inv_num = invoice.invoice_number
        # Brenda faturës e duam vetëm numrin nëse është format standard
        if "NR." in inv_num.upper():
            inv_num = inv_num.upper().split("NR.")[-1].strip()
            
        title_text = f"FATURË {inv_num}/{year}"
        title = Paragraph(title_text, self.title_style)
        story.append(title)
        
        # DATA PERFUND TITULLIT (Shtuar Spacer për të shmangur mbivendosjen)
        story.append(Spacer(1, 6*mm))
        date_text = f"Data: {self.format_date(invoice.date)}"
        subtitle = Paragraph(date_text, self.subtitle_style)
        story.append(subtitle)
        
        story.append(Spacer(1, 15*mm)) # Rritur hapësira deri te logo
        
        # -------------------------------
        # HEADER (2 tabela të ndara: Kompania majtas, Blerësi djathtas)
        # -------------------------------
        # Logo ose emri i kompanisë
        logo_path = company.logo_path if company.logo_path and os.path.exists(company.logo_path) else None
        if not logo_path:
            logo_path = os.path.join(IMAGES_DIR, "logo.png")
        
        # Stil për blerësi (align right)
        buyer_style = ParagraphStyle(
            "buyer",
            fontSize=11, # Rritur
            alignment=TA_RIGHT
        )
        
        buyer_bold_style = ParagraphStyle(
            "buyer_bold",
            fontSize=12, # Rritur
            fontName="Helvetica-Bold",
            alignment=TA_RIGHT
        )
        
        # Tabela e kompanisë (majtas) - e ndarë
        company_data = []
        
        # Logo ose emri - me rezolucion të mirë dhe prerje e pjesëve të bardha
        logo_height = 32*mm  # Rritur nga 25mm
        if os.path.exists(logo_path):
            try:
                # Lexo logo me PIL për të marrë dimensionet origjinale
                pil_img = PILImage.open(logo_path)
                
                # Konverto në RGBA për të punuar me transparent
                original_mode = pil_img.mode
                if pil_img.mode != 'RGBA':
                    pil_img = pil_img.convert('RGBA')
                
                # Gjej pjesët e bardha dhe transparent dhe preji
                # Kjo heq padding-in e bardhë nga logoja
                # Së pari provo me getbbox() për transparent
                bbox = pil_img.getbbox()
                
                # Nëse nuk ka transparent ose bbox është i plotë, gjej pjesët e bardha
                if not bbox or bbox == (0, 0, pil_img.width, pil_img.height):
                    # Konverto në RGB për të gjetur pjesët e bardha
                    rgb_img = pil_img.convert('RGB')
                    width, height = rgb_img.size
                    left, top, right, bottom = width, height, 0, 0
                    
                    # Gjej bounding box manualisht duke kontrolluar piksellat
                    # Optimizuar: kontrollo nga skajet për performancë më të mirë
                    found_content = False
                    
                    # Gjej top (nga lart poshtë)
                    for y in range(height):
                        for x in range(width):
                            r, g, b = rgb_img.getpixel((x, y))
                            # Konsidero si jo-bardhë nëse nuk është shumë afër bardhës (tolerancë)
                            if not (r >= 250 and g >= 250 and b >= 250):
                                top = y
                                found_content = True
                                break
                        if found_content:
                            break
                    
                    if found_content:
                        # Gjej bottom (nga poshtë lart)
                        found_content = False
                        for y in range(height - 1, top - 1, -1):
                            for x in range(width):
                                r, g, b = rgb_img.getpixel((x, y))
                                if not (r >= 250 and g >= 250 and b >= 250):
                                    bottom = y
                                    found_content = True
                                    break
                            if found_content:
                                break
                        
                        # Gjej left dhe right
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
                        else:
                            # Nëse nuk gjejmë përmbajtje, përdor imazhin origjinal
                            pil_img = PILImage.open(logo_path).convert('RGBA')
                elif bbox:
                    # Prej logo duke hequr pjesët transparent
                    pil_img = pil_img.crop(bbox)
                
                img_width, img_height = pil_img.size
                
                # Llogarit raportin e aspektit
                aspect_ratio = img_width / img_height
                
                # Përdor lartësinë e dëshiruar dhe llogarit gjerësinë bazuar në raportin
                logo_width = logo_height * aspect_ratio
                
                # Kufizo gjerësinë maksimale nëse është shumë e madhe
                max_width = 50*mm  # Pak më e vogël
                if logo_width > max_width:
                    logo_width = max_width
                    logo_height = logo_width / aspect_ratio
                
                # Ruaj logo të prerë në një file të përkohshëm
                temp_logo = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                pil_img.save(temp_logo.name, 'PNG')
                temp_logo_path = temp_logo.name
                temp_logo.close()
                
                # Krijo imazhin me rezolucion të mirë (pa pjesë të bardha)
                logo = Image(temp_logo_path, logo_width, logo_height)
                
                # Fshi file-in e përkohshëm pas përdorimit
                def cleanup_temp_logo():
                    try:
                        if os.path.exists(temp_logo_path):
                            os.unlink(temp_logo_path)
                    except:
                        pass
                atexit.register(cleanup_temp_logo)
                
                company_data.append([logo])
            except Exception as e:
                print(f"Gabim në ngarkimin e logos: {e}")
                company_data.append([Paragraph(f"<b>{company.name}</b>", self.bold_style)])
        else:
            company_data.append([Paragraph(f"<b>{company.name}</b>", self.bold_style)])
        
        # Informacione kompanie
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
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            # Pak padding midis logos dhe të dhënave
            ("BOTTOMPADDING", (0, 0), (0, 0), 10),  # Pak padding poshtë logos
            ("TOPPADDING", (0, 1), (0, 1), 10),  # Pak padding mbi "Fasada ventiluese"
            # Logo më në të djathtë
            ("LEFTPADDING", (0, 0), (0, 0), 8),  # Më shumë padding majtas për logo
        ]))
        
        # Tabela e blerësit (djathtas) - e ndarë
        # Shto rresht bosh me lartësi të barabartë me logo që "BLERESI" të jetë në nivel me "Fasada ventiluese"
        buyer_data = [
            [Spacer(1, logo_height)],  # Rresht bosh me lartësi të barabartë me logo
            [Paragraph("<b>BLERESI</b>", buyer_bold_style)],  # Titulli i tabelës
            [Paragraph(f"Emri: {client.name}", buyer_style)],
            [Paragraph(f"Adresa: {client.address}", buyer_style)],
            [Paragraph(f"Numër unik: {client.unique_number}", buyer_style)],
        ]
        
        buyer_table = Table(buyer_data, colWidths=[90*mm])
        buyer_table.setStyle(TableStyle([
            # Outer border vetëm për pjesën e blerësit (nga rreshti 1 poshtë, jo rreshti 0)
            ("BOX", (0, 1), (-1, -1), 1, colors.black),
            # Border për titullin "BLERESI" (rreshti 1)
            ("LINEBELOW", (0, 1), (-1, 1), 1, colors.black),
            # Background për titullin
            ("BACKGROUND", (0, 1), (-1, 1), colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 1), (-1, 1), 6),  # Më shumë padding për titullin
            ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
        ]))
        
        # Kombino 2 tabelat në një tabelë container për pozicionim
        header_container = Table(
            [[company_table, buyer_table]],
            colWidths=[100*mm, 90*mm]
        )
        header_container.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (0, 0), "LEFT"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        
        story.append(header_container)
        story.append(Spacer(1, 12*mm)) # Rritur nga 8mm
        
        # -------------------------------
        # AFATI PAGESES (Nëse ekziston)
        # -------------------------------
        if invoice.payment_due_date:
            details = [
                ["AFATI I PAGESËS"],
                [self.format_date(invoice.payment_due_date)]
            ]
            
            details_table = Table(details, colWidths=[60*mm])
            details_table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 11), # Rritur font i tabelës
                ("TOPPADDING", (0, 0), (-1, -1), 6), # Më shumë padding
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            
            # Alinjimi i tabelës në qendër
            container_table = Table([[details_table]], colWidths=[180*mm])
            container_table.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]))
            
            story.append(container_table)
            story.append(Spacer(1, 10*mm)) # Rritur nga 6mm
        
        # -------------------------------
        # ARTIKUJT
        # -------------------------------
        items = [
            ["PERSHKRIMI", "M²", "CMIMI", "NENTOTALI"]
        ]
        
        # Shto artikujt e faturave
        for item in invoice.items:
            items.append([
                item['description'],
                self.format_number(item['quantity']),
                self.format_number(item['unit_price'], with_currency=True),  # € për çmimin
                self.format_number(item['subtotal'], with_currency=True)  # € për nëntotalin
            ])
        
        # Shto rreshta bosh nëse ka pak artikuj (për të mbajtur strukturën)
        while len(items) < 6:
            items.append(["", "", "", ""])
        
        # Tabela me gjerësi të rregulluara për shuma të mëdha
        # [Përshkrimi, Sasia, Çmimi, Nëntotali]
        # Total gjerësia mbetet 185mm (85+25+35+40)
        items_table = Table(items, colWidths=[85*mm, 25*mm, 35*mm, 40*mm])
        items_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10), # Header font pak me i vogel
            ("FONTSIZE", (0, 1), (-1, -1), 10), # Content font pak me i vogel
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6), 
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        
        story.append(items_table)
        # Pa hapësirë midis tabelave - ngjitur direkt me tabelën e totalit
        
        # -------------------------------
        # TOTALI
        # -------------------------------
        legal_paragraph = ""
        if invoice.vat_percentage == 0:
            legal_text = "<i>Ngarkesa e kundert, nenparagrafi 1.4.1 ose 1.4.2 i nenit 52 te ligjit per TVSH</i>"
            legal_paragraph = Paragraph(legal_text, self.note_style)

        totals = [
            [legal_paragraph, "TOTAL PA TVSH", self.format_number(invoice.subtotal, with_currency=True)],
            ["", "TVSH %", f"{float(invoice.vat_percentage):.2f}%"],
            ["", "TVSH SHUMA", self.format_number(invoice.vat_amount, with_currency=True)],
            ["", "PER PAGESE", self.format_number(invoice.total, with_currency=True)],
        ]
        
        totals_table = Table(totals, colWidths=[95*mm, 50*mm, 40*mm])
        totals_table.setStyle(TableStyle([
            # Border vetëm për kolonën e shumave (kolona 2 tani)
            ("GRID", (2, 0), (2, -1), 1, colors.black),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (2, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), 
            
            # Teksti ligjor (kolona 0, rreshti 0 deri ne fund)
            ("SPAN", (0, 0), (0, 3)), # Shënimi shtrihet në kolonën e parë vertikalisht
            ("VALIGN", (0, 0), (0, 3), "TOP"), # Teksti fillon lart
            
            ("FONTSIZE", (1, 0), (1, -1), 10),
            ("FONTNAME", (1, 3), (1, 3), "Helvetica-Bold"),
            ("FONTNAME", (2, 3), (2, 3), "Helvetica-Bold"),
            ("FONTSIZE", (2, 3), (2, 3), 13),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            # Rregullim specifik për rreshtin e fundit (TOTALIN) 
            # Kolona e Vlerës (E djathta) - e ngritur lart
            ("TOPPADDING", (2, 3), (2, 3), 2),
            ("BOTTOMPADDING", (2, 3), (2, 3), 8),
            # Kolona e Labelës (PER PAGESE) - e ulur pak poshtë për t'u barazuar me numrin
            ("TOPPADDING", (1, 3), (1, 3), 6),
            ("BOTTOMPADDING", (1, 3), (1, 3), 5),
        ]))
        
        
        story.append(totals_table)
        
        story.append(Spacer(1, 40*mm))
        
        # -------------------------------
        # SIGNATURES
        # -------------------------------
        signatures = [
            ["Faturoi", "Pranoi"],
            ["____________________", "____________________"]
        ]
        
        # Gjerësia totale = 185mm (sa tabelat e tjera)
        # Ndahet në dy pjesë të barabarta
        signatures_table = Table(signatures, colWidths=[92.5*mm, 92.5*mm])
        signatures_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (0, -1), "LEFT"),     # Majtas
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),    # Djathtas
            
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 15),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            
            # Hapësirë më e madhe (25mm) për t'i afruar drejt qendrës
            ("LEFTPADDING", (0, 0), (0, -1), 40),  
            ("RIGHTPADDING", (1, 0), (1, -1), 40), 
        ]))
        
        story.append(signatures_table)
        
        # -------------------------------
        # BUILD
        # -------------------------------
        doc.build(story)
        return output_path
