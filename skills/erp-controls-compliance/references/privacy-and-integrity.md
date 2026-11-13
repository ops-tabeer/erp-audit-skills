# Confidentiality, privacy and processing-integrity controls

> Adapted in our own words from Romney & Steinbart, *Accounting Information Systems* 13th ed. (2014), ch. 9-10, and updated for 2026.
> Items marked **(VERIFY)** were not confirmed against a primary source when this was written: check before stating them as fact.
> `standards-current.md` (erp-controls-compliance skill) holds the confirmed versions of standards, laws and dates and wins on any conflict.
> Odoo names confirmed in Odoo 19 source: `account.lock_exception`, `account.move.checked`, `res.company.restrictive_audit_trail`,
> `hard_lock_date`, `account.journal.restrict_mode_hash_table`, `account.move.inalterable_hash`, `res.partner.bank.allow_out_payment` (tracked),
> `auth_totp.policy` = employee_required | all_required (module auth_totp_mail), `auth_passkey` (LGPL), `base.group_allow_export`,
> payment states draft/in_process/paid/canceled/rejected, `hr.version` (replaces contract fields in 19).

## 1. Confidentiality and privacy

### 1.1 What the book teaches (ch. 9)
- Confidentiality (business secrets: plans, pricing, cost data, contracts) and privacy (personal
  data of customers, staff, suppliers) share **four controls**: (1) identify & classify,
  (2) encrypt, (3) control access across the whole life cycle, (4) train people.
- **Classification belongs to the information owner**, not to IT security (COBIT 5 APO01.06);
  controls follow the class.
- Encryption is necessary but never sufficient: data is plaintext while processed, displayed or
  printed, so access control and training must sit on top (defence in depth). Disk encryption
  protects a stolen laptop, not a logged-in session; DB encryption protects against people who
  reach storage but not those who can log into the DB.
- Beyond login controls: **IRM** (limit read/copy/print/forward per document, with expiry and
  remote revoke), **DLP** (outbound content filter, preventive), **digital watermarks**
  (detective: find leaked copies), physical controls on printers/copiers (their memory holds
  documents), screen locks, privacy screens.
- **Disposal**: shred paper; wipe or physically destroy media; OS "delete" is not erasure.
- **Test data**: never give developers production personal data; mask it first (the book equates
  masking with tokenisation, which is now considered imprecise, see section 6).
- **Training** is called the single most important confidentiality control (reply-all, chat,
  leaving reports on desks, redaction that can be reversed in electronic files).
- Privacy framework used: **GAPP** (AICPA/CICA) with 10 principles: management, notice, choice &
  consent, collection (minimise), use & retention (keep only as long as needed, named owner),
  access (subject can view/correct/delete), disclosure to third parties (only to equally
  protective parties), security, quality (accuracy), monitoring & enforcement (complaints,
  dispute resolution).
- Breach economics: US state laws require notification after loss, usually **waived if the data
  was encrypted**, which makes encryption a cost control.
- Crypto primer: symmetric (fast, key-distribution problem) vs asymmetric (slow, solves key
  exchange, enables signatures); hashing (one-way, fixed length, any change alters the hash) as
  the integrity tool; digital signature = hash encrypted with signer's private key, giving
  integrity + non-repudiation; PKI/CAs vouch for public keys; key management (escrow,
  revocation on exit) is the weakest link; VPNs vs firewall inspection trade-off.

### 1.2 Current regimes (what a skill must know)

