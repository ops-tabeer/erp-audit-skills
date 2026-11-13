# Odoo 17-19 hardening checklist (names confirmed in Odoo 19 source)

Ordered by risk-reduction per hour of effort. Each item gives where to set it, and how the
`odoo_controls_check.py` check (K-code) verifies it. Server-side items are written as commands **for the
user to run**: do not connect to servers yourself unless the user's own rules allow it.

## A. Accounting integrity (K01, K02)

1. **Restrictive Audit Trail**: Accounting → Settings → Reporting → *Restrictive Audit Trail*
   (`res.company.restrictive_audit_trail`). Blocks deleting posted entries and keeps their logs.
2. **Lock dates monthly**: set *Lock Everything* (`fiscalyear_lock_date`) within about 15 days of month
   end; sales/purchase locks as needed; **hard lock** (`hard_lock_date`, irreversible) after the annual
   audit. Exceptions are granted per user and time-boxed through `account.lock_exception` (logged).
3. **Hash-secured journals**: Journal → Advanced → *Secure Posted Entries with Hash*
   (`account.journal.restrict_mode_hash_table`) on sales and purchase journals. Run the data
   inalterability report quarterly.
4. **Bank reconciliation**: import bank, POS-acquirer and BNPL statements (Tabby/Tamara/PayPal…) and
   reconcile weekly. One clearing account per gateway, which must net to zero after settlement.
   Reviewer ≠ cashier.
5. **Trusted bank accounts**: only the *Validate bank account* group can set
   `res.partner.bank.allow_out_payment`; payments to untrusted accounts are blocked. That group must not
   also pay suppliers.

## B. Identity and access (K03-K06)

1. **2FA for everyone internal**: install `auth_totp_mail`, then Settings → Permissions → *Enforce
   two-factor authentication*, policy *Employees only* (`auth_totp.policy = employee_required`) or
   *All users*. Better still, roll out **passkeys** (`auth_passkey`, community, LGPL) for administrators
   and finance.
2. **Password policy** (`auth_password_policy`): `auth_password_policy.minlength` ≥ 12 (15 for any
   account without 2FA). No forced periodic changes. Keep login throttling (`base.login_cooldown_after`,
   `base.login_cooldown_duration`).
3. **Few administrators**: 1-2 named people in *Settings* (`base.group_system`) and *Access Rights*
   (`base.group_erp_manager`), with a separate admin login that never processes transactions.
   Accountants get *Accountant*, not *Administrator* (`account.group_account_manager`).
4. **Named accounts only**: retire shared logins (cashier@, info@, ops@). Shared logins make the change
   log useless as evidence.
5. **Joiner/mover/leaver**: archive users on their last day (tie into offboarding); review groups
   quarterly; review API keys (`res_users_apikeys`) and use a dedicated integration user.
6. **Export rights**: limit *Access to export feature* (`base.group_allow_export`).

## C. Server and deployment (K08, plus manual checks)

Config (`odoo.conf`), to give to the user to apply:

```ini
[options]
admin_passwd = <set via the UI database manager so it is stored as $pbkdf2-sha512$...; never plain text>
list_db = False
dbfilter = ^<exact-db-name>$
proxy_mode = True            ; behind nginx/HTTPS only
workers = <2*CPU+1>          ; never 0 in production
max_cron_threads = 1-2
limit_time_cpu = 600
limit_time_real = 1200
limit_memory_soft = 2147483648
limit_memory_hard = 2684354560
logfile = /var/log/odoo/odoo.log   ; shipped off-box and kept ≥ 1 year
log_level = info
```

- Reverse proxy: TLS 1.2+ (1.3 preferred), HSTS, block `/web/database/*` externally, set
  `X-Forwarded-*` correctly, rate-limit `/web/login`.
- PostgreSQL: listen only on localhost/private network; the Odoo DB role is not a superuser; `pg_hba.conf`
  uses scram-sha-256.
- Patching: track Odoo stable branch updates monthly and OS security updates weekly; pin and review
  third-party modules (supply-chain risk, OWASP A03:2025).
- Secrets: no secrets in git; config file `chmod 640` owned by the odoo user.

## C2. Custom code and integrations (K09, K10)

- Every `@http.route(auth='public'|'none')` needs a reason. Protect it with an HMAC signature or a shared
  token compared with `hmac.compare_digest`, an nginx IP allow-list (devices such as ZKTeco biometric
  clocks often can't send tokens), and rate limits. `csrf=False` is acceptable only for machine-to-machine
  routes that have such protection.
- Never `sudo()` on records or values the caller controls. Never auto-create master data (devices,
  partners, users) from unauthenticated input. Remove `/test` and debug routes before production.
- Logging: record method, path, remote IP and a request id. Mask `Authorization`, `X-API-Key`, `api_key`,
  tokens, passport numbers and phone numbers. Never log raw bodies of lead or payment webhooks.
- Integration API keys: one per integration, with an expiry, stored in the integration's settings, and
  rotated after any log exposure.
- PostgreSQL role: Odoo must not run as a superuser (`ALTER ROLE <role> NOSUPERUSER NOCREATEROLE`). The
  role should own only its own databases. Test on a copy first.
- Server actions and automated actions with Python code run with elevated rights. Review the custom ones
  like code.

## D. Backups and recovery (book ch. 10, updated)

- **3-2-1-1-0**: 3 copies, 2 media, 1 off-site, 1 immutable/offline, 0 errors on restore test.
- Back up **both** the database (pg_dump or base backup + WAL archiving for point-in-time recovery) **and**
  the filestore. A database without its filestore loses every attachment, which means losing the evidence.
- Encrypt off-site copies; keep retention ≥ the legal record-retention period for year-end snapshots.
- Restore drill each quarter into an isolated host, with the measured RTO/RPO recorded.
- Backup scripts must not prune anything except their own expired archives.

## E. Data protection (K07)

- No public attachments containing IDs or passports; review `ir_attachment.public = True` monthly.
- Portal links (`access_token`) on invoices are shareable bearer links: rotate on request and don't
  email them to third parties.
- Outgoing mail servers must use STARTTLS or SSL (`ir_mail_server.smtp_encryption`).
- Neutralise copies before using them for dev/test (`odoo-bin neutralize`), and mask passports, phones and
  emails in non-production copies.

## F. Monitoring

- Run `odoo_forensic_scan.py` monthly (and after any incident), and review the per-user roll-up.
- Alert on: new admin group membership, lock-date changes, `restrictive_audit_trail` turned off, bank
  account trust changes, mass exports, logins from new countries.
