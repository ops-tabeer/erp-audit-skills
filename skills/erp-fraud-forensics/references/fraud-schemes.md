# Fraud theory and ERP fraud schemes with detection tests

> Adapted in our own words from Romney & Steinbart, *Accounting Information Systems* 13th ed. (2014), ch. 1-2, 5, and updated for 2026.
> Items marked **(VERIFY)** were not confirmed against a primary source when this was written: check before stating them as fact.
> `standards-current.md` (erp-controls-compliance skill) holds the confirmed versions of standards, laws and dates and wins on any conflict.
> Odoo names confirmed in Odoo 19 source: `account.lock_exception`, `account.move.checked`, `res.company.restrictive_audit_trail`,
> `hard_lock_date`, `account.journal.restrict_mode_hash_table`, `account.move.inalterable_hash`, `res.partner.bank.allow_out_payment` (tracked),
> `auth_totp.policy` = employee_required | all_required (module auth_totp_mail), `auth_passkey` (LGPL), `base.group_allow_export`,
> payment states draft/in_process/paid/canceled/rejected, `hr.version` (replaces contract fields in 19).

## 1. Fraud theory that still holds

**Legal elements of fraud** (ch05): a false representation, of a material fact, made with intent to
deceive, that the victim justifiably relied on, causing loss. Useful for incident write-ups: an
investigation must evidence each element, not just "money missing".

**Four threat classes to an AIS**: disasters; software/hardware failure; unintentional human error
(the book says the biggest loss source); intentional acts (sabotage, misappropriation, financial
statement fraud, corruption, computer fraud). Skills should not assume every anomaly is fraud: error
is the base rate.

**Two fraud families that matter to an ERP**
| | Asset misappropriation ("employee fraud") | Fraudulent financial reporting ("management fraud") |
|---|---|---|
| Frequency | Far more common | Rare |
| Size | Smaller per case | Much larger per case |
| Typical ERP trace | Payments, refunds, credit notes, cash, payroll, vendor master | Manual JEs at period end, revenue cut-off, reserves, capitalisation |
| Book's lesson | Concealment leaves more evidence than the theft itself | Watch management override of controls |
Also named: corruption (bribery, bid rigging, kickbacks) and investment fraud (Ponzi).

**Fraud triangle** = pressure + opportunity + rationalisation; usually all three present for a
first-time fraudster. Predatory/serial fraudsters need only opportunity. The organisation controls
opportunity most directly, so controls aim there.
- *Pressure*: financial (debt, living beyond means), emotional (greed, resentment at being passed
  over, "beat the system"), lifestyle (gambling, addiction, relationships). For reporting fraud:
  earnings targets, covenants, cash-flow trouble, aggressive incentives.
- *Opportunity* has three parts, and each is a control target:
  1. **Commit** (do the act), 2. **Conceal** (keep the books balancing: hide in an expense account
  that closes at year end, or keep rolling a balance-sheet cover such as lapping), 3. **Convert**
  (turn it into spendable value).
- *Rationalisation*: "borrowing it", "they owe me", "no one gets hurt", "everyone does it", "rules
  don't apply to my role".

**Who commits**: mostly trusted insiders with access and system knowledge; usually no prior
record; psychologically similar to the general public. Owner/executive frauds run longer and cost
more. Frauds rarely stop voluntarily; they grow in size and frequency until a mistake or the sheer
amount exposes them. Not prosecuting creates serial fraudsters who move to the next employer.

**Red flags** (personal): lifestyle above salary; refuses leave/rotation; works odd hours alone;
over-protective of own area; close ties to particular customers/vendors; recent grievance.
(Organisational): weak SoD; too much trust in key people; no independent checks; no audit trail;
year-end adjusting entries; crisis mode with controls suspended; understaffed accounting; long
tenure in one key job; no background checks; low prosecution appetite.

