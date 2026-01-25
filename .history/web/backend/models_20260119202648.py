from sqlalchemy import Column, Integer, String, Text, DECIMAL, DateTime, Date, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    address = Column(Text)
    phone = Column(String(50))
    email = Column(String(255))
    unique_number = Column(String(50))
    fiscal_number = Column(String(50))
    account_nib = Column(String(50))
    logo_path = Column(String(500))
    smtp_server = Column(String(255), default='smtp.gmail.com')
    smtp_port = Column(Integer, default=587)
    smtp_user = Column(String(255))
    smtp_password = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    address = Column(Text)
    unique_number = Column(String(50))
    phone = Column(String(50))
    email = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Template(Base):
    __tablename__ = "templates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    template_file = Column(String(500))
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    payment_due_date = Column(Date)
    client_id = Column(Integer, ForeignKey("clients.id"))
    template_id = Column(Integer, ForeignKey("templates.id"))
    subtotal = Column(DECIMAL(10, 2), default=0.00)
    vat_percentage = Column(DECIMAL(5, 2), default=18.00)
    vat_amount = Column(DECIMAL(10, 2), default=0.00)
    total = Column(DECIMAL(10, 2), default=0.00)
    status = Column(Enum('draft', 'sent', 'paid'), default='draft')
    pdf_path = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    client = relationship("Client")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")

class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    description = Column(Text, nullable=False)
    quantity = Column(DECIMAL(10, 2), nullable=False)
    unit_price = Column(DECIMAL(10, 2), nullable=False)
    unit = Column(String(20))
    subtotal = Column(DECIMAL(10, 2), nullable=False)
    order_index = Column(Integer, default=0)

    invoice = relationship("Invoice", back_populates="items")

class Offer(Base):
    __tablename__ = "offers"
    id = Column(Integer, primary_key=True, index=True)
    offer_number = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"))
    subject = Column(String(255))
    description = Column(Text)
    subtotal = Column(DECIMAL(10, 2), default=0.00)
    vat_percentage = Column(DECIMAL(5, 2), default=18.00)
    vat_amount = Column(DECIMAL(10, 2), default=0.00)
    total = Column(DECIMAL(10, 2), default=0.00)
    pdf_path = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    client = relationship("Client")
    items = relationship("OfferItem", back_populates="offer", cascade="all, delete-orphan")

class OfferItem(Base):
    __tablename__ = "offer_items"
    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(Integer, ForeignKey("offers.id"))
    description = Column(Text)
    unit = Column(String(20))
    quantity = Column(DECIMAL(10, 2), default=0.00)
    unit_price = Column(DECIMAL(10, 2), default=0.00)
    subtotal = Column(DECIMAL(10, 2), default=0.00)
    row_type = Column(String(20), default='item')
    custom_attributes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    offer = relationship("Offer", back_populates="items")

class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_value = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
