from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import models, schemas, database
from services.pdf_generator import WebPDFGenerator

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

@app.get("/invoices/{invoice_id}", response_model=schemas.Invoice)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    db_invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if db_invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return db_invoice

@app.get("/invoices/{invoice_id}/pdf")
def get_invoice_pdf(invoice_id: int, db: Session = Depends(get_db)):
    db_invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not db_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    db_company = db.query(models.Company).first()
    db_client = db.query(models.Client).filter(models.Client.id == db_invoice.client_id).first()
    
    generator = WebPDFGenerator()
    pdf_path = generator.generate_invoice_pdf(db_invoice, db_company, db_client)
    
    return FileResponse(pdf_path, media_type='application/pdf', filename=os.path.basename(pdf_path))
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

# --- DASHBOARD ---
@app.get("/dashboard/stats")
def get_stats(db: Session = Depends(get_db)):
    from sqlalchemy import func
    total_invoices = db.query(func.count(models.Invoice.id)).scalar()
    total_revenue = db.query(func.sum(models.Invoice.total)).scalar() or 0
    total_clients = db.query(func.count(models.Client.id)).scalar()
    
    return {
        "total_invoices": total_invoices,
        "total_revenue": float(total_revenue),
        "total_clients": total_clients
    }

# --- COMPANY ---
@app.get("/company", response_model=schemas.Company)
def get_company(db: Session = Depends(get_db)):
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
@app.get("/invoices/next-number")
def get_next_invoice_number(db: Session = Depends(get_db)):
    from datetime import datetime
    year = datetime.now().year
    prefix = f"{year}-"
    max_inv = db.query(models.Invoice).filter(models.Invoice.invoice_number.like(f"{prefix}%")).order_by(models.Invoice.invoice_number.desc()).first()
    if max_inv:
        try:
            last_idx = int(max_inv.invoice_number.split("-")[-1])
            next_num = f"{prefix}{str(last_idx + 1).zfill(4)}"
        except:
            next_num = f"{prefix}0001"
    else:
        next_num = f"{prefix}0001"
    return {"next_number": next_num}

@app.get("/offers/next-number")
def get_next_offer_number(db: Session = Depends(get_db)):
    from datetime import datetime
    year = datetime.now().year
    prefix = f"O-{year}-"
    max_off = db.query(models.Offer).filter(models.Offer.offer_number.like(f"{prefix}%")).order_by(models.Offer.offer_number.desc()).first()
    if max_off:
        try:
            last_idx = int(max_off.offer_number.split("-")[-1])
            next_num = f"{prefix}{str(last_idx + 1).zfill(4)}"
        except:
            next_num = f"{prefix}0001"
    else:
        next_num = f"{prefix}0001"
    return {"next_number": next_num}

@app.get("/offers/{offer_id}/pdf")
def get_offer_pdf(offer_id: int, db: Session = Depends(get_db)):
    db_offer = db.query(models.Offer).filter(models.Offer.id == offer_id).first()
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    db_company = db.query(models.Company).first()
    db_client = db.query(models.Client).filter(models.Client.id == db_offer.client_id).first()
    
    generator = WebPDFGenerator()
    pdf_path = generator.generate_offer_pdf(db_offer, db_company, db_client)
    
    return FileResponse(pdf_path, media_type='application/pdf', filename=os.path.basename(pdf_path))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
