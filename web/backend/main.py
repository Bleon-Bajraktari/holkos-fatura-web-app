from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Query, Body, Header
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, extract, or_, cast, Integer, text
from typing import List, Optional
from datetime import date
import json
import models, schemas, database, os
from services.pdf_generator import WebPDFGenerator
from services.email_service import WebEmailService
from auth import decode_token

# Initialize global services
pdf_generator = WebPDFGenerator()
email_service = WebEmailService()

# Public paths (no auth required)
AUTH_SKIP_PATHS = {
    "/", "/health", "/auth/login", "/auth/refresh",
    "/docs", "/redoc", "/openapi.json",
    "/logo.png", "/apple-touch-icon.png", "/manifest.webmanifest",
}

def _is_public_path(path: str) -> bool:
    base = path.split("?")[0].rstrip("/") or "/"
    if base.startswith("/api/"):
        base = base[4:] or "/"
    if base in AUTH_SKIP_PATHS:
        return True
    if base.startswith("/auth/") or base.startswith("/uploads/"):
        return True
    return False

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)
        path = request.scope.get("path", "")
        if _is_public_path(path):
            return await call_next(request)
        auth_header = request.headers.get("Authorization")
        token = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        if not token or not decode_token(token):
            return JSONResponse(content={"detail": "Not authenticated"}, status_code=401)
        return await call_next(request)

app = FastAPI(title="Holkos Fatura API")

# Auth middleware (last added = runs first for incoming request)
app.add_middleware(AuthMiddleware)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Serve uploaded assets (e.g., company logo)
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# Startup: ekzekuto migrimin e DB (shto kolona qe mungojne)
@app.on_event("startup")
def run_db_migration():
    try:
        from update_db import update_db
        update_db()
    except Exception as e:
        import logging
        logging.warning(f"DB migration skipped or failed: {e}")

# Dependency to get DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- AUTH ---
def _ensure_auth_credentials(db: Session):
    """Krijo admin/holkos2025 vetëm nëse mungojnë. APP_FORCE_RESET_CREDENTIALS mbishkruan vetëm kur kredencialet janë bosh."""
    from auth import hash_password
    import os
    username = os.getenv("APP_INITIAL_USERNAME", "admin")
    password = os.getenv("APP_INITIAL_PASSWORD", "holkos2025")
    pw_hash = hash_password(password)
    changed = False
    for key, val in [("app_login_username", username), ("app_login_password", pw_hash)]:
        row = db.query(models.Setting).filter(models.Setting.setting_key == key).first()
        is_empty = not row or not (row.setting_value or "").strip()
        if is_empty:
            if row:
                row.setting_value = val
            else:
                db.add(models.Setting(setting_key=key, setting_value=val))
            changed = True
    if changed:
        db.commit()

@app.post("/auth/login", response_model=schemas.TokenResponse)
def login(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    from auth import verify_password, create_access_token
    _ensure_auth_credentials(db)
    username_row = db.query(models.Setting).filter(models.Setting.setting_key == "app_login_username").first()
    password_row = db.query(models.Setting).filter(models.Setting.setting_key == "app_login_password").first()
    if not username_row or not password_row or not (username_row.setting_value or "").strip():
        raise HTTPException(status_code=401, detail="Kredencialet nuk janë konfiguruar.")
    stored_username = (username_row.setting_value or "").strip()
    stored_hash = password_row.setting_value or ""
    if not stored_username or not stored_hash:
        raise HTTPException(status_code=401, detail="Kredencialet nuk janë konfiguruar.")
    if login_data.username.strip().lower() != stored_username.lower():
        raise HTTPException(status_code=401, detail="Emri i përdoruesit ose fjalëkalimi është i gabuar.")
    if not verify_password(login_data.password, stored_hash):
        raise HTTPException(status_code=401, detail="Emri i përdoruesit ose fjalëkalimi është i gabuar.")
    token = create_access_token(login_data.username)
    return schemas.TokenResponse(access_token=token, expires_in=1800)

@app.put("/auth/change-password")
def change_password(
    payload: schemas.ChangePasswordRequest,
    Authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db)
):
    from auth import verify_password, hash_password, decode_token
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token i munguar.")
    token = Authorization[7:].strip()
    token_data = decode_token(token)
    if not token_data or "sub" not in token_data:
        raise HTTPException(status_code=401, detail="Token i pavlefshëm.")
    username_row = db.query(models.Setting).filter(models.Setting.setting_key == "app_login_username").first()
    password_row = db.query(models.Setting).filter(models.Setting.setting_key == "app_login_password").first()
    if not username_row or not password_row:
        raise HTTPException(status_code=400, detail="Kredencialet nuk janë konfiguruar.")
    stored_hash = password_row.setting_value or ""
    if not verify_password(payload.current_password, stored_hash):
        raise HTTPException(status_code=400, detail="Fjalëkalimi aktual është i gabuar.")
    if len(payload.new_password) < 4:
        raise HTTPException(status_code=400, detail="Fjalëkalimi i ri duhet të ketë të paktën 4 karaktere.")
    password_row.setting_value = hash_password(payload.new_password)
    db.commit()
    return {"message": "Fjalëkalimi u ndryshua me sukses."}

@app.put("/auth/change-username")
def change_username(
    payload: schemas.ChangeUsernameRequest,
    Authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db)
):
    from auth import verify_password, decode_token, create_access_token
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token i munguar.")
    token = Authorization[7:].strip()
    token_data = decode_token(token)
    if not token_data or "sub" not in token_data:
        raise HTTPException(status_code=401, detail="Token i pavlefshëm.")
    username_row = db.query(models.Setting).filter(models.Setting.setting_key == "app_login_username").first()
    password_row = db.query(models.Setting).filter(models.Setting.setting_key == "app_login_password").first()
    if not username_row or not password_row:
        raise HTTPException(status_code=400, detail="Kredencialet nuk janë konfiguruar.")
    stored_hash = password_row.setting_value or ""
    if not verify_password(payload.current_password, stored_hash):
        raise HTTPException(status_code=400, detail="Fjalëkalimi është i gabuar.")
    new_username = (payload.new_username or "").strip()
    if len(new_username) < 2:
        raise HTTPException(status_code=400, detail="Emri i përdoruesit duhet të ketë të paktën 2 karaktere.")
    username_row.setting_value = new_username
    db.commit()
    new_token = create_access_token(new_username)
    return {"message": "Emri i përdoruesit u ndryshua me sukses.", "access_token": new_token, "token_type": "bearer", "expires_in": 1800}

