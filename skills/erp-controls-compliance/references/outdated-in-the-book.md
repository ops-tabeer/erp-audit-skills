# What the 2014 book gets wrong today: outdated → current tables

> Adapted in our own words from Romney & Steinbart, *Accounting Information Systems* 13th ed. (2014), all chapters, and updated for 2026.
> Items marked **(VERIFY)** were not confirmed against a primary source when this was written: check before stating them as fact.
> `standards-current.md` (erp-controls-compliance skill) holds the confirmed versions of standards, laws and dates and wins on any conflict.
> Odoo names confirmed in Odoo 19 source: `account.lock_exception`, `account.move.checked`, `res.company.restrictive_audit_trail`,
> `hard_lock_date`, `account.journal.restrict_mode_hash_table`, `account.move.inalterable_hash`, `res.partner.bank.allow_out_payment` (tracked),
> `auth_totp.policy` = employee_required | all_required (module auth_totp_mail), `auth_passkey` (LGPL), `base.group_allow_export`,
> payment states draft/in_process/paid/canceled/rejected, `hr.version` (replaces contract fields in 19).

## 4. Outdated in the book -> current

| Book claim/practice (2014) | Current position | Confidence |
|---|---|---|
| ACFE 2010 report: ~5% revenue lost, >$2.9T global | ACFE still uses the ~5% estimate; 2024 report: ~1,900 cases, >$3.1B losses, median loss ~$145k, median duration ~12 months | (VERIFY exact figures; a 2026 edition may now be out) |
| Tips are the top detection method | Still true: ~43% of cases detected by tip (2024) | (VERIFY) |
| Misappropriation 17x more likely than reporting fraud | Asset misappropriation ~89% of cases, financial statement fraud ~5% but highest median loss | (VERIFY) |
| SAS No. 99 governs auditor fraud duties | Superseded by AU-C 240 (AICPA clarified standards); PCAOB AS 2401 for public companies; IAASB revised ISA 240 issued 2025 | (VERIFY ISA 240 effective date, ~periods from Dec 2026) |
| Treadway 1987 recommendations | COSO Internal Control Integrated Framework 2013 + COSO/ACFE Fraud Risk Management Guide (2nd ed. 2023) | fairly sure |
| Average breach cost $6.6M | IBM Cost of a Data Breach 2025: global avg ~$4.4M, US ~$10M | (VERIFY) |
| Median intrusion dwell time 416 days | Mandiant M-Trends: global median ~10-11 days (2024-25) | (VERIFY) |
| Human error causes 80% of security problems | Verizon DBIR: human element in roughly 60% of breaches | (VERIFY) |
| Computer fraud $70-125B/yr US; online crime > drug trade | FBI IC3 2024: ~$16.6B reported losses; BEC ~$2.8B; investment/crypto scams largest | (VERIFY) |
| Ransomware uncommon because payments are traceable | Wrong now: crypto made ransomware the dominant extortion model; double extortion standard | sure |
| Spot phishing/scareware by bad English | Obsolete: LLMs produce fluent, personalised lures | sure |
| "Use only one antivirus"; signature AV | EDR/XDR, behaviour-based detection, managed detection | sure |
| Destroy hard drives on disposal | NIST SP 800-88 sanitisation incl. cryptographic erase; SSDs need crypto-erase | (VERIFY current revision) |
| Kiting via cheque float | Check 21 (2004) image clearing and instant payment rails (FedNow 2023, UAE Aani) killed most float; risk moved to refund/chargeback and BNPL abuse | fairly sure |
| Zeus as the banking trojan to fear | Replaced by infostealers, loaders, initial-access brokers; ransomware-as-a-service affiliates | sure |
| Facebook/MySpace as "new fraud frontier" | Messaging apps (WhatsApp, Telegram), LinkedIn recruitment lures, deepfakes | sure |
| War dialing, Bluetooth snarfing, IE browser | Obsolete or retired (IE retired 2022) | sure |
| Microsoft "Patch Tuesday / zero-day Wednesday" | Patch Tuesday persists, but exploitation now days after any vendor advisory | sure |
| Password-cracking focus | Credential stuffing, infostealers, MFA-bypass dominate | sure |
| Software piracy ~43% of installs | BSA last reported ~37% (2018); SaaS licence compliance is the modern issue | (VERIFY) |
| US laws named: identity theft federal crime (1998), pretexting phone-records law (2007) | Still in force; add CFAA as narrowed by *Van Buren* (2021); SEC cyber disclosure rule (2023, 4-business-day 8-K); GDPR (2018); EU NIS2, DORA (2025); PCI DSS v4.0.1 (future-dated reqs mandatory Mar 2025) | fairly sure |
| Laws relevant to a UAE operation (book silent) | UAE Federal Decree-Law 34/2021 on cybercrimes; Federal Decree-Law 45/2021 PDPL; UAE AML law (Federal Decree-Law 20/2018, updated 2024) | (VERIFY current numbering) |
| Pattern-recognition software, Benford | Still valid; now continuous controls monitoring and ML anomaly detection inside ERPs | sure |
| ERP market: SAP, Oracle, Sage, Microsoft, Infor; $50-500M implementations | Cloud ERP (S/4HANA Cloud, Oracle Fusion, NetSuite, D365, Odoo); SoD tooling (SAP GRC/Access Control, Oracle Risk Management Cloud) | sure |

