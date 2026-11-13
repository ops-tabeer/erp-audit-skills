# Control frameworks, control activities and segregation of duties

> Adapted in our own words from Romney & Steinbart, *Accounting Information Systems* 13th ed. (2014), ch. 7, and updated for 2026.
> Items marked **(VERIFY)** were not confirmed against a primary source when this was written: check before stating them as fact.
> `standards-current.md` (erp-controls-compliance skill) holds the confirmed versions of standards, laws and dates and wins on any conflict.
> Odoo names confirmed in Odoo 19 source: `account.lock_exception`, `account.move.checked`, `res.company.restrictive_audit_trail`,
> `hard_lock_date`, `account.journal.restrict_mode_hash_table`, `account.move.inalterable_hash`, `res.partner.bank.allow_out_payment` (tracked),
> `auth_totp.policy` = employee_required | all_required (module auth_totp_mail), `auth_passkey` (LGPL), `base.group_allow_export`,
> payment states draft/in_process/paid/canceled/rejected, `hr.version` (replaces contract fields in 19).

## 1. Control frameworks: book vs current (as of Nov 2026)

| Framework | What the book teaches | Current state | Practical note for ERP skills |
|---|---|---|---|
| **COSO Internal Control - Integrated Framework** | Says it was issued in 1992 and updated in 2013. Table 7-1 lists the **2013** version correctly: 5 components, 17 principles. | 2013 is still the current version. COSO also issued supplemental guidance on internal control over sustainability reporting (ICSR, 2023) **(VERIFY title/date)**. | Map every ERP control to one of the 17 principles. Principles 10-12 (control activities, technology general controls, policies) carry most of the ERP work. Principle 8 (fraud risk) supports the SoD work. |
| **COSO ERM** | The 2004 "Integrated Framework": 8 components (internal environment, objective setting, event identification, risk assessment, risk response, control activities, information and communication, monitoring), the 3-D cube, and 4 objective types. The book uses ERM as its main teaching model. | Replaced by **ERM 2017 "Integrating with Strategy and Performance"**: 5 components (Governance & Culture; Strategy & Objective-Setting; Performance; Review & Revision; Information, Communication & Reporting) and 20 principles. The cube is gone and risk is tied to strategy and performance. | Treat the 8-component cube as historical. Risk registers should link each risk to a business objective and a stated appetite. |
| **COBIT** | COBIT 5 (2012): 5 principles, 5 EDM governance processes plus 32 management processes in APO/BAI/DSS/MEA (37 in total). Cites DSS05.0x, DSS06.03, BAI06/07, APO01.08 and MEA01/02. | **COBIT 2019**: 40 governance and management objectives (EDM 5, APO 14, BAI 11, DSS 6, MEA 4). New ones include APO14 Managed Data, BAI11 Managed Projects and MEA04 Managed Assurance. Adds design factors, focus areas and CMMI-style capability levels (0-5). | Most COBIT 5 IDs survive with "Managed ..." names: DSS05 is still security services and DSS06 is still business process controls. Re-check numbers that moved. |
| **ISO/IEC 27001 / 27002** | Not discussed. | **27001:2022**: Annex A has **93 controls in 4 themes**: Organizational 37, People 8, Physical 14, Technological 34. 11 controls are new, including threat intelligence, cloud services security, ICT readiness for continuity, physical security monitoring, configuration management, information deletion, data masking, data leakage prevention, monitoring activities, web filtering and secure coding. Certification transition from 2013 ended **31 Oct 2025**. Amendment 1 (2024) adds climate-change consideration to clauses 4.1/4.2. **27002:2022** gives the implementation guidance and adds attributes such as control type and cybersecurity concept. | Useful for non-US clients and cloud vendors. Pair with ISO 27017 (cloud) and 27018/27701 (privacy). |
| **NIST CSF** | Not discussed. | CSF 1.0 (2014), 1.1 (2018), then **CSF 2.0 (Feb 2024)**: six functions, **Govern**, Identify, Protect, Detect, Respond, Recover. Govern covers strategy, roles, policy, oversight and supply-chain risk. | The book's preventive, detective and corrective split maps roughly to Protect, Detect, and Respond/Recover. The book's "security is a management issue" theme is now the Govern function. |
| **NIST SP 800-53** | Not discussed. | **Rev 5** (2020, with later minor patch releases), control families AC, AU, IA, CM, SI, etc. Baselines are in **800-53B**. Privacy and supply-chain families are integrated. | Use AC-5 (separation of duties), AC-6 (least privilege), AU-2/6/9 (logging and protecting logs) and IA-2/5 (MFA, authenticators) as precise anchors. |
| **CIS Controls** | Only "download a CIS benchmark" (exercise 8.2/8.8). | **v8 (2021)** with 18 controls and Implementation Groups IG1-IG3. **v8.1 (2024)** aligns to CSF 2.0 and adds a Governance designation **(VERIFY detail)**. CIS Benchmarks remain the hardening baselines. | IG1, the "essential cyber hygiene" safeguards, is the realistic target for a small ERP shop. |
| **SOX** | Covers PCAOB, auditor independence, audit committee, CEO/CFO certification, s.404 and the SEC's requirement for a recognised framework. | Still in force for **SEC registrants only**. 404(a) is management's assessment. 404(b) is auditor attestation and applies to accelerated and large accelerated filers; non-accelerated filers are exempt. Private and non-US-listed companies are out of scope unless they are subsidiaries of a registrant. | For a UAE private group, SOX is a benchmark, not a legal requirement. Say so in skills. |
| **PCAOB AS 2201** | Not named; the book refers to "PCAOB standards". | **AS 2201** (formerly AS 5, 2007) is the integrated audit of ICFR: top-down, risk-based, and focused on entity-level controls, ITGCs and key controls. PCAOB standards were reorganised and renumbered in 2016-17. | ITGC families to test: access, change, operations, and program development. |
| **SOC reports / Trust Services** | The "Trust Services Framework" from AICPA/CICA, with 5 *principles*. A Type 2 SOC 2 report gives assurance on a cloud provider. | **SOC 1** is reported under **SSAE 18** (AT-C 320) and covers ICFR at a service organisation. **SOC 2** uses the **2017 Trust Services Criteria**, with **points of focus revised in 2022**. The five *categories* are Security (Common Criteria CC1-CC9, mapped to COSO's 17 principles), Availability, Processing Integrity, Confidentiality and Privacy. CICA is now CPA Canada. Type 1 covers design at a point in time; Type 2 covers operating effectiveness over a period. | When relying on a SaaS/ERP host's SOC report, read the **CUECs** (complementary user entity controls), check whether subservice organisations are carved out or included, check the period, and ask for a bridge letter if the period ends early. |
| **IIA model** | Says internal audit should be independent and report to the audit committee. | The **Three Lines Model (2020)** replaced "Three Lines of Defence". It is principle-based and stresses collaboration between management (1st and 2nd line) and internal audit (3rd line) under the governing body. The **Global Internal Audit Standards** were issued Jan 2024 and took effect **9 Jan 2025**: 5 domains, 15 principles, replacing the IPPF Standards. Topical Requirements followed, the first on cybersecurity **(VERIFY effective date, ~2026)**. | Use "lines", not "lines of defence". The book's reporting line for internal audit is unchanged in substance. |
| **PCI DSS** | Mentioned only by name. | **v4.0 (2022)**, **v4.0.1 (2024)**. Future-dated requirements became mandatory 31 Mar 2025, including wider MFA into the CDE and targeted risk analyses. | Keep card data out of the ERP. Use tokenising payment providers so the ERP stays out of PCI scope. |
| **Privacy and resilience law** | HIPAA and SOX only. | GDPR (2018); UAE PDPL (Federal Decree-Law 45/2021) **(VERIFY whether executive regulations are in force)**; EU NIS2 (2024) and DORA (Jan 2025) for in-scope EU entities. | Privacy is a separate chapter of the book (ch. 9). Here it only matters for access and logging. |

Related current practice the book lacks: FAIR (quantitative risk, a refinement of its
expected-loss formula), the CISA Known Exploited Vulnerabilities (KEV) catalogue, EPSS
scoring, and SBOMs.

---

## 2. Control activities catalogue (with ERP and Odoo 19 patterns)

The book's seven families are authorisation; SoD; development and acquisition; change
management; documents and records; safeguarding assets and data; and independent checks.
Monitoring and logging are added here. Each entry below gives the **purpose**, the generic
**ERP pattern**, **Odoo 19** specifics, and an **auditor test**.

General Odoo 19 notes that apply to many entries:
- Access is granted by `res.groups` (ACLs in `ir.model.access`) plus record rules
  (`ir.rule`, domain-based, which also enforce company isolation).
- Odoo 19 restructured the user form around group "privileges" (`res.groups.privilege`)
  **(VERIFY field names)**.
- Server code that calls `sudo()` bypasses both ACLs and record rules. Any custom approval
  or restriction must be checked for `sudo()` bypasses.
- `base.group_system` (Settings) and the database superuser can do anything. Treat both as
  privileged accounts.

### 2.1 Authorisation (general vs specific)
- **Purpose:** transactions happen only within authority that management delegated.
  General authority covers routine work; specific authority covers anything above a
  threshold or unusual.
- **ERP pattern:**
  - Write down a delegation-of-authority (DoA) matrix by amount, document type and company.
  - Enforce it with workflow states so a document cannot post or pay without the approval
    step, and record the approver and timestamp on the document.
  - Approver must not equal requester.
- **Odoo 19:**
  - Purchase: Settings > Purchase > *Order Approval* (two-level validation above an amount)
    puts POs in a "To Approve" state that only `purchase.group_purchase_manager` can
    approve.
  - Expenses: the manager approval stage in `hr_expense`.
  - Enterprise options: Approvals app; Studio approval rules on buttons
    (`studio.approval.rule`).
  - Community: OCA `base_tier_validation` and the `*_tier_validation` family.
  - Credit limits on partners (`credit_limit`, with an invoice warning).
  - Sales discount or price-override rules usually need custom code.
  - Custom approval modules (for example a payment-approval or refund-request module)
    must enforce *requester ≠ approver* on the server side, in the action method and not
    just in view `invisible` attributes. They must also log the approver with
    `tracking=True` fields or chatter messages.
- **Auditor test:**
  - Pull every posted document above each threshold for the period. Join it to
    approval-state history (`mail.tracking.value` on the state field, or tier-review
    records). Count items with no approval, approval after posting, or approver =
    creator (`create_uid`).
  - Try to approve your own request as a test user.

### 2.2 Segregation of duties (see section 3 for the matrix)
- **Purpose:** no one person can authorise, record and hold custody for the same
  transaction stream, so a fraud needs collusion.
- **ERP pattern:**
  - Build roles from tasks.
  - Run a SoD rule set against user-to-role assignments before granting and on a schedule.
  - Keep a register of accepted conflicts with named compensating controls.
- **Odoo 19:** groups are coarse. Accounting groups are roughly Invoicing/Billing
  (`account.group_account_invoice`), Bookkeeper/Accountant (`account.group_account_user`
  and the related basic group), Administrator (`account.group_account_manager`) and
  Read-only/Auditor (`account.group_account_readonly`) **(VERIFY labels in 19)**. Billing
  users can both create bills and register payments, so SoD needs:
  - custom groups, or button-level `groups=` restrictions on `action_post`,
    `action_register_payment` and similar actions;
  - an OCA or custom approval layer;
  - for vendor bank changes: partner bank accounts carry a trust flag (`allow_out_payment`)
    that gates outbound payments. Restrict who can set it **(VERIFY behaviour in 19)**.
- **Auditor test:**
  - Export users with their implied groups (`res.users` → `all_group_ids` / `groups_id`
    depending on version **(VERIFY)**) and run the matrix.
  - Then test *actual* conflicts from data: for the same vendor and period, find bills
    whose `create_uid` equals the `create_uid` of the payment that settled them.

### 2.3 Design and use of documents and records (sequence, audit trail)
- **Purpose:** documents are complete (none missing), sequential, carry an authorisation
  field, and can be traced from source to financial statements and back.
- **ERP pattern:**
  - System-assigned, gap-checked numbering per journal and year.
  - Voids are kept, not erased.
  - Every posted record links to its source (PO → receipt → bill → payment).
- **Odoo 19:**
  - `account.move` names come from `sequence.mixin` per journal and period. Gaps can occur
    if a draft that was already numbered is later deleted.
  - Turn on the company **audit trail** setting (Accounting settings, introduced in 17.x).
    It blocks deletion of posted entries and logs changes in chatter **(VERIFY exact
    behaviour in 19)**.
  - Use the **secure / hash** mechanism: journal "lock posted entries with hash", and in
    18+ the *Secure Entries* wizard. It chains posted moves so tampering shows up as a
    broken hash **(VERIFY 19 UI)**.
  - Keep cancellation as a reversal (`account.move.reversal`), not deletion.
  - Give the fields that matter `tracking=True`, for example amounts, partner, bank
    account, payment terms and state.
  - Keep the three-way match. Bill control policy is set on the product (received vs
    ordered quantity).
- **Auditor test:**
  - Run a gap report on each journal's sequence for the year.
  - Run the hash integrity report or check from the Secure Entries wizard.
  - Try to delete a posted entry as an accountant user; it should fail.
  - Sample 25 payments and trace each back to bill, PO and receipt.

### 2.4 Period control (lock dates)
- **Purpose:** closed periods cannot be altered after reporting. This is a form of
  authorisation over the books as a whole.
- **ERP pattern:**
  - Soft close (only a restricted role may post), then hard close (nobody may post).
  - Any reopening is logged and approved.
- **Odoo 19** (inherited from the 18 redesign):
  - Per-scope lock dates: sales, purchase, tax, fiscal-year/"everything" lock.
  - **Hard lock date**: once set it cannot be moved back, not even by an administrator.
  - Temporary **lock date exceptions** that are logged with user, reason and duration
    **(VERIFY model name, e.g. `account.lock_exception`)**.
  - Restrict the lock-date wizard to `account.group_account_manager`.
  - Set the hard lock after year-end sign-off.
- **Auditor test:**
  - List entries with `date` ≤ the lock date and `create_date` after the lock was set.
    There should be none, except those covered by a logged exception.
  - Review the exception log for the year.

### 2.5 Safeguarding assets, records and data (physical and logical access)
- **Purpose:** only authorised people can reach cash, inventory, cheque stock and data.
  The book stresses insiders, unlocked cheque stock, and unencrypted laptops (the VA case).
- **ERP pattern:**
  - Least-privilege roles; record-level restriction by company, branch and team.
  - Field-level hiding of sensitive data (salaries, bank details, national IDs).
  - Treat payment-file and bank-integration credentials as custody.
- **Odoo 19:**
  - Multi-company record rules.
  - `groups=` on sensitive fields: employee private data, `bank_account_id`, contract
    wage.
  - HR private fields are restricted to HR officer groups by default **(VERIFY in 19)**.
  - Inventory: separate stock users from inventory adjusters
    (`stock.group_stock_manager` applies counts).
  - Server hardening: `list_db = False`, a strong `admin_passwd` (master password),
    `dbfilter`, `proxy_mode` behind TLS, no exposed database manager, PostgreSQL not
    reachable from outside, and filestore permissions.
- **Auditor test:**
  - Log in as each role and try to open payroll, employee bank data and other companies.
  - Try `/web/database/manager` from the internet.
  - Reconcile asset register to a physical count, and inventory valuation to the GL.

### 2.6 Independent checks on performance
- **Purpose:** a second person, record or process catches errors. The book's checks are
  top-level review, analytical review, reconciliation of independent records, counts
  against records, double entry, and second-person review. Re-adding your own work does
  not count as independent.
- **ERP pattern:**
  - Bank reconciliation done by someone who cannot record receipts or payments.
  - Subledger-to-GL ties: AR, AP, inventory, payroll liabilities.
  - Budget vs actual.
  - Analytics on margins and on relationships such as sales vs receivables.
- **Odoo 19:**
  - Bank reconciliation widget and reconcile models. Statement import is better than
    manual entry.
  - Aged receivable and aged payable reports vs the GL account balance.
  - Stock valuation layers vs the GL.
  - `base_account_budget` in this repo, or enterprise budgets.
  - The "To check"/`checked` flag on moves to force reviewer sign-off **(VERIFY field name
    in 19)**.
  - Locate accounts by **account type, tags or company settings, not hard-coded codes**.
- **Auditor test:**
  - Re-perform one month's bank reconciliation. Check that the preparer and reviewer
    differ and that the review is dated.
  - Tie the aged AP total to the AP control balance.

### 2.7 Change management and development controls
- **Purpose:** changes do not break reliability or open a back door. The book asks for:
  documented requests, approvals, testing in a separate environment, conversion controls,
  updated documentation, after-the-fact approval of emergency changes, back-out plans, and
  re-checking user rights during the change.
- **ERP pattern:**
  - Git-based: PR review by someone other than the author.
  - CI tests; staging copy of production; deploy by a role other than the developer.
  - No direct production code or database edits.
  - Emergency fixes get a ticket and are reviewed after the fact.
- **Odoo 19 and this repo:**
  - Custom modules live in their own addons folder. Changes go through feature branches and PRs.
    Do not push straight to main.
  - Upgrades run via `-u module`.
  - Developer mode and `base.group_system` allow live edits of views, server actions and
    automated actions with Python code. These count as code changes and must be
    restricted.
  - Studio changes are also changes.
  - Data migrations need record-count and control-total checks (the book's conversion
    controls).
- **Auditor test:**
  - Sample production deployments. For each, find a PR, a reviewer ≠ author, and passing
    CI.
  - List `ir.actions.server` and `base.automation` records with `code`, plus `ir.ui.view`
    records changed in production since the last release (`write_date`). Every one should
    trace to a change ticket.

### 2.8 HR and entity-level controls (internal environment)
- **Purpose:** the culture and people controls the book stresses, which an ERP
  supports but cannot replace: background checks, a code of conduct, training,
  mandatory vacation and rotation, immediate removal of access at termination,
  confidentiality agreements, fidelity bonding/crime insurance, and a whistle-blower
  channel.
- **ERP pattern:**
  - Joiner-mover-leaver (JML) tied to HR status.
  - Leave records used to schedule the "who covered this role" review.
- **Odoo 19:**
  - Archiving the user (`active=False`) on termination stops logins. Also revoke API keys
    and sessions.
  - A custom offboarding module is the natural place to make deactivation
    automatic (**withdraw, don't delete**).
- **Auditor test:**
  - Compare the leavers list against users who are still active, users with logins after
    their exit date, and API keys still active.

### 2.9 Monitoring and logging
- **Purpose:** the book wants logs that show who did what, when and from where; regular
  review of those logs; logs protected from alteration ("audit the audit trail"); and
  continuous monitoring of compliance.
- **ERP pattern:**
  - Business-event logging (field changes, approvals).
  - Security-event logging (logins, failures, privilege changes).
  - Forward both to central storage the ERP admins cannot alter.
- **Odoo 19:**
  - Field tracking in `mail.tracking.value`.
  - `res.users.log`, which records successful logins only.
  - Failed logins appear in the server log. Odoo applies a login cooldown after repeated
    failures, set by the `base.login_cooldown_after_failure` / `_duration` parameters
    **(VERIFY)**.
  - No full CRUD audit log in core; OCA `auditlog` adds one, at a performance cost.
  - Ship the Odoo and nginx logs to a SIEM or log store.
- **Auditor test:**
  - Pick 5 sensitive changes (vendor bank, credit limit, wage) and confirm each has a
    tracking record naming who changed it.
  - Confirm the log store keeps entries the Odoo admin cannot change.

---

## 3. Segregation of duties: ERP finance conflict matrix

The book's core rule is to separate **authorisation**, **recording** and **custody**. For
systems work it also separates systems administration, network, security, change, users,
analysts, programmers, operators, librarian and data control. In ERP terms each pair below
is a *conflict*: the same user should not hold both roles. Where a small team cannot split
them, use the compensating control listed. The book's own answer for small firms is closer
supervision, mandatory vacation/rotation, independent review, and owner involvement.

| # | Conflict (A vs B) | Risk if combined | Compensating control when it cannot be split |
|---|---|---|---|
| 1 | Create/edit **vendor master** (incl. bank account) vs **enter vendor bills** | Fictitious vendor and invoices (the book's limousine supervisor case) | Second-person approval for any new vendor or bank change. Weekly report of new and changed vendors and banks from tracking, reviewed by the owner or CFO. Call back on a known phone number before trusting a new bank account. |
| 2 | Vendor master/bank vs **release payments** | Redirecting a real vendor's payment to an attacker or insider account (also a BEC/fraud vector) | Payments only to trusted bank accounts (`allow_out_payment`). Bank-portal dual authorisation, with the releaser outside finance entry. Owner reviews the payee list for each payment batch. |
| 3 | Enter/approve **vendor bills** vs **pay** | Paying unapproved, inflated or duplicate bills (Springer's) | Three-way match enforced. Duplicate-reference warning. Bank-side dual approval. Monthly vendor-statement reconciliation by someone else. |
| 4 | **Purchase order approval** vs **goods receipt** | Paying for goods never received | Receipt by stores or the requester. Periodic stock count. Review of GRNI (goods received, not invoiced) and of receipts that have no PO. |
| 5 | **Record customer receipts** vs **bank reconciliation** | Lapping and stolen receipts hidden by adjustments (the Fairfax treasurer) | Owner or outside accountant does or reviews the bank reconciliation monthly, from statements fetched directly from the bank feed. Review unapplied credits and manual reconciliation write-offs. |
| 6 | **Handle cash/cheques** (custody) vs **post receipts to AR** | Skimming, then concealment by crediting the customer | Payments go to a lockbox or bank directly; payment links or gateways rather than cash. Daily deposit of all receipts. Customer statements sent by someone else. |
| 7 | **Create credit notes** vs **approve refunds** vs **pay refunds** | Fake refunds to a colluding customer, or to self (the book's credit-card write-off collusion case) | Three distinct steps in the refund workflow, with approver ≠ requester enforced on the server. Refunds paid only to the original payment instrument or account. Monthly review of credit notes by user and by customer. Alert on refunds to a partner that differs from the original payer. |
| 8 | **Write off receivables / bad debt** vs **cash receipt or AR posting** | Theft concealed as write-off (Covington condition 2) | Write-offs above a small limit need approval. Write-off report reviewed by the owner. Spot-check by confirming balances with customers. |
| 9 | **Post manual journal entries** vs **approve/review JEs** | Earnings management, concealment entries (the book's "creative accounting" controller) | Every manual JE is reviewed by someone else, using the `checked` flag or an approval module. Report of JEs posted by senior finance staff, after hours, to revenue or cash accounts, or with round amounts. |
| 10 | **Post JEs** vs **set/lift lock dates** | Back-dating into closed periods | Lock dates set only by the CFO or owner. Hard lock after sign-off. Lock exceptions logged and reviewed at month end. |
| 11 | **User/role administration** (`base.group_system`, `base.group_erp_manager`) vs **any finance transaction role** | Granting oneself rights, acting, then revoking them; erasing evidence | Admin accounts are separate, named and MFA-protected, and not used for daily work. Group-membership changes are logged and sent to the owner. Quarterly access recertification by business owners. Use break-glass procedures for the superuser. |
| 12 | **Developer / code deploy** vs **production data or transactions** | Logic changes that divert funds; the credit-union programmer case | PR review by another person. No developer in production finance groups. Server actions with code restricted. Diff of deployed code against the reviewed commit. |
| 13 | **Payroll master data** (employees, wage, bank) vs **payroll processing/payment** | Ghost employees and inflated pay (the Dodgers case) | HR owns employee and wage changes. Payroll runs the payslips. The finance owner approves the bank file. Monthly headcount and pay comparison vs the prior month. Review of new hires, bank changes and terminations. |
| 14 | **Timesheet/attendance approval** vs **payroll run** | Paying unworked hours | Approval by line managers. Biometric attendance as source data (`odoo_biometric_attendance`). Exceptions report on overtime. |
| 15 | **Sales order / price or discount entry** vs **approval of pricing exceptions** | Discounts given to colluding customers | Discount thresholds with approval. Margin analytics by salesperson. The repo's agent-cost minimum rule is a good preventive example. |
| 16 | **Inventory custody** vs **inventory adjustments** | Theft hidden as shrinkage | Adjustments approved by someone outside stores. Blind cycle counts. Reason codes on adjustments. |
| 17 | **Fixed asset custody/disposal** vs **asset records** | Unrecorded disposals (the Lancaster case) | Disposal needs approval. Periodic asset count reconciled to the register. |
| 18 | **Loan/advance approval** vs **disbursement** vs **recovery** (`ohrms_loan`, `ohrms_salary_advance`) | Self-approved or never-recovered advances (the Greater Providence case) | Approval limits per approver. Requester ≠ approver. Monthly aged report of outstanding advances, reviewed by someone else. |
| 19 | **Security administration** vs **log review** | Admin hides own actions | Logs shipped off-box to a store admins cannot alter. Log review by the owner or an outsourced provider. |
| 20 | **Bank/API integration credentials** (payment provider, bank host-to-host) vs **finance posting** | Direct custody of funds via the API | Secrets stored in a vault or environment, not in the DB UI. Provider-side approval for payouts and refunds. Periodic rotation and access review. |

Using the matrix in practice:
- Run it per company in multi-company setups. A conflict can arise across companies.
- Watch for *implied groups*: an Administrator group implies the user groups below it.
- Evaluate on effective rights, including `sudo()` paths in custom buttons, not just the
  group names shown on the user form.
- Accepted conflicts go in a register with owner, reason, compensating control, review
  date, and evidence of the control actually operating.

---