@app.post("/auth/refresh", response_model=schemas.TokenResponse)
def refresh_token(Authorization: Optional[str] = Header(None, alias="Authorization")):
    from auth import decode_token, create_access_token
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token i munguar ose i pavlefshëm.")
    token = Authorization[7:].strip()
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Token i skaduar ose i pavlefshëm.")
    new_token = create_access_token(payload["sub"])
    return schemas.TokenResponse(access_token=new_token, expires_in=1800)
def read_root():
    return {"message": "Holkos Fatura API is running"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Verifikon që API dhe databaza funksionojnë."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "database": str(e)},
            status_code=500,
        )

@app.get("/email/status")
def email_status(db: Session = Depends(get_db)):
    """Kontrollon konfigurimin e email-it për diagnostikim."""
    db_company = db.query(models.Company).first()
    smtp_ok = bool(db_company and db_company.smtp_user and db_company.smtp_password)
    return {
        "smtp_configured": smtp_ok,
        "mode": "smtp" if smtp_ok else "none",
        "message": "OK - SMTP" if smtp_ok else "Plotëso SMTP në Cilësimet.",
    }

# --- INVOICES ---
@app.get("/invoices")
def get_invoices(
    search: str = None,
    status: str = None,
    date_from: date = None,
    date_to: date = None,
    client_id: int = None,
    db: Session = Depends(get_db)
):
    try:
        query = db.query(models.Invoice).options(
            joinedload(models.Invoice.client),
            joinedload(models.Invoice.items)
        )
        
        if client_id:
            query = query.filter(models.Invoice.client_id == client_id)
        if status:
            query = query.filter(models.Invoice.status == status)
        if date_from:
            query = query.filter(models.Invoice.date >= date_from)
        if date_to:
            query = query.filter(models.Invoice.date <= date_to)
        if search:
            query = query.outerjoin(models.Client).filter(
                or_(
                    models.Invoice.invoice_number.ilike(f"%{search}%"),
                    models.Client.name.ilike(f"%{search}%")
                )
            )
        
        invoices = query.order_by(
            models.Invoice.date.desc(),
            models.Invoice.id.desc()
        ).all()
        
        result = []
        for inv in invoices:
            invoice_dict = {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "date": str(inv.date),
                "payment_due_date": str(inv.payment_due_date) if inv.payment_due_date else None,
                "client_id": inv.client_id,
                "template_id": inv.template_id,
                "subtotal": float(inv.subtotal),
                "vat_percentage": float(inv.vat_percentage),
                "vat_amount": float(inv.vat_amount),
                "total": float(inv.total),
                "status": inv.status,
                "pdf_path": inv.pdf_path,
                "created_at": str(inv.created_at),
                "updated_at": str(inv.updated_at),
                "client": {
                    "id": inv.client.id,
                    "name": inv.client.name,
                    "address": inv.client.address or "",
                    "unique_number": inv.client.unique_number or "",
                    "phone": inv.client.phone or "",
                    "email": inv.client.email or "",
                    "created_at": str(inv.client.created_at),
                    "updated_at": str(inv.client.updated_at)
                } if inv.client else None,
                "items": [{
                    "id": item.id,
                    "invoice_id": item.invoice_id,
                    "description": item.description,
                    "quantity": float(item.quantity),
                    "unit_price": float(item.unit_price),
                    "subtotal": float(item.subtotal),
                    "order_index": item.order_index or 0
                } for item in inv.items]
            }
            result.append(invoice_dict)
        
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

def _get_next_val(db: Session, year: int, doc_type: str = 'invoice'):
    import re
    from datetime import date
    model = models.Invoice if doc_type == 'invoice' else models.Offer
    
    # Get last items of the year/period
    query = db.query(model)
    if doc_type == 'invoice':
        query = query.filter(model.date >= date(year, 1, 1), model.date < date(year + 1, 1, 1))
    
    items = query.order_by(model.id.desc()).limit(20).all()
    
    max_val = 0
    pattern = r'NR\.(\d+)' if doc_type == 'invoice' else r'NR\.(\d+)' # Assuming same pattern
    
    for item in items:
        num_str = item.invoice_number if doc_type == 'invoice' else item.offer_number
        try:
            nums = re.findall(pattern, num_str.upper())
            if nums:
                val = int(nums[0])
                if val > max_val: max_val = val
        except: pass
    return max_val + 1

@app.get("/invoices/next-number")
def get_next_invoice_number(db: Session = Depends(get_db)):
    from datetime import date
    current_year = date.today().year
    prefix = ""
    db_prefix = db.query(models.Setting).filter(models.Setting.setting_key == 'device_prefix').first()
    if db_prefix and db_prefix.setting_value:
        prefix = f"/{db_prefix.setting_value}"
    
    next_val = _get_next_val(db, current_year, 'invoice')
    return {"next_number": f"FATURA NR.{next_val}{prefix}"}

@app.get("/invoices/years")
def get_invoice_years(db: Session = Depends(get_db)):
    years = db.query(extract('year', models.Invoice.date).label("year")).distinct().order_by(extract('year', models.Invoice.date).desc()).all()
    result = [str(y.year) for y in years if y.year]
    if not result:
        result = [str(date.today().year)]
    return {"years": result}

@app.post("/invoices", response_model=schemas.Invoice)
def create_invoice(invoice: schemas.InvoiceCreate, db: Session = Depends(get_db)):
    try:
        return _create_invoice_impl(invoice, db)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

