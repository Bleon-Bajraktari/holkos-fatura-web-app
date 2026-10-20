# Monthly report recovery

## Activation order

1. Deploy the backend first. Startup creates only the additive `monthly_mail_reports` and `monthly_mail_events` tables using the existing database connection. All new routes use the existing authentication middleware. Verify `/monthly-reports/history` while signed in.
2. In Vercel Production configure existing `CRON_SECRET`, `BACKEND_USERNAME`, `BACKEND_PASSWORD`, and optionally `BACKEND_URL`.
3. Configure independent alert credentials in Vercel Production: `REPORT_ALERT_TO` (comma-separated recipients), `REPORT_ALERT_SMTP_HOST`, `REPORT_ALERT_SMTP_PORT` (default 587), `REPORT_ALERT_SMTP_USER`, `REPORT_ALERT_SMTP_PASSWORD`. These must exist independently of Render. Use a dedicated sender if possible. Never place values in source control. Cron fails closed if required alert configuration is absent.
4. Verify that monthly reporting is enabled and both report recipient addresses and SMTP settings are saved in the app.
5. Deploy the frontend/functions. The schedule is now daily at 10:00 UTC. A completed month is skipped. No production deployment, database migration, environment update, or real email was performed during local implementation.
6. Verify a controlled delivery and history after deployment. The current-month manual button is a separately tracked test, sent once per month; it does not suppress the closed-month automatic report.

## Recovery and history

The first successful automatic claim records the previous month as `monthly_report_start_month` in the settings table. Subsequent daily checks select the oldest incomplete month from that starting month, including across year boundaries. Earlier historical months are not automatically mailed. To cover an earlier month, explicitly configure the starting month before activation after checking what was already sent. An ambiguous oldest report blocks later months until reviewed.

The snapshot freezes invoice IDs, dates, amounts and recipients at the first attempt. PDFs are fetched from the existing invoice PDF endpoint; invoice PDF contents are not permanently archived by this feature. Do not edit/delete those invoices during recovery. If any PDF fails or is not PDF data, no invoice email is sent. Attachments over 18 MiB require operator intervention/splitting; they are not silently omitted.

Settings now shows per-channel status, attempts and errors. Use “Shiko përpjekjet” for events. A database lease prevents concurrent sends. A known SMTP rejection is retried on the next daily run. If invoices succeeded but confirmation failed, only confirmation is retried.

SMTP cannot guarantee exactly-once delivery: acceptance by the mail server and committing the database are separate operations. A disconnect/timeout, partial recipient acceptance, or a crash during sending is marked `uncertain`. After a crashed invocation the lease expires after five minutes. Check the provider's sent/delivery logs, then use the history's explicit resolution buttons. Do not mark a partial delivery “not sent” without considering recipients who already received it. Marking “not sent” authorizes another delivery to all snapshot recipients. `sent` means SMTP accepted, not proof of inbox delivery.

All failures return non-2xx. Independent alerts are attempted even when backend login fails, without downloading credentials from the backend. If the alert provider is itself down, the function logs that failure; no single SMTP provider can guarantee notifications. Calls failing before reaching the database are available in Vercel logs and the independent alert, not in the database ledger. Invalid cron authentication returns 401 without sending an alert. Configure external failed-job monitoring for platform failures that prevent the function from running at all.

Processing has a 42-second work budget within the existing 60-second function configuration, with bounded HTTP/SMTP calls and time reserved for failure notification. Large batches that consistently exceed this budget need a durable worker/queue; repeatedly increasing the HTTP timeout is not a substitute. Backend sleep is still a separate hosting decision.

## Read-only investigation endpoints

- `GET /monthly-reports/history`
- `GET /monthly-reports/{key}/events`

## Authenticated manual resolution

`POST /monthly-reports/{key}/resolve`, body: `{ "channel": "invoices" | "confirmation", "delivered": true | false, "note": "Evidence checked by operator" }`.

## Local regression tests

Install test dependencies with `python -m pip install -r tests/requirements.txt`. From `web`: `python -m unittest discover -s tests -p "test_*.py"` and `node --test tests/monthly-report.test.mjs`.
Tests use SQLite/mock HTTP and SMTP, never the production database or real recipients. SQLite verifies state transitions; MySQL row locking must also be verified in the deployment environment before unattended operation.
