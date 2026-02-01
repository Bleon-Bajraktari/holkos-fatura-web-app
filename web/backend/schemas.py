from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any
from datetime import date, datetime
from decimal import Decimal

# Company Schemas
class CompanyBase(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    unique_number: Optional[str] = None
    fiscal_number: Optional[str] = None
    account_nib: Optional[str] = None
    logo_path: Optional[str] = None
    smtp_server: Optional[str] = 'smtp.gmail.com'
    smtp_port: Optional[int] = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(CompanyBase):
    pass

class Company(CompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Client Schemas
class ClientBase(BaseModel):
    name: str
    address: Optional[str] = None
    unique_number: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class ClientCreate(ClientBase):
    pass

class Client(ClientBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Invoice Item Schemas
class InvoiceItemBase(BaseModel):
    description: str
    quantity: Decimal
    unit: Optional[str] = None
    unit_price: Decimal
    subtotal: Decimal
    order_index: Optional[int] = 0

class InvoiceItemCreate(InvoiceItemBase):
    pass

class InvoiceItem(InvoiceItemBase):
    id: int
    invoice_id: int

    class Config:
        orm_mode = True

# Invoice Schemas
class InvoiceBase(BaseModel):
    invoice_number: str
    date: date
    payment_due_date: Optional[date] = None
    client_id: int  # Pranon edhe string qe konvertohet ne int
    template_id: Optional[int] = None
    client_name: Optional[str] = None  # Per UI - nuk ruhet ne DB
    subtotal: Decimal = 0.00
    vat_percentage: Decimal = 18.00
    vat_amount: Decimal = 0.00
    total: Decimal = 0.00
    status: str = 'draft'
    save_timestamp: Optional[datetime] = None

class InvoiceCreate(InvoiceBase):
    items: List[InvoiceItemCreate]

class Invoice(InvoiceBase):
    id: int
    created_at: datetime
    updated_at: datetime
    items: List[InvoiceItem] = []
    client: Optional[Client] = None

    class Config:
        orm_mode = True

# Offer Item Schemas
class OfferItemBase(BaseModel):
    description: Optional[str] = None
    unit: Optional[str] = None
    quantity: Decimal = 0.00
    unit_price: Decimal = 0.00
    subtotal: Decimal = 0.00
    row_type: Optional[str] = 'item'
    custom_attributes: Optional[Any] = None
    order_index: Optional[int] = 0

class OfferItemCreate(OfferItemBase):
    pass

class OfferItem(OfferItemBase):
    id: int
    offer_id: int

    class Config:
        orm_mode = True

# Offer Schemas
class OfferBase(BaseModel):
    offer_number: str
    date: date
    client_id: int
    subject: Optional[str] = None
    description: Optional[str] = None
    subtotal: Decimal = 0.00
    vat_percentage: Decimal = 18.00
    vat_amount: Decimal = 0.00
    total: Decimal = 0.00
    save_timestamp: Optional[datetime] = None

class OfferCreate(OfferBase):
    items: List[OfferItemCreate]

class Offer(OfferBase):
    id: int
    created_at: datetime
    updated_at: datetime
    items: List[OfferItem] = []
    client: Optional[Client] = None

    class Config:
        orm_mode = True

# Settings Schemas
class SettingBase(BaseModel):
    setting_key: str
    setting_value: Optional[str] = None

class Setting(SettingBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Template Schemas
class TemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    template_file: Optional[str] = None
    is_active: bool = True
    is_default: bool = False

class Template(TemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Bulk Operations
class BulkEmailRequest(BaseModel):
    invoice_ids: List[int]
    override_email: Optional[EmailStr] = None

class BulkDeleteRequest(BaseModel):
    invoice_ids: List[int]

class BulkDeleteOfferRequest(BaseModel):
    offer_ids: List[int]

class BulkEmailOfferRequest(BaseModel):
    offer_ids: List[int]
    override_email: Optional[EmailStr] = None

class StatusUpdate(BaseModel):
    status: str

class EmailRequest(BaseModel):
    dest_email: Optional[EmailStr] = None
