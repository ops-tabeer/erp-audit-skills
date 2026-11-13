# Business-cycle threats and controls (revenue, expenditure, payroll, GL, cash & treasury)

> Adapted in our own words from Romney & Steinbart, *Accounting Information Systems* 13th ed. (2014), ch. 12-16, and updated for 2026.
> Items marked **(VERIFY)** were not confirmed against a primary source when this was written: check before stating them as fact.
> `standards-current.md` (erp-controls-compliance skill) holds the confirmed versions of standards, laws and dates and wins on any conflict.
> Odoo names confirmed in Odoo 19 source: `account.lock_exception`, `account.move.checked`, `res.company.restrictive_audit_trail`,
> `hard_lock_date`, `account.journal.restrict_mode_hash_table`, `account.move.inalterable_hash`, `res.partner.bank.allow_out_payment` (tracked),
> `auth_totp.policy` = employee_required | all_required (module auth_totp_mail), `auth_passkey` (LGPL), `base.group_allow_export`,
> payment states draft/in_process/paid/canceled/rejected, `hr.version` (replaces contract fields in 19).

### Odoo 19 platform levers used throughout
- **Groups and record rules**: `res.groups`, `ir.model.access`, `ir.rule`; multi-company isolation through
  `company_id` / `company_ids` and `check_company=True` on relational fields.
- **Change tracking**: `tracking=True` fields write to `mail_message` + `mail_tracking_value` (old and new value,
  author, date). This is the cheapest "review of master-data changes" source. Fields that are not tracked leave
  no history, so check which ones are tracked.
- **Accounting audit trail**: a company setting that blocks deleting posted entries and logs changes to them
  (`res.company.check_account_audit_trail`, added in 17.x) (VERIFY name and behaviour in 19).
- **Lock dates** on `res.company`: `fiscalyear_lock_date` (everyone), `tax_lock_date`, `sale_lock_date`,
  `purchase_lock_date`, and the irreversible `hard_lock_date` added in 18. Period exceptions go through
  `account.lock_exception` (VERIFY 19 field names).
- **Inalterability**: journal option `restrict_mode_hash_table`. Posted entries get `inalterable_hash` and
  `secure_sequence_number`, and since 18 hashing is applied through a "secure entries" wizard up to a chosen date
  rather than at every posting (VERIFY). Odoo has an integrity report that checks the hash chain.
- **Sequences**: `account_move.sequence_prefix` + `sequence_number`, per journal and per period. Resequencing is a
  privileged action.
- **Chart of accounts**: since 18, `account.account` is shared across companies (`company_ids`) and `code` is
  company-dependent (stored as JSON, not a plain column) (VERIFY for 19). That is one more reason analytics must
  filter on **`account_type`** (`asset_cash`, `asset_receivable`, `asset_current`, `liability_payable`,
  `liability_current`, `income`, `income_other`, `expense`, `expense_direct_cost`, `equity`, …) and on
  **`account_journal.type`** (`sale`, `purchase`, `cash`, `bank`, `credit`, `general`), never on code ranges.
  For suspense and clearing accounts, use per-company settings (journal `suspense_account_id`, company transfer
  account, outstanding receipt/payment accounts on payment method lines) or account tags or groups.
- **Timestamps are UTC** (`create_date`, `write_date`). Tests for night or weekend activity must convert to
  `Asia/Dubai` (UTC+4) or `Asia/Manila` (UTC+8) for each company. The UAE weekend is Sat-Sun since 2022;
  the Philippines also uses Sat-Sun.

---


## 1. Revenue cycle (sales order → delivery/service → invoice → collection)

The book's four steps are order entry, shipping, billing and cash collection. For a travel agency, "shipping"
means fulfilment: a ticket issued in the GDS, a visa submitted or approved, a hotel voucher issued. Theft of
inventory becomes issuing a service without billing it, or selling at cost to friends.

### 1.1 Threats → controls

