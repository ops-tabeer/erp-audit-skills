---
name: erp-security-hardening
description: Assess and harden the security and IT general controls of Odoo (17-19) and other ERPs. It covers 2FA/passkeys and password policy (NIST 800-63B-4), admin and privileged access, segregation of duties from real user activity, dormant and shared logins, API keys, audit trail and lock-date settings, bank-reconciliation evidence, public attachments and data exposure, unsafe public routes/webhooks and secrets in logs in custom addons, odoo.conf/server/proxy/PostgreSQL role settings, backups (3-2-1-1-0, filestore), patching and monitoring. Use it whenever the user asks to secure, harden, pen-test-review or "make compliant" an ERP, check who has admin rights, prepare for an ISO 27001/SOC 2/PCI review, run a security health check, or after an incident or fraud to close the gaps, even if they just say "is our Odoo safe?".
---

# ERP security hardening

Measure first, then fix in order of risk. The book's security chapters (2014) are updated here to 2026
practice: phishing-resistant MFA, no forced password rotation, zero trust, immutable backups, supply-chain
risk. All of it is mapped to Odoo settings that were checked against the Odoo 19 source.

## Workflow

1. **Measure.** Run the read-only baseline against a database copy (or production with a read-only role):
   `python scripts/odoo_controls_check.py --db <db> --out <dir> [--conf path/to/odoo.conf] [--addons path/to/custom_addons] [--days 180]`
   Use the Odoo venv's python. It writes `CONTROLS_REPORT.md` and one CSV per check:
   - K01 audit trail, lock dates, hash journals
   - K02 bank-reconciliation evidence
   - K03 2FA, passkeys, password length, auth modules installed
   - K04 privileged users
   - K05 segregation of duties from actual activity
   - K06 dormant, shared and API accounts
   - K07 public attachments, portal tokens, mail TLS
   - K08 server config, with secret values never printed
   - K09 custom-code routes: public or no-auth routes, `csrf=False`, `sudo()` in public routes, request data written to logs
   - K10 PostgreSQL role privileges

   Then **read the code behind every K09 row**. The scan is pattern-based, so confirm each finding before
   reporting it. Look for:
   - routes that auto-create records from unauthenticated input
   - test or debug routes
   - secrets or personal data written to logs
   - webhooks that don't verify a signature

   Accounting controls (K01-K06) and code and infrastructure exposure (K08-K10) are both needed. A review
   that covers only one side misses half the risk.

   If the config file lives on a server, don't connect to fetch it: ask the user to copy it, or give
   them the command to run.
2. **Prioritise.** Order fixes by (likelihood × impact) ÷ effort. In practice that usually means:
   1. admin sprawl
   2. 2FA for admins and finance
   3. shared logins
   4. restrictive audit trail and lock dates
   5. bank reconciliation
   6. server configuration
   7. backups and restore test
   8. monitoring
3. **Fix with exact steps.** Use `references/odoo-hardening.md` for the menu path, field or parameter
   name, and config line. Separate UI changes (the user does them) from server changes (give commands
   for the user to run) and code changes (a module PR, see the `erp-controls-compliance` guardrails).
   Don't change production yourself.
4. **Verify.** Re-run the check and show the before/after per K-code.
5. **Other ERPs.** Apply the same control intent with that system's native feature (SAP: SU01/PFCG roles,
   SM20 audit log, RSPARAM password parameters, GRC; Oracle Fusion: security console roles, SSO + MFA;
   Dynamics 365: Entra ID conditional access, SoD rules, database log; NetSuite: 2FA roles, login audit
   trail, saved-search SoD). Say clearly what needs confirming in the client's system.

## Principles worth explaining to the user

- **Identity is the perimeter.** Most ERP breaches and frauds use a valid login, so MFA and named
  accounts matter more than firewalls.
- **Least privilege beats trust.** An accountant with *Administrator* can switch off the controls that
  would catch them.
- **Evidence must survive the people who could alter it.** Audit trail on, no deletes, logs and backups
  off the box.
- **Backups aren't backups until restored**, and an Odoo backup without the filestore loses every attachment.
- Password rotation and complexity rules are outdated (NIST SP 800-63B-4). Recommend length, a breached-password
  screen and MFA instead. `erp-controls-compliance/references/standards-current.md` has the confirmed versions.

## References

- `references/odoo-hardening.md`: the checklist with Odoo names, a config template, backups and monitoring.
- `references/security-baseline.md`: the book's security concepts rated still valid / update / obsolete,
  availability and backup practice, and a 15-item deployment checklist.
