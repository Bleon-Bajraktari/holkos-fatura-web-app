from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import models, schemas, database, os
from services.pdf_generator import WebPDFGenerator
from services.email_service import WebEmailService

app = FastAPI(title="Holkos Fatura API")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Holkos Fatura API is running"}

# --- INVOICES ---
@app.get("/invoices", response_model=List[schemas.Invoice])
def get_invoices(db: Session = Depends(get_db)):
    return db.query(models.Invoice).order_by(models.Invoice.date.desc()).all()

@app.get("/invoices/next-number")
def get_next_invoice_number(db: Session = Depends(get_db)):
    from datetime import date
    import re
    current_year = date.today().year
    
    # 1. Get prefix
    prefix = ""
    db_prefix = db.query(models.Setting).filter(models.Setting.setting_key == 'device_prefix').first()
    if db_prefix and db_prefix.setting_value:
        prefix = f"/{db_prefix.setting_value}"

    # 2. Get last invoice of the year
    max_inv = db.query(models.Invoice).filter(models.Invoice.date >= date(current_year, 1, 1)).order_by(models.Invoice.id.desc()).first()
    
    next_val = 1
    if max_inv:
        try:
            nums = re.findall(r'NR\.(\d+)', max_inv.invoice_number.upper())
            if nums:
                next_val = int(nums[0]) + 1
        except:
            pass
    
    return {"next_number": f"FATURA NR.{next_val}{prefix}"}

@app.post("/invoices", response_model=schemas.Invoice)
def create_invoice(invoice: schemas.InvoiceCreate, db: Session = Depends(get_db)):
    db_invoice = models.Invoice(**invoice.dict(exclude={'items'}))
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    
    for item in invoice.items:
        db_item = models.InvoiceItem(**item.dict(), invoice_id=db_invoice.id)
        db.add(db_item)
    
    db.commit()
    db.refresh(db_invoice)
    return db_invoice

@app.put("/invoices/{invoice_id}", response_model=schemas.Invoice)
def update_invoice(invoice_id: int, invoice: schemas.InvoiceCreate, db: Session = Depends(get_db)):
    db_invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not db_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Update main info
    for key, value in invoice.dict(exclude={'items'}).items():
        setattr(db_invoice, key, value)
    
    # Update items: Delete old and create new for simplicity (matches desktop app logic often)
    db.query(models.InvoiceItem).filter(models.InvoiceItem.invoice_id == invoice_id).delete()
    for item in invoice.items:
        db_item = models.InvoiceItem(**item.dict(), invoice_id=invoice_id)
        db.add(db_item)
    
    db.commit()
    db.refresh(db_invoice)
    return db_invoice

@app.get("/invoices/{invoice_id}", response_model=schemas.Invoice)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    db_invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if db_invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return db_invoice

@app.delete("/invoices/{invoice_id}")
def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    db_invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not db_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    db.delete(db_invoice)
    db.commit()
    return {"message": "Invoice deleted"}

@app.get("/invoices/{invoice_id}/pdf")
def get_invoice_pdf(invoice_id: int, db: Session = Depends(get_db)):
    db_invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not db_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    db_company = db.query(models.Company).first()
    db_client = db.query(models.Client).filter(models.Client.id == db_invoice.client_id).first()
    
    generator = WebPDFGenerator()
    pdf_path = generator.generate_invoice_pdf(db_invoice, db_company, db_client)
    
    return FileResponse(pdf_path, media_type='application/pdf', filename=os.path.basename(pdf_path), content_disposition_type='inline')
@app.get("/clients", response_model=List[schemas.Client])
def get_clients(db: Session = Depends(get_db)):
    return db.query(models.Client).order_by(models.Client.name).all()

@app.post("/clients", response_model=schemas.Client)
def create_client(client: schemas.ClientCreate, db: Session = Depends(get_db)):
    db_client = models.Client(**client.dict())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

# --- OFFERS ---
@app.get("/offers", response_model=List[schemas.Offer])
def get_offers(db: Session = Depends(get_db)):
    return db.query(models.Offer).order_by(models.Offer.date.desc()).all()

@app.get("/offers/next-number")
def get_next_offer_number(db: Session = Depends(get_db)):
    from datetime import date
    year = date.today().year
    max_off = db.query(models.Offer).filter(models.Offer.date >= date(year, 1, 1)).order_by(models.Offer.id.desc()).first()
    
    next_seq = 1
    if max_off:
        try:
            parts = max_off.offer_number.split('-')
            if len(parts) == 3:
                next_seq = int(parts[2]) + 1
        except:
            pass
            
    return {"next_number": f"OF-{year}-{next_seq:03d}"}

@app.post("/offers", response_model=schemas.Offer)
def create_offer(offer: schemas.OfferCreate, db: Session = Depends(get_db)):
    db_offer = models.Offer(**offer.dict(exclude={'items'}))
    db.add(db_offer)
    db.commit()
    db.refresh(db_offer)
    
    for item in offer.items:
        db_item = models.OfferItem(**item.dict(), offer_id=db_offer.id)
        db.add(db_item)
    
    db.commit()
    db.refresh(db_offer)
    return db_offer

@app.put("/offers/{offer_id}", response_model=schemas.Offer)
def update_offer(offer_id: int, offer: schemas.OfferCreate, db: Session = Depends(get_db)):
    db_offer = db.query(models.Offer).filter(models.Offer.id == offer_id).first()
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    for key, value in offer.dict(exclude={'items'}).items():
        setattr(db_offer, key, value)
    
    db.query(models.OfferItem).filter(models.OfferItem.offer_id == offer_id).delete()
    for item in offer.items:
        db_item = models.OfferItem(**item.dict(), offer_id=offer_id)
        db.add(db_item)
    
    db.commit()
    db.refresh(db_offer)
    return db_offer