| # | Threat (book, adapted) | Preventive | Detective | Corrective |
|---|---|---|---|---|
| R1 | Incomplete or wrong order (wrong passenger, wrong product, wrong price) | Required fields; lookups from master data instead of free text; reasonableness checks on quantity and price against history | Exception report of price overrides and discounts | Amend the SO before invoicing; credit note after invoicing |
| R2 | Order the customer later denies placing | Signed quote or online acceptance (portal signature, payment link), ID capture | Unconfirmed-order ageing | Cancel or recover cost |
| R3 | Credit sale to a customer who won't pay | Credit limit checked automatically; new customers or over-limit orders approved by someone outside sales (sales on commission push for volume) | AR ageing reviewed often; bad-debt trend | Stop further credit; collections; provision |
| R4 | Fulfilment errors or duplicates (ticket issued twice, visa filed twice) | Block lines once fulfilled; reconcile issued documents to SO lines | Compare supplier/GDS issuance reports to SOs | Void or refund with the supplier |
| R5 | Service delivered but never billed | Separate fulfilment from billing; system won't let fulfilment close without an invoice | "Delivered/issued not invoiced" report; supplier cost with no matching sale | Bill late, or investigate as theft |
| R6 | Billing errors (price, tax) | Price from pricelist; staff can't edit pricelists; tax set from fiscal position | Margin exceptions; zero or negative margin lines | Credit note and re-invoice |
| R7 | AR posting errors (payment applied to wrong customer) | Validity checks, closed-loop confirmation (show partner name), batch totals | Customer statements; AR subledger vs GL control | Re-match |
| R8 | Fake or unauthorised credit notes covering theft, or write-offs for friends | Whoever approves credit notes cannot enter sales, handle cash or edit customers; credit note must reference the invoice and either evidence (return, supplier refund) or a manager's approval | Credit notes with no approval; credit notes by creator of the original sale | Reverse; disciplinary action |
| R9 | Theft of receipts (incl. **lapping**: cover one customer's stolen payment with the next customer's) | Cash handler cannot post to AR, issue credit notes or reconcile the bank; push customers to bank transfer, card or payment links; daily intact deposit | Customer statements; deposit vs receipt reconciliation; receipts applied to older invoices of *other* customers | Recover; restate customer balances |
| R10 | Cash-flow shortfalls | Collect in advance (common in travel); early-pay incentives; gateways | Cash-flow forecast vs actual | Short-term funding |

### 1.2 Generic ERP and Odoo 19 implementation

- **Pricing and discounts**: `product.pricelist`; restrict pricelist and price edits to a pricing group. Discounts
  on `sale.order.line.discount` should be capped by group, and the sales "discount" setting gives no approval step,
  so a capped discount needs a custom constraint or a Studio approval rule (VERIFY Studio approvals in 19).
  Lock confirmed orders through the sales setting "Lock Confirmed Sales" (`group_auto_done_setting`) (VERIFY).
- **Credit limits**: the partner `credit_limit` with the accounting setting "Sales Credit Limit" warns at
  SO and invoice time. In stock Odoo this is a **warning, not a block** (VERIFY 19), so a hard block plus an
  approver needs custom code. Only a credit-manager group should be able to write `credit_limit`.
- **Fulfilment-to-invoice link**: invoicing policy on the product (`invoice_policy` = order/delivery);
  `sale.order.invoice_status` ('to invoice', 'invoiced', 'no'). The not-billed report is SOs in `sale` state with
  `invoice_status = 'to invoice'` and older than N days.
- **Credit notes**: `account.move` with `move_type='out_refund'` and `reversed_entry_id` pointing to the original.
  Restrict the "Reverse"/"Add credit note" buttons by group; Odoo doesn't natively require approval. The repo has
  custom refund-request or payment-approval modules, if you have them, which may already cover this (VERIFY scope).
- **Sale lock date** (`sale_lock_date`) stops back-dated sales documents in closed periods.
- **Customer statements**: follow-up reports (`account_followup`, Enterprise) or a portal statement serve as the
  "customer as detective control".
- **Multi-company**: an inter-company SO or invoice must hit an inter-company receivable. Record rules must stop a
  user in company A from confirming an order for company B's customer under company A's journal.


## 2. Expenditure cycle (requisition → PO → receipt → supplier bill → payment)

For the agency, the suppliers are airlines/consolidators (BSP or GDS), embassies and visa centres (VFS/TLS),
hotels, DMCs, insurers and government fee portals, plus ordinary overheads.

### 2.1 Threats → controls

