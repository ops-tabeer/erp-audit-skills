# Data-analytics tests per transaction cycle (SQL sketches for Odoo)

> Adapted in our own words from Romney & Steinbart, *Accounting Information Systems* 13th ed. (2014), ch. 12-16, and updated for 2026.
> Items marked **(VERIFY)** were not confirmed against a primary source when this was written: check before stating them as fact.
> `standards-current.md` (erp-controls-compliance skill) holds the confirmed versions of standards, laws and dates and wins on any conflict.
> Odoo names confirmed in Odoo 19 source: `account.lock_exception`, `account.move.checked`, `res.company.restrictive_audit_trail`,
> `hard_lock_date`, `account.journal.restrict_mode_hash_table`, `account.move.inalterable_hash`, `res.partner.bank.allow_out_payment` (tracked),
> `auth_totp.policy` = employee_required | all_required (module auth_totp_mail), `auth_passkey` (LGPL), `base.group_allow_export`,
> payment states draft/in_process/paid/canceled/rejected, `hr.version` (replaces contract fields in 19).

## 0. Ideas that apply to every cycle

The book gives each cycle the same four general threats, with the same answers each time:

| General threat | Preventive | Detective | Corrective |
|---|---|---|---|
| Wrong or invalid master data (customers, suppliers, employees, prices, CoA) | Input edits; only named roles may change master data; ERP role defaults tightened so that recording staff cannot create new partners or edit prices | Regular report of every master-data change, reviewed by someone outside the change | Correct the record and trace which transactions used the bad value |
| Sensitive data leaks (prices, bank details, salaries) | Least-privilege read access, not just write access; field-level restrictions; encryption at rest and in transit | Access logs; query-size limits so small-group averages cannot reveal one person's salary | Revoke access, rotate credentials |
| Data loss | Backups, DR; keep prod, test and a hot standby as separate instances | Restore tests (the book's worked problem has backups that turn out unreadable) | Restore from tested backup |
| Poor performance | Management reports built from process knowledge (e.g. revenue margin, inventory turnover) | KPI trend review | Process redesign |

Points from the book that carry over to ERP work:
- **Default ERP configs are permissive.** The book's example: a clerk types an unknown supplier or employee name and
  the system offers to create one. That gives the person who records a transaction the power to authorise a new
  counterparty. Turn off "create on the fly" for partners, employees and products on transactional forms.
- **Read access matters as well as write access.** Generic table browsers can expose password hashes or bank data.
  In Odoo the equivalents are developer mode, the technical menus, export, and `ir.model.access` read grants.
- **Preventive controls never cover everything,** so each one should have a detective twin: a change report, a
  reconciliation, or an exception query.
- **Segregation of duties (SoD)** comes down to keeping authorise, record, custody and reconcile in different hands.
- Subledger-to-GL reconciliation matters less in an ERP because the subledger posts the GL directly, but
  *configuration* errors (wrong default account, a manual entry on a control account) can still break it.


### 1.3 Revenue analytics (SQL sketches against Odoo tables)

Common joins: `account_move m` → `account_move_line l` (`l.move_id`) → `account_account a` (`l.account_id`);
`account_journal j` (`m.journal_id`). Filter `m.state='posted'` and `m.company_id`.

1. **Credit notes without approval / by the original seller.** `m.move_type='out_refund'` joined to the original
   via `m.reversed_entry_id`; flag when `m.create_uid = orig.create_uid`, or `= sale_order.user_id` (join
   `sale_order_line_invoice_rel` → `sale_order_line` → `sale_order`), or when no approval record exists
   (approval table depends on the custom module).
2. **Refund larger than the amount actually paid.** For each original invoice, sum the reconciled payments
   (`account_partial_reconcile` between the invoice's receivable line and payment lines) and compare with total
   out_refund + outbound customer payments for that invoice or partner. Flag refunds paid > receipts.
3. **Refund paid through a different channel than the receipt.** Receipt journal/method (`account_payment.journal_id`,
   `payment_method_line_id`, or `payment_transaction.provider_id`) vs the refund's outbound payment journal/method.
   Flag a card or Tabby receipt refunded in cash or to a third-party bank account, or a refund to a
   `partner_bank_id` whose `partner_id` is not the customer.
4. **Receipt booked to a journal that doesn't match the evidence.** Payment `journal_id.type='cash'` while the
   memo, or the linked `payment_transaction`, shows card or gateway. Or a bank statement line exists for the same
   amount and date in another journal. Match `account_bank_statement_line.amount` to `account_payment.amount` with
   a date window ±3 days.
5. **Lapping signal.** A customer payment reconciled to invoices of a *different* partner (partial reconcile where
   the debit line's `partner_id` ≠ the credit line's `partner_id`), or reconciled to invoices much older than the
   invoice it names.
6. **Delivered/issued not invoiced.** `sale_order.state='sale' AND invoice_status='to invoice' AND date_order < now()-interval '7 days'`.
   Also purchase lines (supplier ticket cost) linked to an SO that has no posted out_invoice.
7. **Price overrides.** `sale_order_line.price_unit` compared with the pricelist price, or `discount > threshold`,
   grouped by `create_uid`. Also lines with `price_subtotal < purchase_price` (negative margin, `sale_margin`).
8. **Write-offs.** Lines hitting expense accounts from receivable reconciliation (the reconcile write-off model),
   grouped by user and by partner. Several small write-offs on one partner deserve a look.
9. **Credit-limit breaches.** Partners whose open `amount_residual` on `asset_receivable` lines > `credit_limit`,
   with the confirming user.
10. **Benford / round amounts** on manual receipts (`amount % 100 = 0`) per cashier.

---


### 2.3 Expenditure analytics

1. **Duplicate vendor bills**: same `partner_id` (or same `commercial_partner_id`) with the same `amount_total`
   and either the same normalised `ref` (strip spaces, punctuation and leading zeros) or `invoice_date` within
   7 days; `move_type='in_invoice'`, posted. Also cross-company: the same supplier billed to two group companies.
2. **Vendor bank account changed shortly before payment**: `mail_tracking_value` (field `acc_number` or
   `partner_id` on `res.partner.bank`, or a new `res_partner_bank.create_date`) within N days before an
   `account_payment` with that `partner_bank_id`. Rank by amount.
3. **Vendor paid into an employee's bank account**: `res_partner_bank.sanitized_acc_number` of the payment's
   `partner_bank_id` = the sanitized number of any `hr_employee.bank_account_id` (VERIFY employee bank field name
   in 19), or the same IBAN on two partners. Also vendor address/phone/email = employee's private details.
4. **Payment with no matching bill / overpayment**: outbound supplier payments not reconciled to any
   `in_invoice` after N days; vendors with a debit balance on `liability_payable`.
5. **Bills without PO or receipt**: `in_invoice` lines with no `purchase_line_id`, above a threshold, by vendor
   and creator. `release_to_pay='exception'` released anyway.
6. **Just-below-threshold**: count of POs or payments within 95-100% of the approval limit
   (`po_double_validation_amount`, payment limit) by user; PO splitting (same vendor, same day, total > limit).
7. **New vendor, fast big payment**: vendor `create_date` < 30 days before the first payment > X; vendor created
   and paid by the same user (`res_partner.create_uid` = `account_payment.create_uid`).
8. **One-time/dormant vendors**: vendors inactive for 12 months who are suddenly paid; vendors with only one bill.
9. **Round amounts and Benford** on bills with no PO.
10. **SoD from logs**: users who both wrote `res_partner_bank` and posted `account_payment` in the same period
    (from `mail_message.author_id` / `create_uid`). This is the book's "who did which task" matrix.

---


### 3.3 Payroll analytics

1. **Ghost employees**: employees paid (`hr_payslip.state='done'`) with no `hr_attendance` rows in the period
   (for staff who must clock in), no leave, and no user login (`res_users.login_date`); or no
   passport/emirates ID (`identification_id`, `passport_id`) on file.
2. **Shared bank accounts**: `GROUP BY sanitized_acc_number HAVING count(DISTINCT employee) > 1` across
   `hr_employee.bank_account_id`; also an employee account equal to a vendor's or customer-refund account (see
   E-3, C-6).
3. **Paid after termination**: payslip `date_from` > the employee's departure date (`departure_date` or
   `active=false` set date from tracking) (VERIFY field).