| Regime | Scope trigger | Breach notice | Key duties |
|---|---|---|---|
| **EU GDPR** (applies 25 May 2018) | Establishment in EU, or offering goods/services to / monitoring people in the EU (Art. 3(2)) - a UAE agency marketing to EU residents can be caught | Supervisory authority within **72 h** of awareness (Art. 33) unless unlikely to cause risk; data subjects without undue delay if high risk (Art. 34) | Lawful basis (Art. 6; consent is only one of six), special categories (Art. 9), privacy by design/default (Art. 25), RoPA (Art. 30), security (Art. 32), DPIA (Art. 35), DPO where required (Art. 37), processor contracts (Art. 28), rights answered within 1 month (+2 for complex), fines up to EUR 20m / 4% worldwide turnover |
| **UAE PDPL** - Federal Decree-Law 45/2021 | Processing in the UAE or of UAE residents' data; excludes government data, health and banking data under their own laws, and free-zone entities with their own DP law | Notify the UAE Data Office promptly on awareness of a breach that harms privacy; exact deadline was to come from the Executive Regulations **(VERIFY)** | Consent or listed lawful grounds, rights (access, correction, erasure, restriction, portability, objection to automated decisions), DPIA for high-risk processing, DPO in some cases, records of processing, transfers to "adequate" jurisdictions or via safeguards (Arts. 22-23). In force 2 Jan 2022; **Executive Regulations not issued as of last check, so penalties and timelines remain open (VERIFY current status)** |
| **DIFC DP Law No. 5 of 2020** | Entities in the DIFC free zone only | Commissioner "as soon as practicable" **(VERIFY wording)**; data subjects if high risk | GDPR-like; Regulation 10 on autonomous/AI systems (2023, VERIFY) ; DPO and annual assessment for some controllers |
| **ADGM DP Regulations 2021** | Entities in ADGM (Abu Dhabi) only | Commissioner within **72 h** **(VERIFY)** | GDPR-like; full application to existing entities from Feb 2023 **(VERIFY)** |
| **Philippines DPA** - RA 10173 (2012), IRR 2016 | Processing in PH or of PH citizens/residents | NPC Circular 16-03: NPC **and** affected data subjects within **72 h** of knowledge/reasonable belief | Sensitive personal information includes government-issued identifiers (passport, SSS, TIN), so passports are SPI; DPO mandatory; registration of DP systems for larger PICs (NPC Circular 2022-04, VERIFY thresholds); security measures circular (2023, VERIFY number). Relevant if staff or customers are in PH |
| **Saudi PDPL** (Royal Decree M/19, amended 2023) | Processing in KSA or of KSA residents' data abroad | SDAIA within **72 h**; data subjects without undue delay if harm likely | In force 14 Sep 2023, enforcement from **14 Sep 2024** after grace year; transfer regulations, registration on SDAIA platform for some controllers, DPO in some cases, fines up to SAR 5m (double for repeats) **(VERIFY amounts)** |
| **CCPA as amended by CPRA** (CA, USA) | For-profit doing business in CA above revenue threshold (inflation-indexed, about USD 26-27m, VERIFY) or 100k consumers or 50%+ revenue from selling/sharing | Separate breach statute (Civ. Code 1798.82); a fixed 30-day deadline for consumer notices from 2026 was enacted **(VERIFY)** | Rights to know, delete, correct, opt out of sale/sharing, limit sensitive PI; CPRA effective 1 Jan 2023; CPPA regulations on risk assessments, cybersecurity audits, ADMT phased in from 2026 **(VERIFY dates)** |

Retention law that limits erasure (UAE): VAT records 5 years (longer for real estate), Corporate
Tax records 7 years, commercial books 5 years **(VERIFY each)**. A "delete me" request does not
override a statutory retention duty: restrict and minimise instead, and explain the basis.

### 1.3 Cross-cutting privacy obligations as implementable controls
- **Data inventory / RoPA**: per model and field: purpose, lawful basis, category (ordinary,
  sensitive, ID document), source, recipients (airlines, GDS, visa portals, payment providers),
  transfer country, retention rule, owner. Keep it as data (a model or YAML) that a check can diff
  against the schema so new PII fields cannot appear unrecorded.
- **Minimisation**: collect passport data only for products that need it (visa, international
  ticketing), not for every lead. Make the field required per product type, not globally.
- **Retention**: rule = trigger event + period + action (anonymise / restrict / archive), with a
  legal-hold flag that suspends it. Run as a scheduled job with a dry-run report first.