---


## 5. Outdated → current: specific claims in ch. 7-8

| # | Book claim (paraphrased) | Status | Current position |
|---|---|---|---|
| 1 | Users should change passwords at least every 90 days, sensitive users every 30. | OBSOLETE | NIST 800-63B: no periodic rotation. Change only on compromise. Screen against breached lists. |
| 2 | Strong passwords need mixed upper/lower/digits/symbols. | OBSOLETE | No composition rules. Length (passphrases ≥15 when single-factor) plus a blocklist. Allow password managers. |
| 3 | Long passphrases may be a better route; "it remains to be seen" whether users accept them. | Settled | Yes: long passphrases, password managers, and increasingly **passwordless passkeys**. |
| 4 | Smart card + PIN as the multifactor alternative. | UPDATE | Still valid (PIV/CAC). The mainstream is now FIDO2 security keys and passkeys. SMS OTP is restricted. |
| 5 | User ID + password is "multimodal" authentication. | WRONG/obsolete | A user ID is an identifier, not an authenticator. Count only secrets, possessions and inherence. |
| 6 | Restrict network access by comparing device MAC addresses to an allow-list. | OBSOLETE as a control | MACs are spoofable and randomised. Use 802.1X with certificates, MDM compliance and ZTNA. |
| 7 | Dial-up modems, RADIUS for dial-in, war dialing for rogue modems. | OBSOLETE | The rogue-access lesson now applies to shadow SaaS, unmanaged remote-access tools and rogue APs. RADIUS survives inside 802.1X Wi-Fi/VPN. |
| 8 | Use noninformative SSIDs; reduce AP power; special paint. | Mostly obsolete | WPA3-Enterprise, 802.1X, guest isolation and WIDS. Obscurity adds little. |
| 9 | Border router → firewall → DMZ → internal firewalls is the security architecture. | UPDATE | Zero trust and identity-aware access. The perimeter still exists, but identity and device posture are the primary controls. |
| 10 | IPSs are "relatively new" and still have problems. | OUTDATED | IPS is a mature commodity and part of NGFW/SSE. Detection has moved toward EDR/XDR and SIEM analytics. |
| 11 | WAFs block HTML "put" while allowing "get". | Terminology error | HTTP methods. Modern WAFs inspect against the OWASP risk classes and are often delivered by a CDN. |
| 12 | Antivirus plus a personal firewall on each endpoint is enough endpoint protection. | UPDATE | EDR/XDR with managed response, allow-listing, disk encryption and automated patching. |
| 13 | Test patches carefully; IPS buys time; patching is a corrective control. | UPDATE | Risk-based vulnerability management with SLAs (KEV within days). Automate patching for most systems; virtual patching as a stopgap. |
| 14 | Secunia online/offline scanners for PCs; DoD "CyberProtect" game; 2005 CSO article. | OBSOLETE references | Secunia PSI discontinued. Use OS update tools, CIS-CAT, and current vendor guidance. |
| 15 | Trust Services *Framework* with 5 *principles*, AICPA/CICA. | UPDATE | 2017 Trust Services *Criteria* (5 categories), points of focus revised 2022. CICA is now CPA Canada. |
| 16 | COBIT 5 with 37 processes is current. | OUTDATED | COBIT 2019, 40 objectives, design factors. |
| 17 | ERM is COSO's 2004 8-component cube. | OUTDATED | COSO ERM 2017: 5 components, 20 principles, tied to strategy and performance. |
| 18 | COSO IC 2013 with 17 principles. | STILL VALID | Current. |
| 19 | SOX is "the most important" law for business controls. | CONTEXT | Still applies to SEC registrants (404(b) only for accelerated filers). Elsewhere: local corporate governance codes, GDPR/PDPL, NIS2/DORA, and SEC cyber disclosure rules (2023). |
| 20 | Computer security officer reports to COO/CEO, independent of IS. | STILL VALID (principle) | Now titled CISO, with board-level oversight under CSF 2.0 Govern. |
| 21 | Separation of systems duties: librarian, operators, data control group, etc. | UPDATE | Mainframe-era roles. Today separate developer / reviewer / deployer (CI/CD with protected branches), platform admin / security admin / app admin, and IAM admin vs business user. |
| 22 | A separate test system via virtualisation fixes programmers working in production. | UPDATE | Still right. Today it is dev/staging/prod with CI/CD, IaC and anonymised production copies. Production data in test must be masked (ISO 27001 A.8.11). |
| 23 | Software validates caller ID by voice-print. | OUTDATED/risky | Voice deepfakes defeat voice biometrics. Use call-back to known numbers and out-of-band verification, especially for bank-detail changes. |
| 24 | Neural networks are the cutting edge of fraud detection. | UPDATE | ML/AI anomaly detection is mainstream, alongside rules-based continuous auditing (CAATs/analytics on full populations). Watch for model risk and explainability. |
| 25 | About a third of frauds are found by anonymous tips. | UPDATE | ACFE's recent *Occupational Fraud* reports put tips at roughly 40%+ and still the top detection method **(VERIFY latest edition figure)**. Hotlines must offer anonymity and protection against retaliation. |
| 26 | Holiday-season attacks rise because "lonely hackers" and students are idle. | Anecdotal | Attackers do time attacks for holidays and weekends, for operational reasons (low staffing). The control lesson (coverage during holidays) holds. |
| 27 | Laptops: lock to immovable objects; tracking software can remotely wipe. | UPDATE | MDM/UEM, full-disk encryption by default, and remote wipe. Cable locks are a minor point. |
| 28 | Biometric template theft is a lifelong problem because templates are centrally stored. | UPDATE | Still a valid risk for central biometric databases (e.g., attendance devices: protect them). Passkeys keep biometrics on the device. |
| 29 | Network printers' hard drives hold document images. | STILL VALID | Include MFPs in asset inventory, encryption and disposal (A.7.14 secure disposal). |
| 30 | Cloud: get the provider's SOC 2 Type 2. | STILL VALID + extend | Add the shared-responsibility matrix, CUEC mapping, subservice carve-outs, bridge letters, and the provider's ISO 27001/27017 certification. |
| 31 | Expected loss = impact x likelihood decides whether a control pays off. | STILL VALID (basic) | Add ranges and Monte Carlo (FAIR). Catastrophic and regulatory risks override pure economics, as the book itself notes. |
| 32 | Preventive controls are superior to detective. | NUANCE | Prevention is cheaper per event, but assume-breach thinking means detection and response capacity is mandatory, not optional. |
| 33 | Packets ~1.4 kB; files split into thousands of packets. | Fine as a teaching point | Ethernet MTU is usually 1500 bytes. Irrelevant to controls. |
| 34 | Security awareness is taught by memos and monthly workshops. | UPDATE | Short, role-based training plus phishing simulations and metrics such as report rate. Train finance staff specifically on BEC and bank-change fraud. |

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