def _create_invoice_impl(invoice: schemas.InvoiceCreate, db: Session):
    from datetime import date as dt_date
    
    # Check for duplicate within the same year
    year = invoice.date.year
    year_start = dt_date(year, 1, 1)
    year_end = dt_date(year + 1, 1, 1)
    
    existing = db.query(models.Invoice).filter(
        models.Invoice.invoice_number == invoice.invoice_number,
        models.Invoice.date >= year_start,
        models.Invoice.date < year_end
    ).first()
    
    target_number = invoice.invoice_number
    
    if existing:
        # Conflict Resolution Logic: "Earlier one gets the number"
        new_ts = invoice.save_timestamp or dt_date.today()
        ext_ts = existing.save_timestamp or existing.created_at
        
        # Ensure comparison works (naive vs aware or datetime vs date)
        if hasattr(new_ts, 'timestamp') and hasattr(ext_ts, 'timestamp'):
             is_earlier = new_ts < ext_ts
        else:
             is_earlier = False # Fallback

        if is_earlier:
            # Shift existing one to next available
            next_val = _get_next_val(db, year, 'invoice')
            # Extract prefix from existing
            import re
            parts = re.split(r'NR\.\d+', existing.invoice_number)
            prefix = parts[1] if len(parts) > 1 else ""
            existing.invoice_number = f"FATURA NR.{next_val}{prefix}"
            existing.pdf_path = None # Invalidate PDF
            db.commit()
        else:
            # Adjust incoming one to next available
            next_val = _get_next_val(db, year, 'invoice')
            import re
            parts = re.split(r'NR\.\d+', target_number)
            prefix = parts[1] if len(parts) > 1 else ""
            target_number = f"FATURA NR.{next_val}{prefix}"

    # Remove client_name if present (not in schema)
    invoice_data = invoice.dict(exclude={'items', 'client_name'})
    invoice_data['invoice_number'] = target_number
    db_invoice = models.Invoice(**invoice_data)
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    
    # Add items
    for item in invoice.items:
        db_item = models.InvoiceItem(**item.dict(), invoice_id=db_invoice.id)
        db.add(db_item)
    
    db.commit()
    
    # Reload with relationships
    db_invoice = db.query(models.Invoice).options(
        joinedload(models.Invoice.client),
        joinedload(models.Invoice.items)
    ).filter(models.Invoice.id == db_invoice.id).first()
    
    return db_invoice