**Computer fraud by processing stage** (still a good taxonomy for ERP control mapping):
input (alter/falsify entries: most common, least skill), processor (unauthorised system use),
computer instructions (tampered code/modules), data (copy/browse/damage data), output (forged
or stolen reports, cheques, payslips).

**Prevention/detection levers (Table 5-5, condensed)**
- Make fraud less likely: tone at top, code of conduct, HR screening, mandatory vacations,
  rotation, employee assistance, change management, prosecute.
- Make it harder: SoD of authorise / record / custody; system authenticates both the person and
  their right to do this transaction; independent reconciliations; input/processing controls.
- Detect better: fraud risk assessment, end-to-end audit trail, surprise audits, analytics,
  hotline with whistleblower protection, activity monitoring.
- Reduce loss: insurance (crime/fidelity), backups off-site, response and continuity plans.
- Book's single most effective control: **segregation of duties**. Rotation is singled out as the
  best deterrent to lapping-type ongoing cover-ups.

**ERP control points from ch01-02**
- System-assigned sequential numbers make completeness provable; **gaps signal missing or deleted
  documents**.
- Subsidiary ledger totals must equal the GL control account; any difference is an error or a
  concealment.
- An audit trail must run both ways: statement line -> source document and source -> statement.
- In an integrated ERP, a bad input propagates everywhere, so input validation and access control
  are the core controls; role design is the ERP form of SoD.
- Policy checks belong in the system (credit limit, stock, approval) rather than in people's heads.

---

## 2. Fraud schemes catalogue for an ERP, with detection tests

Notation: `am` = account_move, `aml` = account_move_line, `ap` = account_payment, `apr` =
account_partial_reconcile, `aa` = account_account, `aj` = account_journal, `rp` = res_partner,
`rpb` = res_partner_bank, `ru` = res_users, `mm` = mail_message, `mtv` = mail_tracking_value,
`imf` = ir_model_fields. Restrict every test by `company_id` and a date window. Convert user
timestamps (stored UTC) to the company tz (e.g. Asia/Dubai) before hour-of-day tests.

### 2.1 Skimming (sale or receipt never recorded)
- ERP trace: none directly; absence of revenue. Shows as gaps between operational records (bookings,
  delivered services, POS sessions) and invoices/receipts.
- Tests: sale_order / service records in state done with no posted `am` (move_type out_invoice) linked
  via invoice lines; POS/cash session expected vs counted difference trend per cashier; revenue per
  cashier/agent vs peers by weekday.

### 2.2 Under-ringing / discount abuse (book: full price sold, half price recorded)
- Trace: invoice/order line price below list or below cost; discounts entered by the same user
  who received payment.
- Tests: `sale_order_line.discount` > policy threshold or `price_unit` < product list price, grouped
  by `create_uid`; share of discounted lines per user z-score; price changes after confirmation via
  `mtv` on sale.order.line price_unit.

### 2.3 Lapping (receipt from A stolen, later receipt from B applied to A)
- Trace: customer payments reconciled to older invoices of a *different* partner, or payment partner
  differs from invoice partner; ageing that "rolls"; frequent unreconcile/re-reconcile.
- Tests: `apr` joins where debit `aml.partner_id` != credit `aml.partner_id` on receivable accounts;
  `ap.partner_id` != partner of the invoice it settles; receipts whose bank statement payer name
  (`account_bank_statement_line.partner_name`) differs from `ap.partner_id`; count of unreconciliations
  per user (`mm` on account.move with tracking of payment_state flipping back). Rotation and customer
  statements sent by someone other than the cashier are the classic breakers.

### 2.4 Fake refunds / fictitious credit notes
- Trace: out_refund or manual liability entries for customers with no original sale, no customer
  request, or refunds exceeding what the customer paid; refund paid in cash or to a bank account not
  belonging to the customer.
