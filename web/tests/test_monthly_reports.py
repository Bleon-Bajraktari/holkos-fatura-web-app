import sys
import json
import unittest
from pathlib import Path
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, Integer, Date, Numeric
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from types import SimpleNamespace
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from monthly_reports import ReportBase, MonthlyReport, MonthlyReportEvent, claim_row, transition, month_before, build_router

FixtureBase = declarative_base()

class Setting(FixtureBase):
    __tablename__ = 'settings'
    setting_key = Column(String, primary_key=True)
    setting_value = Column(String)

class Invoice(FixtureBase):
    __tablename__ = 'invoices'
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    invoice_number = Column(String)
    total = Column(Numeric)


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        ReportBase.metadata.create_all(self.engine)
        FixtureBase.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)
        def get_db():
            with self.session() as db:
                yield db
        app = FastAPI()
        app.include_router(build_router(get_db, SimpleNamespace(Setting=Setting, Invoice=Invoice)))
        self.client = TestClient(app)
        with self.session() as db:
            for key, value in [('monthly_report_enabled', 'true'), ('monthly_report_invoices_email', 'a@example.test'), ('monthly_report_status_email', 'b@example.test')]:
                db.add(Setting(setting_key=key, setting_value=value))
            db.commit()

    def tearDown(self):
        self.client.close()
        self.engine.dispose()

    def test_disabled_reporting_does_not_create_report(self):
        with self.session() as db:
            db.get(Setting, 'monthly_report_enabled').setting_value = 'false'
            db.commit()
        self.assertTrue(self.client.post('/monthly-reports/claim', json={}).json()['skipped'])
        self.assertEqual(self.client.get('/monthly-reports/history').json(), [])

    def test_daily_check_catches_up_oldest_month(self):
        previous = month_before(datetime.now().strftime('%Y-%m'))
        oldest = month_before(previous)
        with self.session() as db:
            db.add(Setting(setting_key='monthly_report_start_month', setting_value=oldest))
            db.commit()
        report = self.client.post('/monthly-reports/claim', json={}).json()
        self.assertEqual(report['month'], oldest)
        self.assertEqual(report['invoices_state'], 'empty')
        for action in ['begin', 'sent', 'release']:
            response = self.client.post(f"/monthly-reports/{report['key']}/transition", json={'token': report['token'], 'action': action, 'channel': 'confirmation'})
            self.assertEqual(response.status_code, 200)
        next_report = self.client.post('/monthly-reports/claim', json={}).json()
        self.assertEqual(next_report['month'], previous)

    def test_manual_current_month_does_not_suppress_automatic_report(self):
        manual = self.client.post('/monthly-reports/claim', json={'manual': True}).json()
        automatic = self.client.post('/monthly-reports/claim', json={}).json()
        self.assertEqual(manual['scope'], 'test')
        self.assertEqual(automatic['scope'], 'monthly')
        self.assertNotEqual(manual['key'], automatic['key'])

    def test_invalid_month_is_rejected(self):
        self.assertEqual(self.client.post('/monthly-reports/claim', json={'manual': True, 'month': '2026-13'}).status_code, 400)

    def test_operator_resolution_requires_evidence_and_expired_lease(self):
        report = self.client.post('/monthly-reports/claim', json={}).json()
        with self.session() as db:
            row = db.get(MonthlyReport, report['key'])
            row.confirmation_state = 'uncertain'
            row.lease_until = datetime.utcnow() - timedelta(seconds=1)
            db.commit()
        path = f"/monthly-reports/{report['key']}/resolve"
        self.assertEqual(self.client.post(path, json={'channel': 'confirmation', 'delivered': True}).status_code, 400)
        resolved = self.client.post(path, json={'channel': 'confirmation', 'delivered': True, 'note': 'Provider receipt verified'})
        self.assertEqual(resolved.status_code, 200)
        self.assertEqual(resolved.json()['confirmation_state'], 'sent')


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://')
        ReportBase.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.db.add(MonthlyReport(key='monthly:2026-09', month='2026-09', scope='monthly', snapshot=json.dumps({'invoices': []})))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def step(self, report, action, channel=None):
        return transition(self.db, report['key'], {'token': report['token'], 'action': action, 'channel': channel})

    def test_second_invocation_cannot_claim_active_report(self):
        claim_row(self.db, 'monthly:2026-09')
        with self.assertRaises(HTTPException) as error:
            claim_row(self.db, 'monthly:2026-09')
        self.assertEqual(error.exception.status_code, 409)

    def test_confirmation_retry_preserves_invoice_success(self):
        report = claim_row(self.db, 'monthly:2026-09')
        self.step(report, 'begin', 'invoices')
        self.step(report, 'sent', 'invoices')
        self.step(report, 'begin', 'confirmation')
        self.step(report, 'failed', 'confirmation')
        self.step(report, 'release')
        retry = claim_row(self.db, 'monthly:2026-09')
        self.assertEqual(retry['invoices_state'], 'sent')
        self.assertEqual(retry['confirmation_state'], 'failed')
        self.assertEqual(retry['attempts'], 2)
        with self.assertRaises(HTTPException):
            self.step(retry, 'begin', 'invoices')

    def test_crash_during_smtp_requires_review(self):
        report = claim_row(self.db, 'monthly:2026-09')
        self.step(report, 'begin', 'invoices')
        row = self.db.get(MonthlyReport, report['key'])
        row.lease_until = datetime.utcnow() - timedelta(seconds=1)
        self.db.commit()
        with self.assertRaises(HTTPException):
            claim_row(self.db, report['key'])
        self.assertEqual(row.invoices_state, 'uncertain')

    def test_release_after_checkpoint_failure_preserves_uncertainty(self):
        report = claim_row(self.db, 'monthly:2026-09')
        self.step(report, 'begin', 'invoices')
        self.step(report, 'release')
        self.assertEqual(self.db.get(MonthlyReport, report['key']).invoices_state, 'uncertain')

    def test_completed_report_is_skipped(self):
        report = claim_row(self.db, 'monthly:2026-09')
        for channel in ('invoices', 'confirmation'):
            self.step(report, 'begin', channel)
            self.step(report, 'sent', channel)
        self.step(report, 'release')
        self.assertTrue(claim_row(self.db, report['key'])['skipped'])
        self.assertGreater(self.db.query(MonthlyReportEvent).count(), 0)

    def test_stale_worker_cannot_checkpoint(self):
        report = claim_row(self.db, 'monthly:2026-09')
        with self.assertRaises(HTTPException):
            transition(self.db, report['key'], {'token': 'wrong', 'action': 'release'})

    def test_year_boundary(self):
        self.assertEqual(month_before('2026-01'), '2025-12')


if __name__ == '__main__':
    unittest.main()
