# IT audit approach, ERP audit programme and change management

> Adapted in our own words from Romney & Steinbart, *Accounting Information Systems* 13th ed. (2014), ch. 11 and 22, and updated for 2026.
> Items marked **(VERIFY)** were not confirmed against a primary source when this was written: check before stating them as fact.
> `standards-current.md` (erp-controls-compliance skill) holds the confirmed versions of standards, laws and dates and wins on any conflict.
> Odoo names confirmed in Odoo 19 source: `account.lock_exception`, `account.move.checked`, `res.company.restrictive_audit_trail`,
> `hard_lock_date`, `account.journal.restrict_mode_hash_table`, `account.move.inalterable_hash`, `res.partner.bank.allow_out_payment` (tracked),
> `auth_totp.policy` = employee_required | all_required (module auth_totp_mail), `auth_passkey` (LGPL), `base.group_allow_export`,
> payment states draft/in_process/paid/canceled/rejected, `hr.version` (replaces contract fields in 19).

## 4. IT audit

### 4.1 Book (ch. 11)
- Audit types: financial, information systems (internal control), operational, compliance,
  investigative. Stages: planning -> evidence -> evaluation -> reporting (+ follow-up).
- Audit risk = inherent x control x detection; plan most work where risk is highest.
- Evidence methods: observation, documentation review, interviews, questionnaires, physical
  examination, confirmation, reperformance, vouching, analytical review, sampling.
- **Risk-based approach**: threats -> controls -> systems review (designed and in place?) + tests
  of controls (operating?) -> evaluate weaknesses and compensating controls -> adjust
  substantive work.
- **Six IS audit objectives**: (1) overall security, (2) program development/acquisition
  authorised, (3) program changes authorised, (4) processing accurate/complete, (5) bad source
  data caught and handled, (6) data files accurate, complete, confidential.
- Change testing: **source code comparison** (keep an audited copy, diff later), **reprocessing**
  (rerun data with audited code), **parallel simulation** (auditor writes own logic; the chapter
  case finds a wrong commission rate this way, then a **scanning routine** locates the literal in
  code). Surprise testing so changes cannot be inserted and removed between audits.
- Processing tests: **test data** (valid/invalid transactions, all logic paths; risk of polluting
  live files), **concurrent audit techniques** with embedded audit modules: **ITF** (fictitious
  entity in live master files), **snapshot** (before/after images of tagged transactions),
  **SCARF** (log of transactions meeting audit criteria), **audit hooks** (real-time alerts),
  **CIS** (DBMS-level independent recomputation). Program logic tools: flowcharting, decision
  tables, scanning, mapping (unexecuted code), tracing.
- **Input controls matrix**: rows = fields, columns = edit checks; documents which controls cover
  each field.
- **CAATs / GAS** (ACL, IDEA): run on a copy of live data; query, stratify, sample, recompute,
  duplicate and gap tests, ratio/trend analytics; do not replace judgement.
- Operational audit: judge results (effectiveness, efficiency), not only policies.

### 4.2 Current standards
- **ISA 315 (Revised 2019)** (effective for periods beginning on/after 15 Dec 2021): auditor must
  understand the IT environment, identify **risks arising from IT** for controls relevant to the
  audit, and the **ITGCs** that address them, grouped as access management, program change,
  IT operations (and acquisition/development). Automated application controls are relied on
  only if supporting ITGCs are effective; a tested automated control can be benchmarked rather
  than retested each year if change controls are strong. Also covers IPE (information produced
  by the entity, e.g. ERP reports used as evidence must be tested for completeness/accuracy).
- **ISA 240** (fraud): IAASB approved a revised ISA 240 in 2025, effective for periods beginning
  on or after 15 Dec 2026 **(VERIFY approval and effective date)**; theme: more professional
  scepticism, technology-enabled procedures, journal-entry testing, communication of fraud
  matters. Journal-entry testing remains mandatory in practice (management override).