| # | Threat | Preventive | Detective | Corrective |
|---|---|---|---|---|
| E1 | Buying what isn't needed; duplicate buying across units | Requisition approval; central purchasing | Spend by category vs budget | Cancel or return |
| E2 | Inflated prices | Price lists or vendor pricelists; competitive bids above a threshold; PO review | Price variance vs history; budget vs actual with exceptions highlighted | Recover from the supplier |
| E3 | Poor or unreliable suppliers | Approved-supplier list; certification | Quality/delivery KPIs per supplier | Replace supplier |
| E4 | Buying from unauthorised or sanctioned parties | System allows POs and bills only to approved, active vendors; restricted vendor creation; sanctions screening | Review of new vendors and vendor changes | Block vendor; report |
| E5 | **Kickbacks / conflicts of interest** | Gift ban; annual conflict-of-interest declarations; job rotation; mandatory leave | **Supplier audits**: red flags are the supplier relying heavily on you, odd pricing, fake addresses, altered third-party invoices | Recover; terminate |
| E6 | Accepting unordered goods/services | Receive only against an approved PO | Receipts without a PO | Return |
| E7 | Miscounting receipts | Blind receiving (hide ordered qty); receiver signs or IDs; scanning | Received vs ordered beyond tolerance | Adjust bill |
| E8 | Paying for services never performed | Budget owner confirms receipt; expenses charged to their cost centre | Budget variance; contract audits | Recover |
| E9 | Supplier-invoice errors | Match invoice price and qty to PO and receipt; **ERS** (pay from PO × receipt) where possible | Match exceptions | Debit note |
| E10 | AP posting errors | Input edits; before/after balance checks | AP subledger vs GL | Correct |
| E11 | **Duplicate payments** | Pay only from a complete voucher package (PO + receipt + original invoice); mark documents paid | Duplicate-invoice queries | Recover from supplier |
| E12 | **Theft of cash / fictitious vendors** | AP records, treasury pays (SoD); dual approval or signatures above a threshold; limited users who can create one-time vendors; vendor master locked | Bank reconciliation by someone outside AP and treasury; review of vendor master changes | Recover; prosecute |
| E13 | EFT/online-banking fraud | Strong MFA on bank portals; per-user and per-day limits; real-time approval above a threshold; dedicated banking device; ACH debit blocks on accounts that shouldn't pay out | Daily review of outgoing transfers; embedded audit queries | Recall the payment quickly (banks often require prompt notice) |
| E14 | Cheque alteration | Protected printing; special paper; **Positive Pay** | Bank rec | Bank claim |
| E15 | Missed early-pay discounts / cash crunch | Schedule by due date; cash forecast | Discounts-lost report | — |
| E16 | T&E fraud (fake boarding passes, booking several options and claiming the dearest) | Corporate cards; proof of attendance | Card-vs-claim matching | Recover from employee |

### 2.2 Generic ERP and Odoo 19 implementation

- **Vendor master**: restrict create/write on `res.partner` (supplier side) and especially `res.partner.bank`
  to a vendor-master group outside AP and treasury. Disable quick-create of partners on `account.move` and
  `purchase.order` forms.
- **Vendor bank accounts**: `res.partner.bank.allow_out_payment` ("trusted", needed for outgoing payments in
  16+). Only a non-AP approver should be able to toggle it, and any change to `acc_number` should reset it.
  Confirm that 19 blocks payments to untrusted accounts or only warns (VERIFY). Track `acc_number`,
  `partner_id` and `allow_out_payment` changes in chatter.