4. **Bank account changed just before payday**: tracking on `bank_account_id`, or `res_partner_bank.write_date`
   within 5 days before `hr_payslip_run` close; changed by the same user who confirmed the run.
5. **Rate changes without approval**: wage changes in tracking not followed by an approval record; raises > X%;
   changes made by payroll users rather than HR.
6. **Register integrity**: per slip, sum(lines by category) vs NET; per run, sum(NET) = WPS/bank debit =
   credit to salaries payable; clearing-account balance ≠ 0 at month end.
7. **Overtime outliers**: hours > legal caps; overtime approved by the employee themself.
8. **Incentive gaming** (`hr_agent_incentive`): commission per agent vs that agent's later refunds and credit
   notes; sales booked at period end and refunded after the commission is paid.
9. **Duplicate payslips**: two `done` slips for the same employee with overlapping `date_from`/`date_to`.

---


### 4.3 GL analytics

1. **Manual entries to cash or revenue at night, weekends or holidays**: `m.move_type='entry'`, journal
   `type='general'`, lines on `account_type IN ('asset_cash','income','income_other','asset_receivable')`,
   `(m.create_date AT TIME ZONE 'UTC' AT TIME ZONE company_tz)` outside 08:00-20:00 or on Sat/Sun or a holiday table.
2. **Back-dated entries**: `m.date` well before `m.create_date::date` (e.g. > 5 days), especially into a month
   that was closed then reopened (compare with lock-date history in tracking); `m.date` in period P but created
   after P's lock date.