- **ISA 330** (responses), **ISA 500** (evidence; revision in progress, VERIFY), **ISA 520**
  (analytics), **ISA 530** (sampling) underpin the programme below.
- **IIA Global Internal Audit Standards** (issued Jan 2024, effective 9 Jan 2025): 5 domains, 15
  principles; replaces the IPPF 2017 standards; **Topical Requirements** (first: Cybersecurity,
  effective 2026, VERIFY date) become mandatory scope elements when the topic is in scope.
  Independence remains: internal audit can advise on control design but must not own controls.
- **ISACA ITAF, 4th ed. (2020)**: IS audit/assurance standards (general, performance, reporting)
  and guidelines; pairs with **COBIT 2019** (replaces COBIT 5 used by the book).
- Also relevant: AICPA **Trust Services Criteria** (2017, points of focus revised 2022) for SOC 2;
  ISO/IEC 27001:2022 Annex A for security controls; NIST CSF 2.0 (2024).

### 4.3 Modern equivalents of the book's techniques
- GAS -> SQL/Python (pandas, DuckDB) directly on a read replica or neutralised copy; commercial
  tools (Diligent/ACL, CaseWare IDEA) still exist.
- Embedded audit modules / SCARF / audit hooks -> **continuous control monitoring (CCM)**:
  scheduled queries or `ir.cron` jobs that write exceptions to a review queue and alert; DB
  triggers or logical-replication streams feeding a SIEM for high-risk tables.
- ITF in production -> generally avoid (fictitious entities in the ledger create reporting and
  fraud-cover risk); use a neutralised staging copy plus synthetic transactions, or a clearly
  flagged test company excluded from consolidation.
- Source code comparison -> git: compare deployed addon tree hash with the approved release tag;
  file-integrity monitoring on the server's addons path; signed tags.
- Parallel simulation / reprocessing -> independent recomputation scripts (e.g. recompute
  payroll, commissions, revenue recognition from source tables and diff).
- Mapping/tracing -> code coverage reports, SAST (Semgrep, Bandit), dependency scanning.
- **Process mining** (Celonis, PM4Py, Disco): build event logs from `mail.message`/tracking and
  state timestamps to reveal variants such as invoice-before-order, payment-before-approval,
  maverick buying, rework loops; compare to the intended process.

### 4.4 ERP audit programme template

**A. Planning**
1. Scope: entities/companies, modules (sales, purchase, accounting, payroll, HR, custom addons),
   integrations (payment links, GDS/airline, bank, biometric devices, CRM/WhatsApp).