- Tests:
  - `am.move_type='out_refund'` with `reversed_entry_id IS NULL` (credit note not derived from an
    invoice) or refund amount > original invoice residual paid.
  - Customer outbound payments: `ap.payment_type='outbound' AND ap.partner_type='customer'`; flag
    where `aj.type='cash'`, or where the settled debit line belongs to `move_type='entry'` (manual
    JE) instead of an out_refund.
  - Refunds where create_uid of the credit note = create_uid of the payment = approver.
  - Refund total per partner > lifetime receipts from that partner.
  - Refunds against partners/orders with no activity in the last N months ("dormant" or legacy).

### 2.5 Cheque kiting / float abuse
- Classic form mostly dead (see section 4). Modern analogue: moving money between own bank/cash/wallet
  journals around period end, or between companies, to show balances that do not exist.
- Tests: internal transfers (`ap.is_internal_transfer` / paired transfer moves, VERIFY field name in
  19) near month-end that reverse within days; inter-company receivable/payable that do not net;
  bank journal book balance vs `account_bank_statement` balance_end_real at each cut-off.

### 2.6 Ghost vendors / fictitious invoices (book: forged approvals, PO-box suppliers, sub-threshold
invoices)
- Trace: vendor created and paid by the same user; vendor without VAT/TRN, phone, or address; vendor
  address/phone/bank matching an employee; invoices just under the approval limit; round amounts.
- Tests: `rp.supplier_rank>0` with `rp.create_uid` = `ap.create_uid` of its first payment; `rp.vat IS
  NULL`; join `rpb.acc_number` (normalised, spaces stripped) to `hr_employee.bank_account_id` ->
  `rpb.acc_number`, and `rp.phone/email/street` to `hr_employee.private_*` fields; in_invoice count
  where `amount_total` in [0.9 x limit, limit); first-payment-within-N-days-of-vendor-creation.

### 2.7 Duplicate payment (book: copied supporting documents, look-alike payee)
- Tests: in_invoice with same `partner_id` and same `ref` (normalised) or same amount + invoice_date
  within 30 days; vendors with near-identical names (trigram similarity via pg_trgm) but different
  bank accounts; payments where `ap.partner_bank_id` belongs to a different partner than `ap.partner_id`.

### 2.8 Vendor bank-detail change fraud (internal or BEC-driven)
- Trace: `rpb` row created/edited shortly before a large payment; new bank account outside home
  country; change made by AP clerk who also releases payments.
- Tests: `rpb.create_date` or `mtv` change on res.partner.bank (acc_number / allow_out_payment;
  VERIFY tracked fields) within 14 days before `ap.date`; `rpb.allow_out_payment` flipped to true by the
  same user who then paid; payments to `rpb` created < 30 days ago above threshold.

