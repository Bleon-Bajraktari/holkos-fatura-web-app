"""Durable monthly mail ledger. SMTP ambiguity is never retried automatically."""
import calendar
import json
import re
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Column, String, Text, Integer, DateTime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import declarative_base

ReportBase = declarative_base()


class MonthlyReport(ReportBase):
    __tablename__ = "monthly_mail_reports"
    key = Column(String(32), primary_key=True)
    month = Column(String(7), nullable=False, index=True)
    scope = Column(String(12), nullable=False)
    invoices_state = Column(String(16), default="pending", nullable=False)
    confirmation_state = Column(String(16), default="pending", nullable=False)
    snapshot = Column(Text, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    token = Column(String(36))
    lease_until = Column(DateTime)
    last_error = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class MonthlyReportEvent(ReportBase):
    __tablename__ = "monthly_mail_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_key = Column(String(32), nullable=False, index=True)
    action = Column(String(32), nullable=False)
    detail = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def month_before(value):
    year, month = map(int, value.split("-"))
    return f"{year - (month == 1):04d}-{12 if month == 1 else month - 1:02d}"


def validate_month(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value):
        raise HTTPException(400, "Muaji duhet të jetë YYYY-MM.")
    if not 2000 <= int(value[:4]) <= 2100:
        raise HTTPException(400, "Viti jashtë intervalit.")
    return value


def event(db, row, action, detail=""):
    row.updated_at = datetime.utcnow()
    db.add(MonthlyReportEvent(report_key=row.key, action=action, detail=detail[:2000]))


def serialize(row):
    return {"key": row.key, "month": row.month, "scope": row.scope,
            "invoices_state": row.invoices_state, "confirmation_state": row.confirmation_state,
            "attempts": row.attempts, "last_error": row.last_error,
            "updated_at": row.updated_at.isoformat(), "snapshot": json.loads(row.snapshot)}


def claim_row(db, key):
    row = db.query(MonthlyReport).filter_by(key=key).populate_existing().with_for_update().one()
    now = datetime.utcnow()
    if row.lease_until and row.lease_until > now:
        raise HTTPException(409, "Raporti po përpunohet nga një ekzekutim tjetër.")
    for field in ("invoices_state", "confirmation_state"):
        if getattr(row, field) == "sending":
            setattr(row, field, "uncertain")
            row.last_error = "Ekzekutimi u ndërpre gjatë SMTP; verifikoni dërgimin para riprovimit."
            event(db, row, "uncertain", field)
    if "uncertain" in (row.invoices_state, row.confirmation_state):
        db.commit()
        raise HTTPException(409, "Dërgim i paqartë: kërkohet verifikim në historikun e raportit.")
    if row.invoices_state in ("sent", "empty") and row.confirmation_state == "sent":
        db.commit()
        return {"skipped": True, "reason": "Raporti është dërguar tashmë.", **serialize(row)}
    row.token = str(uuid.uuid4())
    row.lease_until = now + timedelta(minutes=5)
    row.attempts += 1
    event(db, row, "claimed")
    db.commit()
    return {**serialize(row), "token": row.token}


def transition(db, key, payload):
    row = db.query(MonthlyReport).filter_by(key=key).with_for_update().first()
    if not row:
        raise HTTPException(404, "Raporti nuk u gjet.")
    if not row.token or payload.get("token") != row.token or not row.lease_until or row.lease_until <= datetime.utcnow():
        raise HTTPException(409, "Ekzekutimi nuk e zotëron më raportin.")
    action = payload.get("action")
    channel = payload.get("channel")
    if action == "release":
        # A crash/failed checkpoint after SMTP must not turn 'sending' into retryable.
        for field in ("invoices_state", "confirmation_state"):
            if getattr(row, field) == "sending":
                setattr(row, field, "uncertain")
        row.last_error = str(payload.get("error") or "")[:2000] or None
        row.token = None
        row.lease_until = None
    else:
        if channel not in ("invoices", "confirmation"):
            raise HTTPException(400, "Kanal i pavlefshëm.")
        field = channel + "_state"
        current = getattr(row, field)
        if action == "begin" and current in ("pending", "failed"):
            if channel == "confirmation" and row.invoices_state not in ("sent", "empty"):
                raise HTTPException(409, "Faturat nuk janë dërguar ende.")
            setattr(row, field, "sending")
        elif action in ("sent", "failed", "uncertain") and current == "sending":
            setattr(row, field, action)
        else:
            raise HTTPException(409, "Kalimi i statusit nuk lejohet.")
        row.last_error = str(payload.get("error") or "")[:2000] or None
    event(db, row, action, f"{channel or ''}: {row.last_error or ''}")
    db.commit()
    return serialize(row)


def build_router(get_db, models):
    router = APIRouter(prefix="/monthly-reports", tags=["monthly reports"])

    def setting(db, key, default=""):
        row = db.query(models.Setting).filter_by(setting_key=key).first()
        return row.setting_value if row else default

    @router.get("/history")
    def history(db=Depends(get_db)):
        rows = db.query(MonthlyReport).order_by(MonthlyReport.month.desc()).limit(120).all()
        return [serialize(row) for row in rows]

    @router.get("/{key}/events")
    def events(key: str, db=Depends(get_db)):
        rows = db.query(MonthlyReportEvent).filter_by(report_key=key).order_by(MonthlyReportEvent.id.desc()).limit(200).all()
        return [{"action": r.action, "detail": r.detail, "at": r.created_at.isoformat()} for r in rows]

    @router.post("/claim")
    def claim(payload: dict, db=Depends(get_db)):
        current = datetime.now(timezone.utc).strftime("%Y-%m")
        manual = payload.get("manual") is True
        if not manual and setting(db, "monthly_report_enabled", "false") != "true":
            return {"skipped": True, "reason": "Raporti mujor është i çaktivizuar."}
        month = validate_month(payload.get("month") or (current if manual else month_before(current)))
        if month > current or (not manual and month >= current):
            raise HTTPException(400, "Muaji nuk është mbyllur ende.")
        scope = "test" if manual and month == current else "monthly"
        if not manual:
            # Persist the first covered month, so missed months survive month/year rollover.
            start = setting(db, "monthly_report_start_month")
            if not start:
                try:
                    db.add(models.Setting(setting_key="monthly_report_start_month", setting_value=month))
                    db.commit()
                except IntegrityError:
                    db.rollback()
                start = setting(db, "monthly_report_start_month")
            candidate = validate_month(start)
            while candidate < current:
                existing = db.query(MonthlyReport).filter_by(key=f"monthly:{candidate}").first()
                if not existing or existing.invoices_state not in ("sent", "empty") or existing.confirmation_state != "sent":
                    break
                year, number = map(int, candidate.split("-"))
                candidate = f"{year + (number == 12):04d}-{1 if number == 12 else number + 1:02d}"
            if candidate >= current:
                return {"skipped": True, "reason": "Të gjithë muajt janë dërguar."}
            month = candidate
        key = f"{scope}:{month}"
        row = db.query(MonthlyReport).filter_by(key=key).first()
        if not row:
            year, number = map(int, month.split("-"))
            from datetime import date
            invoices = db.query(models.Invoice).filter(
                models.Invoice.date >= date(year, number, 1),
                models.Invoice.date <= date(year, number, calendar.monthrange(year, number)[1])
            ).order_by(models.Invoice.id).all()
            invoices_email = (payload.get("invoices_email") if manual else None) or setting(db, "monthly_report_invoices_email")
            status_email = (payload.get("status_email") if manual else None) or setting(db, "monthly_report_status_email")
            if not invoices_email or not status_email:
                raise HTTPException(400, "Mungojnë adresat e raportit mujor.")
            snapshot = {"invoices_email": invoices_email, "status_email": status_email,
                        "invoices": [{"id": i.id, "invoice_number": i.invoice_number,
                                      "date": str(i.date), "total": float(i.total or 0)} for i in invoices]}
            try:
                db.add(MonthlyReport(key=key, month=month, scope=scope, snapshot=json.dumps(snapshot),
                                     invoices_state="pending" if invoices else "empty"))
                db.commit()
            except IntegrityError:
                db.rollback()  # Another invocation created the unique monthly row.
        return claim_row(db, key)

    @router.post("/{key}/transition")
    def update(key: str, payload: dict, db=Depends(get_db)):
        return transition(db, key, payload)

    @router.post("/{key}/resolve")
    def resolve(key: str, payload: dict, db=Depends(get_db)):
        """Explicit authenticated operator decision after checking the SMTP provider."""
        row = db.query(MonthlyReport).filter_by(key=key).with_for_update().first()
        if not row:
            raise HTTPException(404, "Raporti nuk u gjet.")
        if row.lease_until and row.lease_until > datetime.utcnow():
            raise HTTPException(409, "Raporti është në përpunim.")
        channel = payload.get("channel")
        if channel not in ("invoices", "confirmation") or type(payload.get("delivered")) is not bool or not payload.get("note"):
            raise HTTPException(400, "Kërkohen channel, delivered dhe note pas verifikimit.")
        field = channel + "_state"
        if getattr(row, field) not in ("uncertain", "sending"):
            raise HTTPException(409, "Vetëm dërgimet e paqarta mund të zgjidhen.")
        setattr(row, field, "sent" if payload["delivered"] else "failed")
        row.token = None
        row.lease_until = None
        event(db, row, "resolved", f"{channel}: delivered={payload['delivered']}; {payload['note']}")
        db.commit()
        return serialize(row)

    return router