2. Risk assessment: inherent risks (cash refunds, agent commissions, manual journals, multi-
   company transfers, FX), fraud brainstorm (ISA 240 / book's State Farm hook example), prior
   findings, materiality.
3. Inventory of key reports used as evidence (IPE) and key automated controls.
4. Data access agreement: read-only replica or neutralised copy; no auditor write access to prod.

**B. ITGC tests**
- *Access*: list users with admin/settings/accounting manager rights; compare to HR active
  staff (leavers still active?); review shared accounts, API keys, `base.group_system` members,
  portal users with internal rights; SoD conflicts (create vendor + approve bill + pay; create
  employee + run payroll; post journal + reconcile bank); password/2FA policy; superuser and
  `sudo` usage in custom code; DB-level roles (who can connect to PostgreSQL directly).
- *Change*: population = git merges to the production branch + deployment log + module
  upgrade log in the period; sample changes: ticket, review approval by someone other than the
  author, CI pass, test evidence, release approval, deploy by authorised person; compare the
  deployed tree to the tagged release; look for direct DB edits (rows with `write_uid` = admin or
  odd `write_date` times, SQL history), changes to `ir.rule`, `ir.model.access`, server actions,
  automated actions and email templates done in the UI (configuration changes are changes too).
- *Operations*: backup success logs, restore drill evidence, cron failures, incident tickets,
  patch levels, monitoring alerts, capacity.

**C. Application control tests** (test of one per control if automated and ITGCs effective)
- Reperform each key constraint in a staging copy (positive/negative/boundary).
- Posting controls: balanced entries, lock dates, hash integrity check, sequence gaps/dupes.
- Three-way match / release-to-pay; duplicate vendor reference; credit limits; approval flows
  (refunds, discounts, agent cost overrides); payroll recomputation for a sample.
- Interface controls: record counts and totals of imports, error queues cleared, idempotency.
- Master data change controls: bank account changes on partners (who, when, approved?), price
  and cost changes across company copies.

**D. Substantive analytics**
- Journal entries: manual entries, posted by unusual users, weekends/late night, round amounts,
  just below approval limits, to rarely used accounts, reversed soon after, posted after period
  end into closed periods (if lock bypassed), descriptions with keywords.
- Duplicates: same vendor+amount+date, same ref different vendor, same bank account on two
  vendors or on a vendor and an employee.
- Benford first-digit test on bills/expenses; gap tests on invoice and payment numbers.
- Revenue: sales confirmed without delivery/travel date, refunds exceeding receipts, credit notes
  after period end, revenue recognition schedule vs bookings.
- Payroll: employees without attendance, pay after termination, bank account shared.
- Recompute: AR/AP ageing totals vs GL, deferred revenue roll-forward, FX revaluation.

**E. Reporting**
- Finding format: condition, criteria, cause, effect (quantified), recommendation, owner, due
  date, management response; severity (deficiency / significant / material weakness).
- Follow-up: re-test closed findings; track overdue actions to the audit committee/owner.

---

## 5. Change management and implementation controls (ch. 22 updated)

### 5.1 Book (ch. 22, plus ch. 11 objectives 2 and 3)
- Program development steps: requirements, plan, code (standards, structured modules), test
  (unit, integration, interfaces), document, train, install, maintain. Defects found late cost
  far more; a sizable share of budget should go to testing. Most lifetime effort is maintenance.
- Controls designed in: validity, authorisation, accuracy, security, numerical control,
  availability, **maintainability** (only authorised, tested, documented changes), integrity,
  audit trail.
- Testing types: walk-throughs, processing test data (expected results defined in advance),
  **user acceptance tests** on copies of real data with user-set criteria. Purchased software
  must also be tested.
- Conversion: direct (cheap, risky), parallel (safe, costly), phase-in, pilot. Data conversion:
  choose files, cleanse, convert, **validate nothing was lost**, catch up transactions, monitor,
  document.
- Post-implementation review: goals, user satisfaction, benefits, costs, reliability,
  accuracy, controls, documentation.
- Change controls (ch. 11 Table 11-3): list components changed, management + user approval,
  testing incl. UAT, documentation, **separate dev/test/prod**, deployment by someone independent
  of programmers and users, logical access over production code.

### 5.2 Modern DevOps equivalents for an Odoo shop
- **Version control**: every custom addon in git; production runs only a tagged commit; no
  editing files on the server; record the deployed commit hash.
- **Branch protection**: no direct pushes to the release branch; PR required with at least one
  reviewer who is not the author; CI must pass; history not rewritten.
- **Code review checklist**: access rules for new models (`ir.model.access.csv`, record rules),
  `sudo()` justification, SQL injection (no string-formatted SQL), PII fields with `groups` and
  no tracking, no hard-coded IDs/account codes, migration script present when stored fields or
  data change, tests for new constraints.
- **Environments**: dev (synthetic data) -> staging (neutralised, masked copy of prod, same
  Odoo/PostgreSQL versions) -> prod. Developers do not hold production write access day to day.
- **CI**: install/upgrade the changed modules on a fresh DB and on a recent staging copy;
  `--test-enable --test-tags /module_name`; lint (pylint-odoo, ruff); fail on warnings that
  indicate broken views or access.
- **Migrations**: schema/data changes via `migrations/<version>/pre-|post-migrate.py` or
  `end-` scripts, version bump in `__manifest__.py`, idempotent and logged; dry-run on staging
  and compare record counts/totals before and after (the book's data-conversion validation).
- **No direct production DB edits**: corrections go through the application (reversal entries,
  wizards) or a reviewed, ticketed script run with logging; never `UPDATE account_move_line`
  on posted data (also breaks the inalterability hash).
- **Release approval**: change ticket with scope, risk, rollback plan, test evidence, business
  owner sign-off for user-visible or financial-logic changes; release window; pre-upgrade backup
  verified; post-deploy smoke test and monitoring.
- **Rollback / progressive delivery**: restore-from-snapshot plan, feature flags via
  `ir.config_parameter` or company settings, pilot in one company before all (book's pilot
  conversion, modernised).
- **Emergency change**: allowed to restore service, by a named small group, minimal scope,
  logged at the time, retrospective review and approval within a fixed period (e.g. 2 business
  days), then normal PR merged so git matches production.
- **Configuration as change**: UI changes to access rights, record rules, automated actions,
  server actions, email templates, sequences and lock dates are tracked (export to XML/data
  modules where practical, or a periodic config diff report).
- **SoD in the pipeline**: author != approver != deployer where staff allows; if one person must
  do all, compensate with post-deployment review by someone else and automatic deploy logs.
- **Post-implementation review** 2-6 weeks after major releases: did controls work, error
  rates, user issues, data reconciliation after migration.

---


## 6. Outdated -> current

| Book claim (2014) | Current position |
|---|---|
| SSL secures browser traffic and VPNs | SSL and TLS 1.0/1.1 are deprecated; use TLS 1.2 minimum, prefer 1.3 |
| DES given as an example symmetric cipher | DES/3DES retired; AES-GCM or ChaCha20-Poly1305 |
| Key length equals block size; keys of 256 to 1024+ bits make ciphertext stronger by reducing repeated blocks | Conflates block size, key size and cipher mode. AES has 128-bit blocks; symmetric keys 128/256 bits; RSA >= 2048 (3072 preferred) or ECC; repeated-block leakage is solved by modes (GCM), not key length. Post-quantum migration (NIST FIPS 203/204/205, 2024) is starting |
| RSA and PGP named as asymmetric "systems" | PGP is a protocol/tool using RSA/ECC; modern use: Ed25519/X25519, age, S/MIME |
| SHA-256 as hashing example | Still fine; MD5 and SHA-1 broken for integrity/signatures; passwords need slow hashes (argon2, bcrypt, PBKDF2) |
| Data masking is "also called tokenisation" | Different: masking irreversibly replaces values (test data); tokenisation substitutes a reversible token held in a vault (e.g. PCI card data); pseudonymisation is a GDPR term, still personal data |
| Archives seldom encrypted because keys may be lost | Encrypt archives and backups; manage keys with escrow/KMS and dual custody |
| Wipe media by repeated overwrite; incinerate | NIST SP 800-88 (clear/purge/destroy; Rev. 2 issued 2025, VERIFY); for SSDs and cloud use cryptographic erase; multi-pass overwrite is unreliable on flash |
| Thawte/VeriSign issue certs; check via Internet Explorer menus | Let's Encrypt/ACME automation; certificate lifetimes shrinking toward 47 days by 2029 (CA/B Forum, VERIFY); IE is dead |
| Highly sensitive data probably should not go to public cloud | Common and acceptable with shared-responsibility model, customer-managed keys, region pinning, contractual and transfer safeguards |
| VPN + firewall inspection trade-off is the main network model | Zero trust (NIST SP 800-207): identity- and device-based access, MFA everywhere, TLS inspection at managed proxies |
| US is opt-out, Europe is opt-in for collection | GDPR requires a lawful basis (consent is one of six, must be freely given, specific, withdrawable); many US states now have comprehensive privacy laws with opt-out of sale/targeted ads and opt-in for sensitive data |
| GAPP (AICPA/CICA) as the privacy framework | Replaced by AICPA/CPA Canada Privacy Management Framework (2020); privacy criteria in TSC 2017; ISO/IEC 27701 |
| Laws cited: Massachusetts 201 CMR 17, HIPAA, HITECH, GLBA, CAN-SPAM | Still in force but now secondary to GDPR, UAE PDPL, KSA PDPL, PH DPA, CCPA/CPRA for this business; CAN-SPAM opt-out still 10 business days; Massachusetts penalty figure in the book should not be relied on (VERIFY) |
| Breach notice cost avoided if data encrypted | Still a common safe harbour, but only if keys were not also compromised; GDPR still needs a breach register entry |
| Cookies are harmless text files; honour browser refusal | Cookie consent under ePrivacy/GDPR; tracking pixels, fingerprinting and SDKs are treated like cookies |
| Spam and identity theft framed as main privacy concerns | Plus ransomware/extortion, credential stuffing, business email compromise, data broker exposure, AI training on personal data |
| Parity bits and checksums as transmission controls | Handled by TCP/TLS (AEAD); application-level concern is idempotency, file hashes, message signing (HMAC webhooks) |
| Header/trailer labels, tapes, write-protect tabs | Object metadata, checksums, object lock/WORM, DB constraints and hash chains on posted entries |
| Weekly full + nightly incremental to DVD/tape, one copy off-site | Continuous WAL archiving + daily logical dumps; 3-2-1-1-0 with immutable copy; automated restore verification |
| RAID gives fault tolerance | Still true but RAID and replication are not backups (they copy deletions and ransomware) |
| Cold site / hot site contracts | Cloud DR, infrastructure as code, replicas in another region, tested runbooks; RTO measured in drills |
| Antivirus and patch management | EDR/XDR, vulnerability management with SLAs and KEV prioritisation, MFA, least privilege |
| Test DRP/BCP at least annually | Still valid; add ransomware tabletop and actual restore drills per release/month |
| COBIT 5 references (APO01.06, DSS01, DSS04, DSS05, DSS06) | COBIT 2019 (same domain codes largely retained); NIST CSF 2.0; ISO 22301 for BCM |
| Embedded audit modules, SCARF, CIS inside the DBMS | Continuous control monitoring via scheduled queries, triggers/CDC to SIEM, automated exception workflows |
| ITF: fictitious entities in live master files | Avoid in production ledgers; use synthetic transactions in staging or a flagged test company |
| Source code comparison program, flowcharting, mapping tools | git diffs and signed tags, deployed-tree hash checks, code coverage, SAST, dependency scanning |
| ACL and IDEA as the CAATs | Still exist (Diligent, CaseWare) but SQL/Python/BI and process mining dominate |
| Auditors should not help develop systems | IIA 2024 Standards allow advisory input on control design with safeguards; auditors must not own or operate controls |
| Audit risk model and ITGCs implicit | ISA 315 (Revised 2019) makes risks arising from IT and ITGCs (access, change, operations) explicit; revised ISA 240 (VERIFY effective date) |
| SDLC waterfall; direct vs parallel conversion | Agile/DevOps with CI/CD, feature flags, canary/pilot by company or branch; parallel run still used for payroll and GL cut-overs |
| Separate dev/test/prod, change by independent staff | Still core; implemented via branch protection, CI, deployment pipelines and access separation; small teams use compensating post-deploy review |
| Spreadsheet controls via multiple-person cell review | Reduce end-user computing; version control, locked inputs, reconciliation to ERP; formal EUC inventory |
| Store rates in reference cells, not hard-coded (spreadsheets, and the commission case) | Still exactly right; in ERP terms, configuration records not literals in code, and no hard-coded account codes |