### 2.9 Ghost employees / payroll padding (book: supervisor kept turning in time for a departed
worker; programmer redirected tax withholdings to himself)
- Tests: payslips (`hr_payslip`) for employees with `active=false`, departure date before slip
  period, or no attendance records (`hr_attendance`) in the period; two employees sharing a bank
  account; salary/contract wage changes (`mtv` on hr.contract or hr.version in 19, VERIFY model)
  made by payroll user on own record or on a peer without HR approval; reconciliation of payslip
  deduction totals to amounts actually remitted (the book's tax-withholding lesson).

### 2.10 Expense reimbursement fraud
- Trace: personal items, duplicate receipts, fictitious receipts, mischaracterised spend, inflated
  mileage; executives having subordinates book personal costs as company invoices.
- Tests: `hr_expense` with same attachment checksum (`ir_attachment.checksum`) across expenses;
  same amount/date/employee duplicates; weekend/holiday dates; Benford and round-number tests per
  employee; expenses approved by a subordinate of the claimant (approver's `parent_id` chain).

### 2.11 Manual journal-entry fraud (concealment or reporting fraud)
- Trace: `move_type='entry'` posted by non-accountants; entries touching cash, receivable/payable,
  revenue or refund-liability accounts; posted outside hours; back-dated; round amounts; vague
  `ref`/line name; reversed soon after period close.
- Tests:
  - JEs where any line has `aa.account_type IN ('asset_cash','asset_receivable','liability_payable')`
    and `am.move_type='entry'` and no `origin_payment_id` / `statement_line_id`.
  - `am.create_uid` not in accountant group, or `create_uid = posting user` with no reviewer.
  - Back-dating: `am.date < (am.create_date AT TIME ZONE tz)::date - N` days, or `am.date` in a
    period that was later locked; date edits via `mtv` where `imf.name='date'` and model account.move.
  - Hour-of-day: `extract(hour from create_date at tz)` outside shift; days the user was on leave
    (`hr_leave`).
  - Round amounts (`balance % 100 = 0`), and amounts just under approval thresholds.
  - Reversals: `am.reversed_entry_id` set within 10 days after a period end.

### 2.12 Round-tripping / fictitious revenue / channel stuffing
- Trace: revenue from a partner who is also paid an equal amount (vendor bill, "commission", "refund")
  shortly after; sales booked before period end, credited after.
- Tests: partners with both out_invoice and in_invoice/out_refund of similar amounts within 60 days;
  out_refund in first 15 days of a period against invoices of the last 5 days of the prior period;
  related-party flags on `rp` (shared directors, address, bank with staff).

### 2.13 Salami / round-down (tiny slices diverted)
- Mostly a custom-code risk now: rounding differences, FX differences or fees posted to an account
  someone controls.
- Tests: tiny-amount lines (|balance| < 1) concentrated on one partner/account; FX gain/loss or
  rounding accounts with growing balances; code review of any module touching rounding.

### 2.14 Data diddling / record alteration after the fact
- Tests: `mtv` on account.move / account.move.line / sale.order / res.partner for fields amount,
  partner_id, date, account_id, bank, made after posting, by user, by hour; posted moves reset to
  draft (`mtv` state posted -> draft) and re-posted with different amounts.

### 2.15 Deletion and sequence gaps (book: sequence codes reveal missing items)
- Odoo blocks deleting posted moves and moves that are not last in a sequence chain, but a draft or
  the last entry can be deleted, and admin/SQL/shell can bypass the ORM.
- Tests:
  - Gaps: per `journal_id, sequence_prefix`, `sequence_number - lag(sequence_number) > 1`.
  - Reused numbers: `am.posted_before = true` history or `mm` messages pointing to an `am.name` that
    now belongs to a different record.
  - Orphan chatter: `mm.model='account.move' AND mm.res_id NOT IN (SELECT id FROM account_move)`
    reveals deleted moves; same for account.payment, res.partner.bank.
  - Compare nightly backups: moves present in backup D but absent in D+1.
  - Hash chain: journals with `restrict_mode_hash_table` true; run the integrity report (VERIFY field
    location in 19).

### 2.16 Superzapping / admin bypass
- Trace: writes by `ru.id IN (1,2)` (root/admin) or service users; records whose `write_uid` is a
  technical user; ORM-bypassing SQL leaves no `mtv`.
- Tests: accounting records with `write_date` changes but no corresponding `mm`/`mtv`; users holding
  both `account.group_account_manager` and `base.group_system`; frequency of `sudo`-capable custom
  actions (server actions with code) and who runs them.

### 2.17 Benford's Law (book's analytics example)
- First-digit test: compare `left(regexp_replace(abs(amount)::text,'[^1-9]','','g'),1)` distribution
  per user/journal/vendor with log10(1+1/d); flag chi-square or MAD outliers. Use on populations of
  several hundred+, not on capped or assigned numbers (prices, fees).

---


## 5. Worked example: a cashier with accounting-admin rights (illustrative scenario)

Profile: one person held cash custody (till), recording rights (manual JEs, credit notes) and
authorisation (self-approval) plus accounting-admin. That is the book's textbook failure: no
separation of authorise / record / custody, and an insider who knows where the system is not
reconciled. The book's point that "there are no small frauds, only ones caught early" applies:
expect escalation over time.

### (a) Fake refund liabilities on legacy-system orders, then cash paid out at night
- Book concepts: asset misappropriation; opportunity triangle (commit via JE, conceal by creating a
  liability that the payout then clears so the books self-balance, convert via cash); input fraud /
  data diddling; targeting data nobody can verify (legacy orders lack an independent subsidiary
  record to reconcile against); odd-hours activity red flag; superzapping-style use of admin rights
  to bypass the normal refund path.
- Preventive: cashier role cannot post `move_type='entry'`; manual JEs touching refund-liability,
  receivable or cash accounts require a second approver; journal `account_control_ids` / allowed
  accounts limited; legacy-order refunds require evidence of the original receipt and finance
  approval; cash payouts above a small float only via approved refund request; cash journal
  operations blocked outside shift hours.
- Detective: daily independent cash count and till reconciliation; test 2.4 (customer outbound
  cash payments settling a manual JE); test 2.11 hour-of-day; ageing review of refund-liability
  account by someone outside the cashier's line; customer confirmation of refunds received.

### (b) Cash refunds when the customer asked for bank/Tabby, self-approved
- Book concepts: conversion step (cash is directly spendable, bank/Tabby is traceable); lack of
  independent authorisation; customers as the independent check (like the book's withholding
  reconciliation that exposed the payroll programmer).
- Preventive: refund method forced to original payment method (Tabby refunds through the provider,
  card back to card); cash refunds only for cash-paid orders and only with customer-signed
  acknowledgement and ID; approver must differ from requester and from the payer (enforced in code,
  not policy); notify the customer automatically (SMS/email) when a refund is recorded, stating
  method and amount.
- Detective: compare refund method vs original receipt method; refunds where requester = approver
  = payment creator; customer complaints/tips channel monitored by finance, not by the till.

### (c) Back-dated entries
- Book concepts: concealment; audit-trail integrity; numerous/odd adjusting entries; the
  reporting-fraud cut-off tricks (holding books open, closing early) applied to hide theft in a
  reviewed period.
- Preventive: lock dates (`fiscalyear_lock_date`, `sale/purchase/tax lock`, `hard_lock_date` in
  Odoo 18+, VERIFY names in 19) set promptly after each close; only the controller can change them;
  entries dated more than N days before creation blocked or routed to approval.
- Detective: test 2.11 back-dating (`date` vs `create_date`); `mtv` date edits; report of entries
  posted into periods already reviewed.

### (d) Credit notes outside the refund workflow
- Book concepts: lack of proper authorisation procedures; bypass of designed documents; input fraud.
- Preventive: only the refund module can create `out_refund` for front-office roles; credit notes
  must link to an approved refund request and to the original invoice (`reversed_entry_id`); amount
  capped at paid amount.
- Detective: out_refund with no refund-request link or no `reversed_entry_id`; refund total per
  creator per week; credit notes where partner had no recent invoice.

### (e) Deleted entries, sequence gaps
- Book concepts: sequence codes make missing items visible (ch02); concealment by destroying records
  (like removing cancelled cheques from the reconciliation in the book's serial-embezzler case);
  audit-trail destruction; superzapping.
- Preventive: remove `unlink` on account.move/account.payment from non-manager roles (ACL
  perm_unlink=0); journal hash/restrict mode on cash and sales journals; nobody with till custody has
  admin or DB access; DB-level audit (pgaudit) on DELETE for accounting tables.
- Detective: gap test and orphan-chatter test (2.15); diff consecutive nightly backups for vanished
  move ids; alert on any deletion of accounting records.

### Cross-cutting lessons
- SoD first: split till custody, JE/credit-note recording, refund approval and admin rights across
  different people; run an SoD conflict matrix on `res_groups` membership monthly.
- Mandatory leave and rotation for cash roles (the book's top deterrent for rolling cover-ups).
- Admin rights are a red flag on any operational user; review privileged users quarterly.
- Prosecute or at least formally document and report: the book's serial-embezzler case shows quiet
  dismissal just moves the fraud to the next employer.
- Build detection as scheduled queries with owners outside the cashier's reporting line.