@app.put("/invoices/{invoice_id}", response_model=schemas.Invoice)
def update_invoice(invoice_id: int, invoice: schemas.InvoiceCreate, db: Session = Depends(get_db)):
    from datetime import date as dt_date
    
    db_invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not db_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Check for duplicate if number changed (within same year)
    if db_invoice.invoice_number != invoice.invoice_number:
        year = invoice.date.year
        year_start = dt_date(year, 1, 1)
        year_end = dt_date(year + 1, 1, 1)
        
        existing = db.query(models.Invoice).filter(
            models.Invoice.invoice_number == invoice.invoice_number,
            models.Invoice.date >= year_start,
            models.Invoice.date < year_end
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Fatura me numrin '{invoice.invoice_number}' ekziston për vitin {year}!")

    # Update main info (exclude client_name if present)
    invoice_data = invoice.dict(exclude={'items', 'client_name'})
    for key, value in invoice_data.items():
        setattr(db_invoice, key, value)
    
    # Invalidate PDF cache
    db_invoice.pdf_path = None
    
    # Update items: Delete old and create new for simplicity
    db.query(models.InvoiceItem).filter(models.InvoiceItem.invoice_id == invoice_id).delete()
    for item in invoice.items:
        db_item = models.InvoiceItem(**item.dict(), invoice_id=invoice_id)
        db.add(db_item)
    
    db.commit()
    
    # Reload with relationships
    db_invoice = db.query(models.Invoice).options(
        joinedload(models.Invoice.client),
        joinedload(models.Invoice.items)
    ).filter(models.Invoice.id == invoice_id).first()
    
    return db_invoice

@app.get("/invoices/{invoice_id}", response_model=schemas.Invoice)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    db_invoice = db.query(models.Invoice).options(
        joinedload(models.Invoice.client),
        joinedload(models.Invoice.items)
    ).filter(models.Invoice.id == invoice_id).first()
    
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

@app.put("/invoices/{invoice_id}/status")
def update_invoice_status(invoice_id: int, status_update: schemas.StatusUpdate, db: Session = Depends(get_db)):
    db_invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not db_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    db_invoice.status = status_update.status
    db.commit()
    return {"id": db_invoice.id, "status": db_invoice.status}

@app.post("/invoices/bulk-delete")
def bulk_delete_invoices(req: schemas.BulkDeleteRequest, db: Session = Depends(get_db)):
    if not req.invoice_ids:
        return {"deleted": 0}
    db.query(models.InvoiceItem).filter(models.InvoiceItem.invoice_id.in_(req.invoice_ids)).delete(synchronize_session=False)
    deleted = db.query(models.Invoice).filter(models.Invoice.id.in_(req.invoice_ids)).delete(synchronize_session=False)
    db.commit()
    return {"deleted": deleted}

@app.post("/invoices/bulk-email")
def bulk_email_invoices(req: schemas.BulkEmailRequest, db: Session = Depends(get_db)):
    if not req.invoice_ids:
        return {"success": 0, "failed": 0, "errors": []}
    
    db_company = db.query(models.Company).first()
    if not db_company:
        raise HTTPException(status_code=400, detail="Company not found")
    
    invoices = db.query(models.Invoice).options(
        joinedload(models.Invoice.client)
    ).filter(models.Invoice.id.in_(req.invoice_ids)).all()

    found_by_id = {inv.id: inv for inv in invoices}
    missing_ids = [inv_id for inv_id in req.invoice_ids if inv_id not in found_by_id]
    if missing_ids:
        raise HTTPException(status_code=404, detail=f"Faturat nuk u gjetën: {', '.join(map(str, missing_ids))}")

    ordered_invoices = [found_by_id[inv_id] for inv_id in req.invoice_ids]

    dest_email = req.override_email
    if not dest_email:
        emails = {inv.client.email for inv in ordered_invoices if inv.client and inv.client.email}
        if len(emails) == 1:
            dest_email = next(iter(emails))
        else:
            raise HTTPException(status_code=400, detail="Zgjidhni një email për dërgimin e faturave.")

    pdf_paths = []
    for inv in ordered_invoices:
        pdf_path = inv.pdf_path
        if not pdf_path or not os.path.exists(pdf_path):
            pdf_path = pdf_generator.generate_invoice_pdf(inv, db_company, inv.client)
            inv.pdf_path = pdf_path
            db.commit()
        pdf_paths.append(pdf_path)

    email_service = WebEmailService()
    ok, msg = email_service.send_bulk_documents(ordered_invoices, db_company, dest_email, pdf_paths)
    if not ok:
        raise HTTPException(status_code=500, detail=msg)

    return {"success": len(ordered_invoices), "failed": 0, "errors": []}

@app.get("/invoices/{invoice_id}/pdf")
def get_invoice_pdf(invoice_id: int, db: Session = Depends(get_db)):
    db_invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not db_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Check if PDF already exists
    if db_invoice.pdf_path:
        if db_invoice.pdf_path.startswith(('http://', 'https://')):
            from fastapi.responses import RedirectResponse
            return RedirectResponse(db_invoice.pdf_path)
        elif os.path.exists(db_invoice.pdf_path):
            return FileResponse(
                db_invoice.pdf_path,
                media_type='application/pdf',
                filename=os.path.basename(db_invoice.pdf_path),
                headers={"Content-Disposition": f'inline; filename="{os.path.basename(db_invoice.pdf_path)}"'}
            )

    db_company = db.query(models.Company).first()
    db_client = db.query(models.Client).filter(models.Client.id == db_invoice.client_id).first()
    
    pdf_path = pdf_generator.generate_invoice_pdf(db_invoice, db_company, db_client)
    db_invoice.pdf_path = pdf_path
    db.commit()
    
    return FileResponse(
        pdf_path,
        media_type='application/pdf',
        filename=os.path.basename(pdf_path),
        headers={"Content-Disposition": f'inline; filename="{os.path.basename(pdf_path)}"'}
    )
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

@app.put("/clients/{client_id}", response_model=schemas.Client)
def update_client(client_id: int, client: schemas.ClientCreate, db: Session = Depends(get_db)):
    db_client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")
    for key, value in client.dict().items():
        setattr(db_client, key, value)
    db.commit()
    db.refresh(db_client)
    return db_client

@app.delete("/clients/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    db_client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")
    db.delete(db_client)
    db.commit()
    return {"message": "Client deleted"}

# --- OFFERS ---
@app.get("/offers", response_model=List[schemas.Offer])
def get_offers(
    search: str = None,
    date_from: date = None,
    date_to: date = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Offer).options(
        joinedload(models.Offer.client),
        joinedload(models.Offer.items)
    )
    
    if date_from:
        query = query.filter(models.Offer.date >= date_from)
    if date_to:
        query = query.filter(models.Offer.date <= date_to)
    if search:
        query = query.outerjoin(models.Client).filter(
            or_(
                models.Offer.offer_number.ilike(f"%{search}%"),
                models.Client.name.ilike(f"%{search}%"),
                models.Offer.subject.ilike(f"%{search}%")
            )
        )
    
    # Sort by offer number sequence (like desktop app)
    # Extract number from "OFERTA NR.XX" or "OF-YYYY-XXX" format and sort by it
    return query.order_by(
        text("""
            CAST(
                CASE 
                    WHEN offers.offer_number LIKE 'OFERTA NR.%' 
                    THEN CAST(SUBSTRING_INDEX(offers.offer_number, '.', -1) AS UNSIGNED)
                    WHEN offers.offer_number LIKE 'OF-%-%' 
                    THEN CAST(SUBSTRING_INDEX(offers.offer_number, '-', -1) AS UNSIGNED)
                    ELSE 0
                END AS UNSIGNED
            ) DESC
        """),
        models.Offer.id.desc()
    ).all()

@app.get("/offers/next-number")
def get_next_offer_number(db: Session = Depends(get_db)):
    # Get the last offer to find max sequence number
    # Format: "OFERTA NR.XX" where XX is sequential number
    last_offer = db.query(models.Offer).order_by(models.Offer.id.desc()).first()
    
    if last_offer:
        try:
            # Try to extract number from "OFERTA NR.XX" format
            offer_num = last_offer.offer_number.upper()
            if "NR." in offer_num:
                # Extract number after "NR."
                num_part = offer_num.split("NR.")[-1].strip()
                next_seq = int(num_part) + 1
                return {"next_number": f"OFERTA NR.{next_seq}"}
            # Try old format "OF-YYYY-XXX"
            elif "-" in offer_num:
                parts = offer_num.split("-")
                if len(parts) >= 3:
                    num_part = parts[-1].strip()
                    next_seq = int(num_part) + 1
                    return {"next_number": f"OFERTA NR.{next_seq}"}
        except (ValueError, IndexError):
            pass
    
    # Default: first offer
    return {"next_number": "OFERTA NR.1"}

@app.get("/offers/years")
def get_offer_years(db: Session = Depends(get_db)):
    years = db.query(extract('year', models.Offer.date).label("year")).distinct().order_by(extract('year', models.Offer.date).desc()).all()
    result = [str(y.year) for y in years if y.year]
    if not result:
        result = [str(date.today().year)]
    return {"years": result}

@app.post("/offers", response_model=schemas.Offer)
def create_offer(offer: schemas.OfferCreate, db: Session = Depends(get_db)):
    def normalize_custom_attributes(value):
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return value
    
    # Check for duplicate within the same year
    from datetime import date as dt_date
    year = offer.date.year
    year_start = dt_date(year, 1, 1)
    year_end = dt_date(year + 1, 1, 1)
    
    existing = db.query(models.Offer).filter(
        models.Offer.offer_number == offer.offer_number,
        models.Offer.date >= year_start,
        models.Offer.date < year_end
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Oferta me numrin '{offer.offer_number}' ekziston për vitin {year}!")

    db_offer = models.Offer(**offer.dict(exclude={'items'}))
    db.add(db_offer)
    db.commit()
    db.refresh(db_offer)
    
    for idx, item in enumerate(offer.items):
        item_data = item.dict()
        item_data["custom_attributes"] = normalize_custom_attributes(item_data.get("custom_attributes"))
        # Set order_index if not provided
        if "order_index" not in item_data or item_data["order_index"] is None:
            item_data["order_index"] = idx
        db_item = models.OfferItem(**item_data, offer_id=db_offer.id)
        db.add(db_item)
    
    db.commit()
    db.refresh(db_offer)
    return db_offer

@app.put("/offers/{offer_id}", response_model=schemas.Offer)
def update_offer(offer_id: int, offer: schemas.OfferCreate, db: Session = Depends(get_db)):
    def normalize_custom_attributes(value):
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return value
    
    db_offer = db.query(models.Offer).filter(models.Offer.id == offer_id).first()
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    # Check for duplicate if number changed (within same year)
    from datetime import date as dt_date
    if db_offer.offer_number != offer.offer_number:
        year = offer.date.year
        year_start = dt_date(year, 1, 1)
        year_end = dt_date(year + 1, 1, 1)
        
        existing = db.query(models.Offer).filter(
            models.Offer.offer_number == offer.offer_number,
            models.Offer.date >= year_start,
            models.Offer.date < year_end
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Oferta me numrin '{offer.offer_number}' ekziston për vitin {year}!")

    for key, value in offer.dict(exclude={'items'}).items():
        setattr(db_offer, key, value)
    
    # Invalidate PDF cache
    db_offer.pdf_path = None
    
    db.query(models.OfferItem).filter(models.OfferItem.offer_id == offer_id).delete()
    for idx, item in enumerate(offer.items):
        item_data = item.dict()
        item_data["custom_attributes"] = normalize_custom_attributes(item_data.get("custom_attributes"))
        # Set order_index if not provided
        if "order_index" not in item_data or item_data["order_index"] is None:
            item_data["order_index"] = idx
        db_item = models.OfferItem(**item_data, offer_id=offer_id)
        db.add(db_item)
    
    db.commit()
    db.refresh(db_offer)
    return db_offer

@app.get("/offers/{offer_id}", response_model=schemas.Offer)
def get_offer(offer_id: int, db: Session = Depends(get_db)):
    db_offer = db.query(models.Offer).options(
        joinedload(models.Offer.client),
        joinedload(models.Offer.items)
    ).filter(models.Offer.id == offer_id).first()
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return db_offer

@app.delete("/offers/{offer_id}")
def delete_offer(offer_id: int, db: Session = Depends(get_db)):
    db_offer = db.query(models.Offer).filter(models.Offer.id == offer_id).first()
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    db.delete(db_offer)
    db.commit()
    return {"message": "Offer deleted"}

@app.post("/offers/bulk-delete")
def bulk_delete_offers(req: schemas.BulkDeleteOfferRequest, db: Session = Depends(get_db)):
    if not req.offer_ids:
        return {"deleted": 0}
    db.query(models.OfferItem).filter(models.OfferItem.offer_id.in_(req.offer_ids)).delete(synchronize_session=False)
    deleted = db.query(models.Offer).filter(models.Offer.id.in_(req.offer_ids)).delete(synchronize_session=False)
    db.commit()
    return {"deleted": deleted}

@app.post("/offers/bulk-email")
def bulk_email_offers(req: schemas.BulkEmailOfferRequest, db: Session = Depends(get_db)):
    if not req.offer_ids:
        return {"success": 0, "failed": 0, "errors": []}
    
    db_company = db.query(models.Company).first()
    if not db_company:
        raise HTTPException(status_code=400, detail="Company not found")
    
    offers = db.query(models.Offer).options(
        joinedload(models.Offer.client)
    ).filter(models.Offer.id.in_(req.offer_ids)).all()

    found_by_id = {off.id: off for off in offers}
    missing_ids = [off_id for off_id in req.offer_ids if off_id not in found_by_id]
    if missing_ids:
        raise HTTPException(status_code=404, detail=f"Ofertat nuk u gjetën: {', '.join(map(str, missing_ids))}")

    ordered_offers = [found_by_id[off_id] for off_id in req.offer_ids]

    dest_email = req.override_email
    if not dest_email:
        emails = {off.client.email for off in ordered_offers if off.client and off.client.email}
        if len(emails) == 1:
            dest_email = next(iter(emails))
        else:
            raise HTTPException(status_code=400, detail="Zgjidhni një email për dërgimin e ofertave.")

    pdf_paths = []
    for off in ordered_offers:
        pdf_path = off.pdf_path
        if not pdf_path or not os.path.exists(pdf_path):
            pdf_path = pdf_generator.generate_offer_pdf(off, db_company, off.client)
            off.pdf_path = pdf_path
            db.commit()
        pdf_paths.append(pdf_path)

    email_service = WebEmailService()
    ok, msg = email_service.send_bulk_documents(ordered_offers, db_company, dest_email, pdf_paths, is_offer=True)
    if not ok:
        raise HTTPException(status_code=500, detail=msg)

    return {"success": len(ordered_offers), "failed": 0, "errors": []}

# --- DASHBOARD ---
@app.get("/dashboard/stats")
def get_stats(db: Session = Depends(get_db)):
    from datetime import datetime, timedelta
    
    now = datetime.now()
    first_day_current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    first_day_prev_month = (first_day_current_month - timedelta(days=1)).replace(day=1)
    
    total_invoices = db.query(func.count(models.Invoice.id)).scalar()
    total_offers = db.query(func.count(models.Offer.id)).scalar()
    total_revenue = db.query(func.sum(models.Invoice.total)).scalar() or 0
    total_vat = db.query(func.sum(models.Invoice.vat_amount)).scalar() or 0
    total_clients = db.query(func.count(models.Client.id)).scalar()
    
    # Monthly Stats
    current_month_revenue = db.query(func.sum(models.Invoice.total)).filter(models.Invoice.date >= first_day_current_month).scalar() or 0
    prev_month_revenue = db.query(func.sum(models.Invoice.total)).filter(models.Invoice.date >= first_day_prev_month, models.Invoice.date < first_day_current_month).scalar() or 0
    current_month_invoices = db.query(func.count(models.Invoice.id)).filter(models.Invoice.date >= first_day_current_month).scalar() or 0
    
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
        client_name = (inv.client.name if inv.client else None) or "Klient"
        activity.append({
            "type": "invoice",
            "number": inv.invoice_number,
            "amount": float(inv.total),
            "date": (inv.created_at or inv.date).isoformat() if inv.created_at or inv.date else "",
            "client": client_name
        })
    for off in recent_offers:
        client_name = (off.client.name if off.client else None) or "Klient"
        activity.append({
            "type": "offer",
            "number": off.offer_number,
            "amount": float(off.total),
            "date": (off.created_at or off.date).isoformat() if off.created_at or off.date else "",
            "client": client_name
        })
    
    # Sort activity by date
    activity.sort(key=lambda x: x['date'], reverse=True)

    return {
        "total_invoices": total_invoices,
        "total_offers": total_offers,
        "total_revenue": float(total_revenue),
        "total_vat": float(total_vat),
        "total_clients": total_clients,
        "current_month_revenue": float(current_month_revenue),
        "month_invoices": current_month_invoices,
        "growth": round(growth, 1),
        "recent_activity": activity[:5]
    }

# --- COMPANY ---
@app.get("/company", response_model=schemas.Company)
def get_company(db: Session = Depends(get_db)):
    db_company = db.query(models.Company).first()
    if db_company is None:
        # Krijo kompani të zbrazët në hyrjen e parë – përdoruesi mund ta plotësojë nga Cilësimet
        db_company = models.Company(
            name="Kompania ime",
            address=None, phone=None, email=None,
            unique_number=None, fiscal_number=None, account_nib=None, logo_path=None,
            smtp_server="smtp.gmail.com", smtp_port=587, smtp_user=None, smtp_password=None
        )
        db.add(db_company)
        db.commit()
        db.refresh(db_company)
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

@app.post("/company/logo", response_model=schemas.Company)
def upload_company_logo(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Lejohen vetëm imazhe për logo.")

    db_company = db.query(models.Company).first()
    if db_company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(file.filename or "")[1].lower() or ".png"
    filename = f"company_logo{ext}"
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    db_company.logo_path = os.path.join("uploads", filename).replace("\\", "/")
    db.commit()
    db.refresh(db_company)
    return db_company

@app.get("/logo.png")
def get_logo_icon(db: Session = Depends(get_db), size: int = 512):
    """
    Kthen logo-n e kompanisë të optimizuar për PWA.
    Konverton dhe resize-on logo-n në madhësi të specifikuar (default 512x512).
    """
    from datetime import datetime
    from io import BytesIO
    from PIL import Image as PILImage, ImageDraw, ImageFont
    import tempfile
    
    print(f"[DEBUG] Fetching logo.png at {datetime.now()}, size={size}")
    
    company = db.query(models.Company).first()
    logo_path = None
    
    if company and company.logo_path:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_dir, company.logo_path.replace("\\", "/").lstrip("/"))
        if os.path.exists(full_path):
            logo_path = full_path
    
    # Fallback: try to serve from frontend public folder
    if not logo_path:
        frontend_public = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "public", "icon-512.png")
        if os.path.exists(frontend_public):
            logo_path = frontend_public
    
    if logo_path:
        try:
            # Hap logo-n me PIL
            img = PILImage.open(logo_path)
            
            # Konverto në RGBA nëse nuk është
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Krijon një background transparent
            background = PILImage.new('RGBA', (size, size), (255, 255, 255, 0))
            
            # Llogarit dimensionet për të mbajtur aspect ratio
            img.thumbnail((size, size), PILImage.Resampling.LANCZOS)
            
            # Vendos logo-n në qendër të background-it
            x_offset = (size - img.width) // 2
            y_offset = (size - img.height) // 2
            background.paste(img, (x_offset, y_offset), img)
            
            # Konverto në RGB me background të bardhë për kompatibilitet më të mirë
            final_img = PILImage.new('RGB', (size, size), (255, 255, 255))
            final_img.paste(background, mask=background.split()[3] if background.mode == 'RGBA' else None)
            
            # Ruaj në buffer
            buffer = BytesIO()
            final_img.save(buffer, format='PNG', optimize=True)
            buffer.seek(0)
            
            return Response(
                content=buffer.getvalue(),
                media_type="image/png",
                headers={
                    "Cache-Control": "public, max-age=3600"
                }
            )
        except Exception as e:
            print(f"[ERROR] Error processing logo: {e}")
            # Nëse ka gabim, kthe logo-n origjinale
            if os.path.exists(logo_path):
                return FileResponse(logo_path, media_type="image/png", headers={
                    "Cache-Control": "public, max-age=3600"
                })
    
    # Final fallback: Krijon një logo default me emrin e kompanisë
    try:
        company_name = company.name if company and company.name else "HOLKOS"
        # Merr shkronjën e parë ose dy shkronjat e para
        initials = company_name[:2].upper() if len(company_name) >= 2 else company_name[0].upper() if company_name else "H"
        
        # Krijon një imazh me background të bardhë
        img = PILImage.new('RGB', (size, size), (17, 24, 39))  # #111827 - theme color
        draw = ImageDraw.Draw(img)
        
        # Përpiqet të përdorë një font, ose default
        try:
            font_size = int(size * 0.4)
            # Përpiqet të përdorë font të sistemit
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
                except:
                    font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Llogarit pozicionin për tekstin
        bbox = draw.textbbox((0, 0), initials, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size - text_width) // 2
        y = (size - text_height) // 2
        
        # Vizaton tekstin në qendër
        draw.text((x, y), initials, fill=(255, 255, 255), font=font)
        
        # Ruaj në buffer
        buffer = BytesIO()
        img.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)
        
        return Response(
            content=buffer.getvalue(),
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=3600"
            }
        )
    except Exception as e:
        print(f"[ERROR] Error creating default logo: {e}")
        return JSONResponse({"error": "Icon not found"}, status_code=404)