@app.get("/offers/{offer_id}", response_model=schemas.Offer)
def get_offer(offer_id: int, db: Session = Depends(get_db)):
    db_offer = db.query(models.Offer).filter(models.Offer.id == offer_id).first()
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return db_offer

# --- DASHBOARD ---
@app.get("/dashboard/stats")
def get_stats(db: Session = Depends(get_db)):
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    now = datetime.now()
    first_day_current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    first_day_prev_month = (first_day_current_month - timedelta(days=1)).replace(day=1)
    
    total_invoices = db.query(func.count(models.Invoice.id)).scalar()
    total_offers = db.query(func.count(models.Offer.id)).scalar()
    total_revenue = db.query(func.sum(models.Invoice.total)).scalar() or 0
    total_clients = db.query(func.count(models.Client.id)).scalar()
    
    # Monthly Stats
    current_month_revenue = db.query(func.sum(models.Invoice.total)).filter(models.Invoice.date >= first_day_current_month).scalar() or 0
    prev_month_revenue = db.query(func.sum(models.Invoice.total)).filter(models.Invoice.date >= first_day_prev_month, models.Invoice.date < first_day_current_month).scalar() or 0
    
    # Growth calculation
    growth = 0
    if prev_month_revenue > 0:
        growth = ((current_month_revenue - prev_month_revenue) / prev_month_revenue) * 100
    elif current_month_revenue > 0:
        growth = 100
        
    # Recent Activity (simplified)
    recent_invoices = db.query(models.Invoice).order_by(models.Invoice.created_at.desc()).limit(3).all()
    recent_offers = db.query(models.Offer).order_by(models.Offer.created_at.desc()).limit(2).all()
    
    activity = []
    for inv in recent_invoices:
        activity.append({
            "type": "invoice",
            "number": inv.invoice_number,
            "amount": float(inv.total),
            "date": inv.created_at.isoformat(),
            "client": inv.client_name if hasattr(inv, 'client_name') else "Klient"
        })
    for off in recent_offers:
        activity.append({
            "type": "offer",
            "number": off.offer_number,
            "amount": float(off.total),
            "date": off.created_at.isoformat(),
            "client": off.client_name if hasattr(off, 'client_name') else "Klient"
        })
    
    # Sort activity by date
    activity.sort(key=lambda x: x['date'], reverse=True)

    return {
        "total_invoices": total_invoices,
        "total_offers": total_offers,
        "total_revenue": float(total_revenue),
        "total_clients": total_clients,
        "current_month_revenue": float(current_month_revenue),
        "growth": round(growth, 1),
        "recent_activity": activity[:5]
    }

# --- COMPANY ---
@app.get("/company", response_model=schemas.Company)
def get_company(db: Session = Depends(get_db)):
    db_company = db.query(models.Company).first()
    if db_company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return db_company

@app.put("/company", response_model=schemas.Company)
def update_company(company_update: schemas.CompanyUpdate, db: Session = Depends(get_db)):
    db_company = db.query(models.Company).first()
    if db_company is None:
        # Create one if it doesn't exist
        db_company = models.Company(**company_update.dict())
        db.add(db_company)
    else:
        for key, value in company_update.dict().items():
            setattr(db_company, key, value)
    
    db.commit()
    db.refresh(db_company)
    return db_company


@app.get("/offers/{offer_id}/pdf")
def get_offer_pdf(offer_id: int, db: Session = Depends(get_db)):
    db_offer = db.query(models.Offer).filter(models.Offer.id == offer_id).first()
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    db_company = db.query(models.Company).first()
    db_client = db.query(models.Client).filter(models.Client.id == db_offer.client_id).first()
    
    generator = WebPDFGenerator()
    pdf_path = generator.generate_offer_pdf(db_offer, db_company, db_client)
    
    return FileResponse(pdf_path, media_type='application/pdf', filename=os.path.basename(pdf_path), content_disposition_type='inline')

@app.post("/invoices/{invoice_id}/email")
def email_invoice(invoice_id: int, db: Session = Depends(get_db)):
    db_invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not db_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    db_company = db.query(models.Company).first()
    db_client = db.query(models.Client).filter(models.Client.id == db_invoice.client_id).first()
    
    if not db_client.email:
        raise HTTPException(status_code=400, detail="Klienti nuk ka adresë email-i.")
        
    generator = WebPDFGenerator()
    pdf_path = generator.generate_invoice_pdf(db_invoice, db_company, db_client)
    
    email_service = WebEmailService()
    success, message = email_service.send_document(db_invoice, db_company, db_client.email, pdf_path, is_offer=False)
    
    if not success:
        raise HTTPException(status_code=500, detail=message)
        
    return {"message": message}

@app.post("/offers/{offer_id}/email")
def email_offer(offer_id: int, db: Session = Depends(get_db)):
    db_offer = db.query(models.Offer).filter(models.Offer.id == offer_id).first()
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    db_company = db.query(models.Company).first()
    db_client = db.query(models.Client).filter(models.Client.id == db_offer.client_id).first()
    
    if not db_client.email:
        raise HTTPException(status_code=400, detail="Klienti nuk ka adresë email-i.")
        
    generator = WebPDFGenerator()
    pdf_path = generator.generate_offer_pdf(db_offer, db_company, db_client)
    
    email_service = WebEmailService()
    success, message = email_service.send_document(db_offer, db_company, db_client.email, pdf_path, is_offer=True)
    
    if not success:
        raise HTTPException(status_code=500, detail=message)
        
    return {"message": message}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