- **PO approval**: `res.company.po_double_validation` / `po_double_validation_amount` (Purchase setting "Order
  Approval"), with approvers in the purchase manager group.
- **Three-way match**: product `purchase_method` = 'receive' (bill on received qty), and the purchase setting
  "Bill control". Enterprise `account_3way_match` adds `account.move.release_to_pay` (yes/no/exception) to hold
  payment until receipt (VERIFY in 19). For services there is no stock receipt, so you need an explicit
  "received" confirmation by the budget owner (custom field or activity).
- **Duplicate bill guard**: Odoo warns on duplicate vendor reference (`ref`) per partner (VERIFY whether 19 blocks
  or warns). Make `ref` required on vendor bills.
- **Purchase lock date** (`purchase_lock_date`) for closed periods.
- **Payments**: `account.payment` (outbound, supplier) or batch payments (`account.batch.payment`, Enterprise)
  exported as SEPA/ISO 20022 or bank files. Odoo has no native payment approval; the options are Studio approval
  rules on `action_post`, a custom state, or doing the release in the bank portal with dual authorisation
  (VERIFY 19). Payment states changed in 18 (`draft`, `in_process`, `paid`, `canceled`, `rejected`) (VERIFY).
- **Budgets**: `account.budget` (Enterprise; in 19 possibly merged into analytic budgets) (VERIFY); the repo has
  `base_account_budget` (community). Budget vs actual by `analytic_distribution`.
- **Employee T&E**: `hr.expense` with manager approval; corporate card statement lines matched to expenses.


## 3. Payroll / HR cycle (master data → time → payroll run → disbursement → statutory remittance)

### 3.1 Threats → controls

| # | Threat | Preventive | Detective | Corrective |
|---|---|---|---|---|
| P1 | Hiring unqualified or dishonest staff | Credential and reference checks; criminal background checks for finance and cash roles | — | Terminate |
| P2 | Employment-law breaches | Documented hiring, appraisal and dismissal; keep up with law changes | HR file audits | Remediate |
| P3 | **Unauthorised payroll master changes** (rates, bank, ghost hires) | HR maintains master data, payroll only runs it, treasury pays; access matrix; HR can't release pay | Report of every pay-related change sent to each department head | Reverse; recover |
| P4 | Wrong master updates | Validity and reasonableness checks (e.g. raise above X%) | Manager review of changes | Correct next run |
| P5 | Wrong or false time/attendance (buddy-punching) | Automated capture; **biometric** clock-in; limits on hours | Reconcile attendance to job/time records by an independent person; supervisor approval; system logs for remote workers | Adjust pay |
| P6 | Payroll calculation errors | Batch/hash totals of employee IDs; cross-foot the register (gross − deductions = net); **payroll clearing account that must net to zero** | Supervisor review of the register; payslips to employees | Off-cycle correction |
| P7 | Misclassifying contractors vs employees | HR approves all temporary or outside hires | Review of contractor spend | Reclassify; pay arrears |
| P8 | **Theft / ghost or terminated employees paid** | Restrict EFT authorisation (MFA); separate payroll bank account run as an imprest (funded = net pay, so it should drain to zero); whoever releases pay has no HR duties | Review every direct-deposit record; surprise pay-out observation; follow up unclaimed pay | Recover; prosecute |
| P9 | Statutory remittances late, missed or wrong | System computes and schedules remittances from current rules | Supervisor review; employees check their payslip | Pay with penalties |
| P10 | Poorly designed incentive schemes that reward bad behaviour (book: auto-repair commissions led to unnecessary repairs) | Measurable goals aligned with company objectives; accountant review | Monitor outcomes such as refunds and complaints per agent | Redesign |

Keep terminated employees' records (deactivate, don't delete); year-end statutory reports need them. This matches
the global no-delete rule.

### 3.2 Generic ERP and Odoo 19 implementation

- **Stock Odoo 19 payroll is Enterprise (`hr_payroll`).** Many community deployments use the OHRMS stack
  instead (`hr_payroll_community`, `hr_payroll_account_community`, `ohrms_loan`, `ohrms_salary_advance`),
  often with custom deduction, incentive and biometric-attendance modules. Table names below assume that
  stack (VERIFY against your installed modules).
- **Master data**: `hr.employee` (+ `hr.contract` or the 19 equivalent: in 19 contract data may have moved onto
  the employee/version model (VERIFY)); wage fields and `bank_account_id` (→ `res.partner.bank`) restricted to an
  HR-officer group; payroll officers read-only on wage and bank. Enable tracking on wage, bank account and
  department.
- **Time**: `hr.attendance` (biometric push modules feed this); `hr.leave` with manager approval; geo-fenced
  attendance is a project in progress. Overtime approval should sit with the line manager, not payroll.
- **Run**: `hr.payslip.run` → `hr.payslip` (states draft/verify/done/cancel in community) → `hr.payslip.line`
  (codes such as BASIC, GROSS, NET). Accounting integration posts to a salary journal; use a **salaries-payable
  clearing account** that must net to zero after the WPS/bank transfer posts.
- **Disbursement (UAE)**: salaries go through the **Wage Protection System (WPS)** via an agent bank or exchange
  house using a SIF file. Reconcile the SIF total to the payslip NET total and to the bank debit. For
  Philippines: bank payroll file, then SSS, PhilHealth, Pag-IBIG and BIR withholding (1601-C monthly,
  2316 annual) (VERIFY current forms).
- **Accruals**: UAE end-of-service gratuity and leave-salary accruals; GPSSA pension for UAE/GCC nationals
  (VERIFY rates). Loans and advances (`ohrms_loan`, `ohrms_salary_advance`) must deduct automatically. Check that
  the loan balance falls to zero at offboarding (a custom offboarding module is a good place for this).


## 4. General ledger & reporting

### 4.1 Threats → controls