3. **Sequence gaps / breaks**: per `journal_id, sequence_prefix`, find gaps with
   `sequence_number - lag(sequence_number) OVER (PARTITION BY journal_id, sequence_prefix ORDER BY sequence_number) > 1`.
   Gaps can be legitimate (draft deleted before the audit trail was on), but every one needs an explanation.
   Also look for resequencing events in chatter.
4. **Hash-chain integrity**: journals with `restrict_mode_hash_table` true and posted moves lacking
   `inalterable_hash` older than the last secured date (VERIFY 19 semantics).
5. **Just-below-threshold manual entries**: amounts in [0.95·limit, limit) by user; many entries of about the
   same amount the same day.
6. **Round amounts**: manual entries where `abs(balance) % 1000 = 0` above X; Benford first-digit test on
   manual lines vs system-generated lines.
7. **Suspense ageing**: open (unreconciled) lines on each journal's `suspense_account_id`, outstanding
   receipt/payment accounts, the transfer account, and the payroll and gateway clearing accounts, aged 0-30/31-60/61-90/90+.
   Any non-zero clearing balance at month end is an exception.
8. **Unusual account pairs**: e.g. debit `asset_cash`, credit `expense` (an expense "refund" into cash), or
   debit `expense`, credit `asset_receivable` outside the write-off model. Build the pair frequency table and
   look at the rare pairs.
9. **Entries by unexpected users**: posted `entry` moves by users outside the accountant group; self-approved
   entries (`create_uid = posting user`, from tracking on `state`).
10. **Reversals after close**: entries reversed in the next period (`reversed_entry_id`) that inflated a
    period-end figure (revenue at year end reversed in January).
11. **Inter-company mismatches**: the A→B receivable vs the B→A payable by currency and period.

---


### 5.3 Cash & treasury analytics

1. **Till over/short by cashier**: `pos_session.cash_register_difference` (or the custom till model) by
   `user_id`, monthly. Repeated small shortages, or an over that offsets a later short.
2. **Late or partial deposits**: daily cash-journal receipts vs the next bank-journal statement line tagged as a
   cash deposit. Flag lag > 1 business day or amount mismatch.
3. **Refund > paid**: per SO/invoice, `sum(outbound customer payments + refund transactions) > sum(inbound receipts)`.
4. **Refund via a different channel**: original receipt journal/provider ≠ refund journal/provider; refund to a
   `partner_bank_id` not owned by the customer; refund in cash for a card receipt.
5. **Refund without a receipt**: outbound customer payment where the partner has no inbound payment ever.
6. **Refund recipient bank = employee bank** (join `res_partner_bank.sanitized_acc_number` to employee banks),
   or one account receiving refunds for several unrelated customers.
7. **Refund ratio per agent/branch**: refunds ÷ sales by `sale_order.user_id`, outliers above 2σ; refunds just
   below the approval limit.
8. **Gateway clearing not netting**: per provider clearing account, open balance by settlement date; items older
   than the provider's payout cycle (e.g. > 7 days) are exceptions. Also match `payment_transaction` (state `done`)
   with no `payment_id`, and payments with no transaction.
9. **Duplicate gateway captures**: two `done` transactions for the same SO or amount within minutes (the
   duplicate-protection check in the gateway module).
10. **Unreconciled statement lines ageing**: `account_bank_statement_line.is_reconciled = false` by journal and
    age; statement lines created manually (`create_uid` is not the import/sync user).
11. **Outgoing payments outside banking hours** or approved by the creator; payments to accounts first used that week.
12. **Security deposit ageing**: liability balance by partner/visa where the visa is closed > N days and the
    deposit isn't refunded (and excluded from revenue-recognition gap tests).

---


