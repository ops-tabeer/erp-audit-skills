# Guardrails for building or reviewing custom Odoo modules that touch money or personal data

Use these when writing a custom addon, reviewing a PR, or designing a workflow (refunds, payment
approval, payroll, cash tills, gateways). Each rule says why it matters, usually with the failure it
prevents. Odoo names are checked against the Odoo 19 source. For syntax, load the Odoo 19 development
skill.

## 1. Approvals must be enforced on the server and separate the people involved

- Enforce approval checks in Python (`write`/action methods with `@api.constrains`, or explicit checks in
  `action_*`), never only with `invisible`/`readonly` in the view. The UI can be bypassed with JSON-RPC,
  import or `sudo` code.
- Store **who** did each stage (`*_user_id`) and **when**, and block the same user from performing two
  incompatible stages: requester ≠ approver ≠ payer. Typical failure: a cashier with accounting-admin rights
  approved his own cash refunds.
- When a team is too small to separate duties, add a compensating control: a mandatory second approver
  above a threshold, plus a daily exception report reviewed by someone outside cash handling.
- Treat `sudo()` as a security decision. Every `sudo()` in a write path needs a comment saying why, and a
  check that the calling user is allowed to trigger it.

## 2. Money must leave through the right channel, for the right amount

- Refunds should default to, and be validated against, the **original payment channel** (Tabby refund
  through Tabby, bank receipt refunded to bank). Paying cash when the customer asked for bank should need
  a reason plus a second approval. Typical failure: cash refunds booked against BNPL and bank requests.
- Cap the payment at the approved payable, and block a second payment of the same request
  (`sum(payments) ≤ payable`).
- Never let the cashier choose a journal or amount freely when an upstream document already states them
  (payment proof, refund request). Pre-fill from the source, lock the field, and require a reason to
  change it. Typical failure: the proof said cash, the cashier booked it to bank, and nothing compared the two.
- Vendor and customer bank accounts must be **trusted** (`res.partner.bank.allow_out_payment`) before any
  outbound payment. The person who changes bank details must not be the person who pays.

## 3. Never delete. Reverse, cancel or archive, and keep evidence

- Turn on `res.company.restrictive_audit_trail`. With it, posted entries and their logs can't be
  removed. Don't write `unlink()` overrides or scripts that delete accounting records. A correction is a
  reversal or credit note with a reason.
- Keep sequences gap-free and posted entries tamper-evident: set `account.journal.restrict_mode_hash_table`
  on sales and purchase journals, and keep `inalterable_hash` intact.
- Require an attachment (receipt, slip, customer request) before posting cash-outs, refunds and manual
  journals that touch cash or refund liabilities. Store attachments on the record.
- Track (`tracking=True`) every field that changes money or ownership: amount, journal, partner, bank
  account, date, state, approver. Odoo 19 logs move-line `balance` and `account_id` changes on the entry's
  chatter (visible in `mail_tracking_value` against `account.move.line` fields), but custom models only log
  what you mark `tracking=True`, and logs can be deleted unless the restrictive audit trail is on.

## 4. Periods close and stay closed

- Lock dates: `fiscalyear_lock_date` (everyone), `sale_lock_date`/`purchase_lock_date`, and the
  irreversible `hard_lock_date` once the year is audited. Exceptions go through `account.lock_exception`
  with a reason and expiry. Code must not bypass lock dates with context flags.
- Don't back-date: the gap between `create_date` and the accounting `date` on cash and bank entries
  should be small, and monitored. Make "date more than N days in the past" need a reason.

## 5. Manual journal entries are the riskiest feature

- Restrict who can post manual entries to cash/till accounts and to refund/deposit/payable accounts. A
  manual entry that credits cash against a liability with no partner is the fabricated-refund pattern.
- Require a partner on lines that hit receivable, payable, refund-payable and security-deposit accounts.
  Without a partner, a liability can't be traced to a customer.
- Never hard-code account codes. Identify accounts by `account_type`, journal default accounts, or a
  per-company setting (see the no-hard-coded-account-codes rule).

## 6. Personal data (passports, IDs, visas)

- Put identity-document fields behind a dedicated group (`groups=` on the field), keep them out of
  chatter tracking, and never attach scans as public (`ir_attachment.public = False`).
- Limit export (`base.group_allow_export`) for staff who don't need bulk data.
- Retention: anonymise rather than delete once the legal retention ends (accounting records: keep at
  least 7 years). Run jobs as a dry run first, and log what changed.

## 7. Integrations and automation

- Use a dedicated integration user with minimal groups and its own API key. Never run integrations as an
  admin or a real person's login.
- Payment-gateway webhooks: verify signatures, deduplicate by provider transaction id, and reconcile
  settlements to one clearing account per provider that nets to zero.
- Scheduled actions and server actions are code. Review them like code, and never let them run as
  `base.user_root` on financial models without a reason.

## 8. Tests that should exist for any money-moving module

- The same user can't approve and pay (expects `UserError`/`AccessError`).
- Paying more than the payable, or paying twice, is blocked.
- The refund channel is forced to match the receipt channel unless an override reason and second approver exist.
- Posted records can't be deleted, and edits after posting are blocked or logged.
- Lock dates are respected (posting before the lock date fails).
- A user without the group can't read or export passport fields.

## PR review checklist (copy into the review)

- [ ] Server-side permission and approval checks; no UI-only security
- [ ] No `unlink` of financial records; corrections by reversal
- [ ] Separation of duties enforced (stage users stored and compared)
- [ ] Amounts and journals sourced from upstream documents, overrides need a reason
- [ ] Tracking on money and ownership fields; evidence attachments required
- [ ] No hard-coded account codes or company ids
- [ ] Lock dates and hash chain untouched
- [ ] Personal-data fields restricted; nothing public by default
- [ ] Tests cover the rules above