| # | Threat | Preventive | Detective | Corrective |
|---|---|---|---|---|
| G1 | Wrong or invalid GL data | Input edits on manual journals: account exists, numeric amounts, **debits = credits**, source required, account name shown on entry, sign check on resulting balance, run-to-run totals | Trial balance; subledger vs control account; cut-off review of entries near period end | Correcting entry |
| G2 | **Unauthorised journal entries** (incl. management override) | MFA; access matrix; most managers read-only; manual entries allowed only from controller roles | Independent review of **every non-system journal entry** (the book's main answer to reporting fraud); audit trail | Reverse; escalate |
| G3 | Unauthorised or premature disclosure of financials | Restricted access; encryption | Access logs | — |
| G4 | Wrong adjusting entries (accruals, deferrals, estimates, revaluations, corrections) | Standard recurring-entry templates; spreadsheet controls on workings | Reconciliations | Correct |
| G5 | Suspense/clearing accounts not cleared | Design clearing accounts that should hit zero | Month-end zero-balance check on every clearing/suspense account | Investigate and clear |
| G6 | Fraudulent financial reporting | Audit committee; external audit | Journal-entry testing (auditors are required to test entries and adjustments) | Restate |
| G7 | Misleading internal reports and graphs | Responsibility accounting; flexible budgets; balanced scorecard; graph design rules (axis starts at zero, time left-to-right, 2-D bars) | Review | Redesign |
| G8 | Weak audit trail | Prenumbered documents that can't be deleted; protected logs | Trace both ways: source → GL → report and report → source | — |

### 4.2 Generic ERP and Odoo 19 implementation

- **Who may post manual entries**: restrict `account.move` with `move_type='entry'` on `general` journals to an
  accountant group. Remove "Billing" users' access to Miscellaneous journals. Restrict journal access by user
  where supported (journal-level restrictions are limited in stock Odoo, so record rules on `journal_id` may be
  needed) (VERIFY).
- **Account controls**: `account.account.deprecated` stops new use. Make cash, bank, receivable and payable
  accounts unreachable from manual entries; `account.journal.account_control_ids` (allowed accounts on a journal)
  helps (VERIFY in 19).
- **Lock dates**: monthly `fiscalyear_lock_date` after close; `tax_lock_date` after each VAT return;
  `hard_lock_date` after the annual audit (irreversible, so use it deliberately). Log every lock-date change and
  `account.lock_exception` (VERIFY).
- **Inalterability**: enable `restrict_mode_hash_table` on sale, purchase, cash and bank journals; run the
  data-integrity report monthly and keep its output with close evidence.
- **Recurring entries**: `account.move` "recurring"/auto-post (`auto_post` = monthly/quarterly/yearly) and
  deferred revenue/expense (Enterprise, `deferred_start_date`/`deferred_end_date` on lines). For travel revenue
  recognition the repo has `travel_revenue_recognition`.
- **Multi-company and consolidation**: inter-company rules (`res.company.rule_type`); inter-company balances
  must net to zero across companies; FX revaluation (Enterprise "unrealized gains/losses"). Analytic plans
  (`account.analytic.plan`) give responsibility accounting by branch, agent or product.
- **Reporting**: `account.report` engine (Enterprise) for TB, P&L, BS, cash flow, VAT returns, and the custom
  `advanced_accounting_reports`. XBRL in the book's sense (SEC) isn't relevant here. The current UAE/PH analogue
  is structured e-invoice and tax-return data, plus FTA audit file (FAF) exports (VERIFY Odoo UAE localisation
  support).


## 5. Cash & treasury (tills, deposits, petty cash, bank rec, gateways/BNPL, refunds)

The book spreads cash controls over the revenue chapter (collections), the expenditure chapter (disbursements,
petty cash, Positive Pay) and the payroll chapter (imprest payroll account). This section pulls them together
for a counter-and-online travel business.

### 5.1 Threats → controls

| # | Threat | Preventive | Detective | Corrective |
|---|---|---|---|---|
| C1 | Cash taken at the counter without being recorded | Every sale gets a system receipt (customer sees it; prenumbered); cash accepted only against an SO/invoice; per-cashier till (no shared drawers); cash limits | **Blind** end-of-shift count by cashier, verified by a second person; over/short by cashier tracked over time | Recover shortages; retrain or remove |
| C2 | Receipts not banked intact / used for expenses | **Deposit all receipts intact daily**; no expenses paid out of till takings; cash-in-transit procedure | Deposit slip vs system receipts by day; bank credit date lag | Investigate the gap |
| C3 | Lapping | SoD: cash handler ≠ AR poster ≠ credit-note approver ≠ bank reconciler | Statements to customers; cross-partner reconciliation test | Restate |
| C4 | Petty cash abuse | **Imprest** fund at a fixed float; voucher plus receipt for every payout; custodian has no other cash or accounting role; replenish only against cancelled vouchers | Surprise counts (cash + vouchers = float) | Recover |
| C5 | Bank-rec manipulation | Reconciler has no access to cash, receipts or payments; statements fed by bank (API or file), not typed in | Monthly (better: daily) reconciliation reviewed; ageing of unreconciled items | Correct |
| C6 | Outgoing EFT fraud (fake vendor, changed bank details, business email compromise) | Dual control in the bank portal; per-user limits; trusted beneficiaries; call-back on any bank-detail change using a number on file; dedicated banking device; debit blocks on collection-only accounts | Daily outgoing review; Positive Pay for cheques | Recall/claim fast |
| C7 | Gateway/BNPL settlement doesn't reconcile (fees, chargebacks, holds, refunds netted) | One **clearing account per provider** (and per company); post gross sale to clearing, fees to expense, net payout to bank | Clearing account should net to zero per settlement batch; transaction-level match of provider report to `payment.transaction` | Chase provider; book fees and chargebacks |
| C8 | **Refund fraud** (refund to the agent's own card or account, refund > paid, refund of a never-paid booking, refund twice) | Refund only to the original instrument and channel; refunds need approval; supplier refund evidence (airline/embassy) for supplier-dependent refunds; refunds only by roles that can't take payments | Refund analytics below; refund ratio per agent | Recover; block |
| C9 | Cash-flow shortfall; idle surplus | Cash-flow budget/forecast fed from AR, AP and payroll | Forecast vs actual | Funding or investment |
| C10 | Security deposits treated as income | Book visa security deposits to a liability (refundable); returns go back against that liability | Liability ageing; deposits not refunded after visa closure | Reclassify |

### 5.2 Generic ERP and Odoo 19 implementation

- **Journals**: one `cash` journal per till/branch/cashier (gives per-cashier accountability), `bank` journals per
  bank account, and one journal per gateway (Tabby, Tamara, card acquirer) or a bank journal with a
  provider-specific outstanding account on its payment method line.
- **Tills**: stock Odoo till sessions with opening/closing counts exist in POS (`pos.session`:
  `cash_register_balance_start`, `cash_register_balance_end_real`, `cash_register_difference`). Back-office cash
  journals only have statement balances (`account.bank.statement` `balance_start`/`balance_end_real`). Without
  POS, a custom "till session" model is needed for blind counts (VERIFY whether the repo has one).
- **Bank statements and reconciliation**: `account.bank.statement.line` (amount, `payment_ref`, `partner_id`,
  `account_number`, `is_reconciled`, its own `move_id` hitting the journal's `suspense_account_id` until
  matched). Matching uses reconciliation models (`account.reconcile.model`). The reconciliation UI is in
  Enterprise `account_accountant`. Feeds come from bank sync or CAMT/OFX/CSV import. Restrict manual creation and
  editing of statement lines; a typed statement defeats the control.
- **Payments without entries**: in 18+ a payment can skip a journal entry when the journal has no outstanding
  account and is matched straight to the statement line (VERIFY 19). Analytics must then use `account_payment`
  as well as `account_move`.
- **Gateways**: `payment.provider` / `payment.transaction` (`reference`, `provider_reference`, `amount`, `state`,
  `payment_id`, `invoice_ids`/`sale_order_ids`). Configure each provider's payment journal; the repo forks Tabby
  as a forked gateway module with duplicate protection. Settlement reports (CSV/API) should be imported as statement lines
  on the provider journal so fees and chargebacks are booked against the clearing account.
- **Refunds**: customer credit note (`out_refund`) plus outbound customer payment (`payment_type='outbound'`,
  `partner_type='customer'`), or a provider refund transaction (`payment.transaction` with
  `operation='refund'` and `source_transaction_id`) (VERIFY). Rule: the refund payment journal or provider
  equals the original receipt's. Exceptions need an approver and a documented reason.
- **Petty cash**: a `cash` journal with an imprest float. Expenses through `hr.expense` (paid by company, cash)
  or vendor bills; top-ups as internal transfers equal to the vouchers.
- **Payroll bank account** as an imprest-style account (funded = WPS total), reconciled separately.


## 6. Production cycle (ch. 14), brief

Mostly irrelevant to a travel agency. What carries over: (a) **fixed assets**: approve acquisitions, get
competitive bids, tag and physically verify assets, record disposals (Odoo `account.asset`, Enterprise); (b)
**cost accounting**: automated capture, activity-based allocation instead of a single overhead rate (here: cost
per visa/ticket processed by agent time, via analytic plans); (c) **planning**: capacity planning maps to staff
scheduling (custom schedule overrides).

---

## 7. Modernisation: what the 2014 book doesn't cover

- **Mandatory e-invoicing / CTC.**
  - *UAE*: Peppol-based "5-corner" model through accredited service providers (ASPs), with the FTA receiving tax
    data. Ministerial Decisions 243/244 of 2025 set phased go-live: pilot from mid-2026; businesses with revenue
    ≥ AED 50M from **Jan 2027** (ASP appointed by mid-2026); others from **Jul 2027**; government entities
    late 2027 (VERIFY all dates). The ERP must produce PINT-AE structured invoices and credit notes with mandatory
    fields, handle ASP rejections, and keep invoice numbering unique and unbroken per legal entity (VERIFY Odoo
    `l10n_ae` e-invoicing support in 19).
  - *Philippines*: BIR **EIS** (Electronic Invoicing System) under TRAIN §237-A for large taxpayers, exporters and
    e-commerce, with deadlines extended repeatedly (latest reported target end-2026) (VERIFY). The **EOPT Act**
    (RA 11976, 2024) replaced official receipts with invoices for services. Computerized Accounting System (CAS)
    registration/acknowledgement is needed before an ERP becomes the books of account (VERIFY current RR/RMO).
- **Record retention.** UAE VAT: generally 5 years (longer for real estate) (VERIFY current law after
  2025 amendments); UAE Corporate Tax (FDL 47/2022): 7 years after the tax period (VERIFY); Philippines: generally
  5 years per BIR rules, with longer periods for some records (VERIFY). This argues for withdraw/archive over
  deletion (no-delete rule), hashed journals, and readable exports kept for the longest applicable period.
  UAE CT also brings transfer-pricing documentation for inter-company and related-party flows, and the
  qualifying-group and free-zone rules affect how multi-company is structured (VERIFY).
- **Real-time payments**: UAE **Aani** (instant payments) and the UAE IPP; Philippines **InstaPay/PESONet/QR Ph**.
  Instant, irrevocable transfers make pre-release controls (dual approval, payee verification) more important than
  after-the-fact recall. Use name-check or "confirmation of payee" where banks offer it (VERIFY availability).
- **Gateways and BNPL (Tabby, Tamara, cards)**: settlement is net of fees, in batches, with chargebacks and
  BNPL-specific refund flows (partial refunds reduce instalments). Needs per-provider clearing accounts,
  transaction-level matching, and webhook integrity (signature checks, idempotency, replay protection). The book's
  "credit cards cost 2-4%" line covers none of this.
- **OCR/AI invoice capture** (Odoo's AI-based digitisation, `account_invoice_extract`): it speeds up entry, but
  new risks come with it. Wrong vendor auto-matched, a bank IBAN read from the invoice into the vendor master,
  duplicates with slightly different OCR'd references, and fake invoices that look perfect. Controls: never update
  vendor bank details from a document, fuzzy duplicate checks, human approval above a threshold, confidence-score
  logging.
- **LLM/agent and RPA automation**: bots need least-privilege service users (not admin), their own identity in
  the audit trail, rate and amount limits, and SoD treated as if the bot were a person. Bot changes go through
  change management. Prompt injection through documents or emails is a new input-integrity risk.
- **Bank-side controls**: Positive Pay (still useful where cheques remain, e.g. UAE PDCs), payee-name checks,
  debit blocks/filters, host-to-host files signed and encrypted, MFA tokens per user. API bank feeds replace
  typed statements.
- **Virtual cards** for supplier payments (airline/GDS, hotels): single-use or merchant-locked cards with exact
  amounts. They cut overpayment and fraud risk, but card statements need matching to bills, and rebates must be
  booked.
- **Payroll**: UAE **WPS** compliance (SIF files, MOHRE monitoring), end-of-service gratuity, Emiratisation
  quotas and reporting (VERIFY); Philippines SSS/PhilHealth/Pag-IBIG e-remittance and BIR eFPS/eBIRForms (VERIFY).
- **Continuous monitoring** in place of periodic audit: the analytics in §1-5 run as scheduled jobs (Odoo crons
  writing exceptions to a review model or activities) instead of an annual CAAT exercise.
- **Identity**: SSO/MFA (`auth_totp`, passkeys where available), session limits, and no shared logins (shared
  logins break the audit trail every control relies on).

---

## 8. Outdated → current

| Book (2014) practice | Current equivalent / view |
|---|---|
| Paper prenumbered documents, account for every number | System sequences per journal + **gap analysis** + hash chain (`restrict_mode_hash_table`) + hard lock date |
| Two people open the mail; restrictive endorsement of cheques | Few cheques; receipts arrive by bank transfer, payment links, cards and BNPL. Controls move to webhook integrity and statement-feed reconciliation. Still needed for UAE post-dated cheques |
| Lockbox / electronic lockbox | Bank API feeds, virtual IBANs per customer, gateway payment links with reference matching |
| FEDI (EFT + EDI remittance) | ISO 20022 (pain/camt) with structured remittance; instant payments (Aani, InstaPay) with rich references |
| UPIC to hide bank details | Virtual accounts, payment links, request-to-pay |
| Cash registers with printed receipt; "free if no receipt" | POS/till sessions with blind counts, e-receipt to customer by SMS/email, mandated e-invoice to FTA/BIR |
| Check-protection machines, special inks | Positive Pay where cheques remain; mostly replaced by dual-authorised bank transfers and payee-name checks |
| Dedicated PC for online banking | Hardware MFA/passkeys, bank-portal dual control, conditional access; still useful as defence in depth |
| ACH debit blocks | Debit blocks/filters plus API-level beneficiary whitelists |
| Invoiceless billing / ERS by agreement | E-invoicing **mandatory** (UAE 2027, PH EIS), so the invoice is now a regulated data object and can't be skipped |
| EDI over VANs/AS2 | Peppol (UAE PINT-AE), APIs |
| XBRL for SEC filings | Not relevant to private UAE/PH entities; the analogue is structured e-invoices, VAT/CT returns, FTA audit file |
| GAAP → IFRS transition | UAE and PH entities already report under IFRS / PFRS (PFRS for SMEs where eligible) |
| Report of master-data changes printed for review | Field tracking (`mail_tracking_value`) + scheduled exception queries + approval workflows |
| Annual or periodic audit sampling (CAATs) | Continuous controls monitoring: full-population SQL tests on a schedule |
| Payroll cheques, surprise pay-out observation | WPS/bank files; controls move to bank-account changes, shared-account tests and ghost detection |
| Imprest payroll bank account | Still valid: fund exactly the WPS total, then verify it drains to zero |
| Biometric hand scanners at the plant | Biometric/geo-fenced mobile attendance with anti-spoofing; privacy law (UAE PDPL, PH Data Privacy Act) now governs biometric data (VERIFY) |
| Backups to tape/optical; three ERP instances | Offsite encrypted backups with restore tests (repo: nightly Drive backup); separate prod/staging; never test on prod |
| Encrypt with SSL | TLS 1.2+; encryption at rest; secrets out of config files; PCI DSS scope reduction by never storing card data (gateways tokenise) |
| Manual credit memo with credit manager signature | Credit note linked to the original invoice (`reversed_entry_id`), approval workflow, refund routed to the original instrument |
| Kickback control via gift policy and supplier audits | Still valid, plus vendor/employee data matching (bank, phone, address), beneficial-ownership checks and sanctions screening APIs |
| Graph design rules | Still valid; apply to dashboards (axes start at zero, chronological order) |

---

## 9. Quick SoD matrix for this business (incompatible pairs to test in user/group assignments)

| Role A | Must not also hold | Why (book principle) |
|---|---|---|
| Takes cash/payment at counter | Posts receipts to AR; issues credit notes or refunds; reconciles bank | Lapping; concealment by credit note; concealment by bank rec |
| Sales agent (commissioned) | Sets credit limits; approves own discounts or refunds | Incentive toward volume over collectability |
| Fulfils (issues ticket/visa) | Bills the customer | Unbilled service to friends |
| Creates or edits vendors / vendor bank | Posts bills; releases payments | Fictitious-vendor fraud |
| Posts vendor bills (AP) | Releases payments (treasury); reconciles bank | Custody vs recording |
| HR (hire, fire, pay rates, employee bank) | Runs payroll; releases WPS file | Ghost employees, retained pay of leavers |
| Payroll processor | Edits wage or bank master; reconciles payroll account | Self-authorised pay |
| Accountant posting manual JEs | Changes lock dates alone; approves own JEs | Management override |
| System admin | Any finance transaction role in prod | Bypass of all controls |

In Odoo, test this with SQL over `res_groups_users_rel` (or `res_users` group fields in 19 (VERIFY)) joined to
`res_groups` by xml id (`ir_model_data`). Also test *actual behaviour* from `create_uid` and `mail_message`
authorship (the book's employee × task count table), because assigned rights and actual usage can differ.