- **Subject rights**: intake log with due date (GDPR 1 month; others vary), identity check,
  search across models, response pack export, and a decision record (fulfilled / refused with
  basis, e.g. tax retention).
- **Breach handling**: clock starts at awareness; runbook names who decides, who notifies which
  regulator (GDPR SA, UAE Data Office, NPC, SDAIA) and the template content (nature, categories,
  approximate numbers, likely consequences, measures). Keep a breach register even for
  non-notifiable incidents (GDPR Art. 33(5)).
- **Cross-border transfer**: list processors and hosting locations; for EU data use adequacy,
  SCCs (2021 set) or EU-US Data Privacy Framework (2023); for UAE/KSA follow local transfer rules.
- **DPIA**: required before high-risk processing (large-scale ID documents, biometrics such as
  fingerprint attendance, geolocation of staff, profiling). Template: description, necessity,
  risks to individuals, mitigations, residual risk sign-off.
- **Processor contracts** with every SaaS that receives PII (email, WhatsApp/CRM, payment link
  providers, backup storage).

### 1.4 ERP implementation (travel agency storing passports, Odoo 19)
- **Field-level access**: put `groups="module.group_pii_passport"` on passport number, expiry,
  date of birth, nationality, Emirates ID, visa numbers. Non-members get no read via ORM, views,
  export or RPC. Caveats: `sudo()`, raw SQL, server actions and reports run as superuser bypass
  it; review every `sudo()` that returns these fields.
- **Separate the document**: store passport scans in a dedicated model or a binary field with
  `attachment=True` and the same `groups`, so the `ir.attachment` inherits the field restriction;
  do not attach scans to chatter, where any follower and every recipient of the record's email
  can see them. Set `public=False`; review `access_token` links shared with customers and their
  expiry.
- **Record rules** (`ir.rule`): agents see travellers on their own orders/teams; HR PII only for
  HR officers; multi-company isolation (`company_ids` domain) so one entity cannot read another's
  travellers.
- **Masking**: display a computed `passport_masked` (e.g. last 3 characters) to general users;
  keep the real field restricted. Mask in PDFs and emails unless the document's purpose (visa
  application) needs the full value.
- **Do not track sensitive fields**: `tracking=True` writes old and new values into
  `mail.tracking.value`, readable by anyone who can read the chatter. Track a boolean
  "passport updated" instead, or keep a restricted audit model.
- **Read logging**: Odoo logs writes (tracking, `write_uid/write_date`) but not reads. For ID
  documents add an access-log model written when the restricted field is fetched in a dedicated
  "reveal" action, which also deters browsing.
- **Export restriction**: limit the export feature to a group (Odoo 17+ has an "allow export"
  group, `base.group_allow_export`, VERIFY name); field `groups` also block export of the field.
  Watch XML-RPC/JSON-RPC API keys: a user with API access can read anything their groups allow.
- **Encryption at rest**: Odoo has no native field encryption and community PostgreSQL has no
  TDE. Use encrypted volumes (LUKS / cloud disk encryption) for DB and filestore, encrypted
  backups (age/gpg/rclone crypt) with keys stored apart from the backups, and, for the highest
  class (passport numbers), optional application-level encryption with a key held outside the DB
  (env/KMS). Trade-off: encrypted fields cannot be searched or deduplicated without a keyed hash
  column.
- **Non-production copies**: run `odoo-bin neutralize` (disables mail servers, crons, payment
  providers) plus a masking script that replaces names, emails, phones, passport numbers with
  format-valid fakes before a copy leaves production.
- **Retention / anonymisation job**: `ir.cron` that, N months after the last travel date and with
  no legal hold, blanks or pseudonymises passport fields and removes scan attachments, writing a
  log row per record. Default to dry-run; actual erasure only after the data owner approves the
  run. Odoo's `privacy_lookup` module helps locate a person across models for subject requests.
- **Consent / marketing**: blacklist (`mail.blacklist`) and opt-out handling for mass mailing;
  separate service messages from marketing.