@app.get("/apple-touch-icon.png")
def get_apple_touch_icon(db: Session = Depends(get_db)):
    """
    Kthen apple-touch-icon të optimizuar për iOS (180x180).
    iOS kërkon background të bardhë dhe madhësi saktësisht 180x180.
    """
    from datetime import datetime
    from io import BytesIO
    from PIL import Image as PILImage, ImageDraw, ImageFont
    
    size = 180  # iOS kërkon saktësisht 180x180
    print(f"[DEBUG] Fetching apple-touch-icon.png at {datetime.now()}")
    
    company = db.query(models.Company).first()
    logo_path = None
    
    if company and company.logo_path:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_dir, company.logo_path.replace("\\", "/").lstrip("/"))
        if os.path.exists(full_path):
            logo_path = full_path
    
    # Fallback: try to serve from frontend public folder
    if not logo_path:
        frontend_public = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "public", "icon-512.png")
        if os.path.exists(frontend_public):
            logo_path = frontend_public
    
    if logo_path:
        try:
            # Hap logo-n me PIL
            img = PILImage.open(logo_path)
            
            # Konverto në RGBA nëse nuk është
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Krijon një background të bardhë (iOS kërkon background të bardhë, jo transparent)
            background = PILImage.new('RGB', (size, size), (255, 255, 255))
            
            # Llogarit dimensionet për të mbajtur aspect ratio dhe të përshtatet brenda
            # Lëmë pak padding (10%) për të shmangur që logoja të prekë skajet
            max_size = int(size * 0.8)
            img.thumbnail((max_size, max_size), PILImage.Resampling.LANCZOS)
            
            # Vendos logo-n në qendër të background-it
            x_offset = (size - img.width) // 2
            y_offset = (size - img.height) // 2
            
            # Nëse logoja ka transparency, përdor mask
            if img.mode == 'RGBA':
                background.paste(img, (x_offset, y_offset), img)
            else:
                background.paste(img, (x_offset, y_offset))
            
            # Ruaj në buffer
            buffer = BytesIO()
            background.save(buffer, format='PNG', optimize=True)
            buffer.seek(0)
            
            return Response(
                content=buffer.getvalue(),
                media_type="image/png",
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
        except Exception as e:
            print(f"[ERROR] Error processing apple-touch-icon: {e}")
            # Nëse ka gabim, krijo default
            pass
    
    # Fallback: Krijon një logo default me emrin e kompanisë
    try:
        company_name = company.name if company and company.name else "HOLKOS"
        # Merr shkronjën e parë ose dy shkronjat e para
        initials = company_name[:2].upper() if len(company_name) >= 2 else company_name[0].upper() if company_name else "H"
        
        # Krijon një imazh me background të bardhë (iOS kërkon të bardhë)
        img = PILImage.new('RGB', (size, size), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Krijon një background të rrumbullakët me ngjyrën e temës
        padding = 20
        draw.ellipse([padding, padding, size - padding, size - padding], fill=(17, 24, 39))  # #111827
        
        # Përpiqet të përdorë një font
        try:
            font_size = int(size * 0.35)
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
                except:
                    font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Llogarit pozicionin për tekstin
        bbox = draw.textbbox((0, 0), initials, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size - text_width) // 2
        y = (size - text_height) // 2
        
        # Vizaton tekstin në qendër
        draw.text((x, y), initials, fill=(255, 255, 255), font=font)
        
        # Ruaj në buffer
        buffer = BytesIO()
        img.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)
        
        return Response(
            content=buffer.getvalue(),
            media_type="image/png",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    except Exception as e:
        print(f"[ERROR] Error creating default apple-touch-icon: {e}")
        return JSONResponse({"error": "Icon not found"}, status_code=404)

# --- SETTINGS ---
@app.get("/settings/feature-payment-status")
def get_feature_payment_status(db: Session = Depends(get_db)):
    setting = db.query(models.Setting).filter(models.Setting.setting_key == "feature_payment_status").first()
    enabled = True if not setting else (setting.setting_value == "true")
    return {"enabled": enabled}

@app.get("/manifest.webmanifest")
def get_manifest(db: Session = Depends(get_db)):
    from datetime import datetime
    print(f"[DEBUG] Fetching manifest.webmanifest at {datetime.now()}")
    
    # Përdorim rrugën tonë të rregullt /logo.png që është më e stabilmja për Safari
    # Shtojmë një timestamp të thjeshtë për të shmangur cache probleme
    import time
    timestamp = int(time.time() / 60)  # Ndryshon çdo minutë
    
    return JSONResponse(
        {
            "name": "Holkos Fatura",
            "short_name": "Holkos Fatura",
            "description": "Menaxhimi i faturave dhe ofertave",
            "start_url": "/",
            "scope": "/",
            "display": "standalone",
            "orientation": "portrait",
            "background_color": "#111827",
            "theme_color": "#111827",
            "icons": [
                {
                    "src": f"/logo.png?size=192&v={timestamp}",
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any"
                },
                {
                    "src": f"/logo.png?size=512&v={timestamp}",
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any maskable"
                }
            ],
        },
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Content-Type": "application/manifest+json"
        }
    )

@app.put("/settings/feature-payment-status")
def update_feature_payment_status(payload: dict, db: Session = Depends(get_db)):
    enabled = payload.get("enabled", True)
    value = "true" if enabled else "false"
    setting = db.query(models.Setting).filter(models.Setting.setting_key == "feature_payment_status").first()
    if not setting:
        setting = models.Setting(setting_key="feature_payment_status", setting_value=value)
        db.add(setting)
    else:
        setting.setting_value = value
    db.commit()
    return {"enabled": enabled}

# --- TEMPLATES ---
@app.get("/templates", response_model=List[schemas.Template])
def get_templates(db: Session = Depends(get_db)):
    return db.query(models.Template).order_by(models.Template.is_default.desc(), models.Template.name).all()

@app.put("/templates/{template_id}/default", response_model=schemas.Template)
def set_default_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(models.Template).filter(models.Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    db.query(models.Template).update({models.Template.is_default: False})
    template.is_default = True
    db.commit()
    db.refresh(template)
    return template

@app.put("/templates/{template_id}/toggle-active", response_model=schemas.Template)
def toggle_template_active(template_id: int, db: Session = Depends(get_db)):
    template = db.query(models.Template).filter(models.Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    template.is_active = not template.is_active
    db.commit()
    db.refresh(template)
    return template


# Store for temporary preview data (in production, use Redis or similar)
_preview_cache = {}

def _create_temp_offer(data):
    """Helper function to create temporary offer object"""
    class TempOffer:
        def __init__(self, data):
            self.id = 999999  # Temporary ID
            self.offer_number = data.offer_number
            self.date = data.date
            self.client_id = data.client_id
            self.subject = data.subject or ""
            self.description = data.description or ""
            self.subtotal = data.subtotal
            self.vat_percentage = data.vat_percentage
            self.vat_amount = data.vat_amount
            self.total = data.total
            self.items = []
            for idx, item in enumerate(data.items):
                class TempItem:
                    def __init__(self, item_data, idx):
                        self.description = item_data.description or ""
                        self.unit = item_data.unit or ""
                        self.quantity = item_data.quantity
                        self.unit_price = item_data.unit_price
                        self.subtotal = item_data.subtotal
                        self.row_type = item_data.row_type or 'item'
                        self.custom_attributes = item_data.custom_attributes
                        self.order_index = item_data.order_index if hasattr(item_data, 'order_index') and item_data.order_index is not None else idx
                self.items.append(TempItem(item, idx))
    return TempOffer(data)

@app.post("/offers/preview-store/{preview_id}")
def store_preview_data(preview_id: str, offer: schemas.OfferCreate, db: Session = Depends(get_db)):
    """Ruan të dhënat e preview në cache për mobile devices"""
    # Store in cache (expires after 5 minutes)
    _preview_cache[preview_id] = offer.dict()
    # Clean up old entries (older than 5 minutes)
    import time
    current_time = time.time()
    keys_to_delete = [k for k in _preview_cache.keys() if k.startswith('preview_') and len(k.split('_')) > 1]
    for k in keys_to_delete:
        try:
            timestamp = float(k.split('_')[1]) / 1000
            if current_time - timestamp > 300:  # 5 minutes
                if k in _preview_cache:
                    del _preview_cache[k]
        except:
            pass
    return {"status": "stored", "preview_id": preview_id}

@app.get("/offers/preview-pdf/{preview_id}")
def preview_offer_pdf_get(preview_id: str, font_size: str = Query(None), db: Session = Depends(get_db)):
    """Gjeneron PDF për preview nga cache (për mobile devices)"""
    # Try to get from cache
    offer_data = _preview_cache.get(preview_id)
    
    if not offer_data:
        raise HTTPException(status_code=404, detail="Preview data not found or expired")
    
    # Remove from cache after use
    del _preview_cache[preview_id]
    
    try:
        offer = schemas.OfferCreate(**offer_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid offer data: {str(e)}")
    
    db_company = db.query(models.Company).first()
    db_client = db.query(models.Client).filter(models.Client.id == offer.client_id).first()
    
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    temp_offer = _create_temp_offer(offer)
    
    pdf_path = pdf_generator.generate_offer_pdf(temp_offer, db_company, db_client, manual_font_size=font_size)
    
    return FileResponse(pdf_path, media_type='application/pdf', filename=f"Preview_{temp_offer.offer_number.replace(' ', '_')}.pdf", content_disposition_type='inline')

@app.post("/offers/preview-pdf")
def preview_offer_pdf(offer: schemas.OfferCreate, font_size: str = Query(None), db: Session = Depends(get_db)):
    """Gjeneron PDF për preview pa e ruajtur ofertën në database"""
    
    db_company = db.query(models.Company).first()
    db_client = db.query(models.Client).filter(models.Client.id == offer.client_id).first()
    
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    temp_offer = _create_temp_offer(offer)
    
    pdf_path = pdf_generator.generate_offer_pdf(temp_offer, db_company, db_client, manual_font_size=font_size)
    
    return FileResponse(pdf_path, media_type='application/pdf', filename=f"Preview_{temp_offer.offer_number.replace(' ', '_')}.pdf", content_disposition_type='inline')

@app.get("/offers/{offer_id}/pdf")
def get_offer_pdf(offer_id: int, font_size: str = None, db: Session = Depends(get_db)):
    db_offer = db.query(models.Offer).filter(models.Offer.id == offer_id).first()
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    # Check if PDF already exists
    if db_offer.pdf_path:
        if db_offer.pdf_path.startswith(('http://', 'https://')):
            from fastapi.responses import RedirectResponse
            return RedirectResponse(db_offer.pdf_path)
        elif os.path.exists(db_offer.pdf_path):
            return FileResponse(
                db_offer.pdf_path, 
                media_type='application/pdf', 
                filename=os.path.basename(db_offer.pdf_path), 
                content_disposition_type='inline'
            )

    db_company = db.query(models.Company).first()
    db_client = db.query(models.Client).filter(models.Client.id == db_offer.client_id).first()
    
    pdf_path = pdf_generator.generate_offer_pdf(db_offer, db_company, db_client, manual_font_size=font_size)
    
    # Only save path if it's not a custom font size preview
    if not font_size:
        db_offer.pdf_path = pdf_path
        db.commit()
    
    return FileResponse(pdf_path, media_type='application/pdf', filename=os.path.basename(pdf_path), content_disposition_type='inline')

@app.post("/invoices/{invoice_id}/email")
def email_invoice(invoice_id: int, payload: Optional[schemas.EmailRequest] = Body(None), db: Session = Depends(get_db)):
    db_invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not db_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    db_company = db.query(models.Company).first()
    db_client = db.query(models.Client).filter(models.Client.id == db_invoice.client_id).first()
    
    dest_email = (payload and payload.dest_email) or None
    if not dest_email:
        dest_email = db_client.email if db_client else None
    if not dest_email:
        raise HTTPException(status_code=400, detail="Klienti nuk ka adresë email-i.")
        
    pdf_path = pdf_generator.generate_invoice_pdf(db_invoice, db_company, db_client)
    
    success, message = email_service.send_document(db_invoice, db_company, dest_email, pdf_path, is_offer=False)
    
    if not success:
        raise HTTPException(status_code=500, detail=message)
        
    return {"message": message}

@app.post("/offers/{offer_id}/email")
def email_offer(offer_id: int, payload: Optional[schemas.EmailRequest] = Body(None), db: Session = Depends(get_db)):
    db_offer = db.query(models.Offer).filter(models.Offer.id == offer_id).first()
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    db_company = db.query(models.Company).first()
    db_client = db.query(models.Client).filter(models.Client.id == db_offer.client_id).first()
    
    dest_email = (payload and payload.dest_email) or None
    if not dest_email:
        dest_email = db_client.email if db_client else None
    if not dest_email:
        raise HTTPException(status_code=400, detail="Klienti nuk ka adresë email-i.")
        
    pdf_path = pdf_generator.generate_offer_pdf(db_offer, db_company, db_client, manual_font_size=None)
    
    success, message = email_service.send_document(db_offer, db_company, dest_email, pdf_path, is_offer=True)
    
    if not success:
        raise HTTPException(status_code=500, detail=message)
        
    return {"message": message}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