- **Automated checks**: test that a user without the PII group gets `AccessError` reading the
  passport field via ORM and via `export_data`; scan models for fields whose names match PII
  patterns (`passport|emirates_id|dob|iban|national_id`) and fail CI if they lack `groups` or are
  tracked.

---

## 2. Processing integrity

Book frame (ch. 10, COBIT 5 DSS06): reliable output is **accurate, complete, timely, valid**.
Controls sit at input, processing, output. In a modern ERP most "batch" controls become
database constraints, posting rules and reconciliation reports; online entry replaces batches.

### 2.1 Input controls

| Control (book meaning) | ERP implementation | Odoo 19 specifics | Automated test |
|---|---|---|---|
| **Field check** (right data type) | Typed fields, input masks | Field types enforce type; add regex in `@api.constrains` for formats (passport, phone E.164, TRN 15 digits) | Create with bad format -> `ValidationError` |
| **Sign check** | Quantities/prices non-negative where business requires | `models.Constraint('CHECK(qty >= 0)', msg)` (Odoo 19 replaces `_sql_constraints`; VERIFY syntax in the dev skill) or `@api.constrains` | Insert negative qty -> error |
| **Limit check** | Fixed ceiling/floor (discount <= X%, agent cost >= product cost) | `@api.constrains`, or block in `action_confirm`; approvals for overrides via a group | Values at limit pass, limit+1 fails, approver can override |
| **Range check** | Value between bounds (travel date >= order date, <= +18 months) | Same; dates compared in user tz carefully | Boundary tests both ends |
| **Size check** | Length limits | `fields.Char(size=...)` is not enforced in UI for all widgets; validate in constrains | Over-length -> error |
| **Completeness check** | Required data before an action | `required=True` for always; conditional required in `action_confirm` (e.g. passport required only for visa products) | Confirm without required data -> `UserError` |
| **Validity check** (exists in master) | Foreign keys to active master records | `Many2one` with `ondelete='restrict'`, domain `active=True`, `check_company=True` for cross-company | Reference archived/other-company record -> error |
| **Reasonableness test** (logical relation) | Cross-field logic (return after departure, refund <= amount paid) | `@api.constrains` on all involved fields; remember it only fires when a listed field is written | Inconsistent pair -> error; update unrelated field does not bypass |
| **Check digit** | Validate IDs that carry one | `base_iban` (mod-97), `base_vat` via python-stdnum, Luhn for card numbers, ICAO 9303 MRZ check digits (7-3-1 weights) for passport scans | Known-good and one-digit-changed values |
| **Sequence check / prenumbering** | Gapless, unique document numbers; report gaps | `sequence.mixin` on `account.move` gives unique `name` per journal; unique constraint on sequence; for custom docs use `ir.sequence` assigned at confirm, not at draft | Query for gaps and duplicates per journal/year; test two concurrent confirms get distinct numbers |
| **Duplicate check** | Same vendor ref, same payment, same booking PNR | Odoo flags duplicate vendor bill references per partner (warning, not a block, VERIFY behaviour); add unique index on (partner, ref) for bills if policy demands a block; PNR/ticket number unique per company | Second bill with same ref is flagged/blocked |
| **Closed-loop verification** | Show the looked-up name after a code is entered | Many2one display names, partner VAT shown on bill | UI test (tour) optional |
| **Prompting / transaction log** | Wizard steps; immutable log of who/when | `create_uid/date`, `write_uid/date`, chatter tracking on key fields, `mail.message` | Assert tracking value created on change of amount |
| **Cancel source documents** | Mark consumed inputs so they cannot be re-entered | State fields (`posted`, `paid`), `payment_state`, import IDs (`external id`) to stop double imports | Re-import same file -> no duplicates |

### 2.2 Processing controls

| Control | ERP implementation | Odoo 19 specifics | Automated test |
|---|---|---|---|
| **Data matching / three-way match** | Pay only when PO, receipt and bill agree | Product "control policy" (ordered vs received quantities) drives billable qty; enterprise `account_3way_match` sets a release-to-pay status on bills; for services (tickets, hotels) the "receipt" is supplier confirmation, so match against the sale line instead | Bill qty > received -> bill not "to pay"; payment proposal excludes it |
| **Payment matching / reconciliation** | Every bank line reconciled to an invoice/bill or explained | Bank reconciliation widget, reconciliation models (rules), `account.partial.reconcile`; unreconciled suspense account must trend to zero | Count bank lines unreconciled > N days; suspense balance = 0 at period end |
| **Batch / financial totals** | Imported bank or GDS files carry totals; compare to processed | Import wizard computes sum of lines and compares to statement balance (`balance_start + sum = balance_end_real`) | Statement with mismatched end balance cannot be validated |
| **Hash total** (sum of non-money field) | Sum of ticket numbers or quantities in an interface file | Custom import: compute and store file-level control totals and record count in an import log | Import log totals equal sum of created records |
| **Record count** | Lines in file = records created + rejected | Same import log; rejected rows go to an error log, never silently skipped | Feed file with one bad row; assert counts reconcile |
| **Cross-footing / zero-balance** | Clearing accounts net to zero; row and column totals agree | Every `account.move` must balance (core check); payroll, outstanding receipts/payments and transfer accounts should net to zero after matching | Period-end query: clearing-account balances = 0; trial balance debits = credits |
| **Inalterability of posted records** (book: write-protection, file labels) | Posted entries immutable; corrections by reversal only | Journal option to lock posted entries with a hash chain (`restrict_mode_hash_table`); Odoo 18+ secures entries via a "secure entries" step and lock dates including an irreversible hard lock date; "Data Inalterability Check" report recomputes the chain (VERIFY exact names/flow in 19) | Run integrity check in CI on a seeded DB; test that writing to a hashed posted move raises |
| **Lock dates** | Close periods | Company lock dates (fiscal, tax, sales, purchase, hard lock) | Posting into locked period -> error |
| **Concurrent update** | Prevent lost updates | PostgreSQL row locks / serialisation errors retried by Odoo; use `SELECT ... FOR UPDATE NOWAIT` for counters | Parallel confirm test does not duplicate sequence |
| **Recalculation** | Recompute totals independently | Stored computed fields; periodic job recomputes order totals from lines and compares | Diff report empty |

### 2.3 Output controls
- **User review**: control reports routed to owners (daily posted-entries summary, new vendors,
  bank detail changes, credit-limit overrides).
- **Sub-ledger to GL reconciliation**: aged receivable/payable totals = control account
  balances; inventory valuation = stock accounts; deferred revenue schedule = deferred account.
  Automate as a scheduled report that emails differences, not just totals.
- **External reconciliation**: bank statements, supplier statements (airline BSP/ARC or
  consolidator statements), payroll headcount vs HR employee count (ghost-employee test),
  physical/stock counts.
- **Distribution**: reports with PII only to authorised groups; PDF access via record rules.
- **Transmission integrity** (book: parity, checksums): today TLS for transport; file hashes
  (SHA-256) on interface files and backups; idempotency keys on webhooks so retries do not
  double-post payments.
- **Spreadsheet risk** (book: hard-coded constants, single-reviewer): move recurring
  spreadsheet logic into the ERP or into version-controlled scripts; parameters in config
  records, never literals in code (matches the book's commission-rate lesson in ch. 11, and the
  rule against hard-coding account codes).

### 2.4 Test pattern (Odoo)
```python
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged

@tagged('post_install', '-at_install')
class TestInputControls(TransactionCase):
    def test_agent_cost_limit(self):
        line = self._make_line(agent_cost=90, product_agent_cost=100)
        with self.assertRaises(ValidationError):
            line.action_confirm()
```
Rule: one positive, one negative and one boundary case per control; one test that the control
cannot be bypassed by writing a different field or by import.

---


