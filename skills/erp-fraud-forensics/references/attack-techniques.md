# Computer fraud and abuse techniques: status today and ERP controls

> Adapted in our own words from Romney & Steinbart, *Accounting Information Systems* 13th ed. (2014), ch. 6, and updated for 2026.
> Items marked **(VERIFY)** were not confirmed against a primary source when this was written: check before stating them as fact.
> `standards-current.md` (erp-controls-compliance skill) holds the confirmed versions of standards, laws and dates and wins on any conflict.
> Odoo names confirmed in Odoo 19 source: `account.lock_exception`, `account.move.checked`, `res.company.restrictive_audit_trail`,
> `hard_lock_date`, `account.journal.restrict_mode_hash_table`, `account.move.inalterable_hash`, `res.partner.bank.allow_out_payment` (tracked),
> `auth_totp.policy` = employee_required | all_required (module auth_totp_mail), `auth_passkey` (LGPL), `base.group_allow_export`,
> payment states draft/in_process/paid/canceled/rejected, `hr.version` (replaces contract fields in 19).

## 3. Attack and abuse techniques (ch06): status today and ERP-level controls

Legend: **SR** = still relevant, **EV** = evolved, **OB** = obsolete/marginal.

| Technique (book) | Status | Modern form / note | ERP-level control |
|---|---|---|---|
| Hacking via known flaws | SR | Exploitation of internet-facing apps, VPNs, ERP portals | Patch cadence for Odoo/OS/PostgreSQL; WAF; no public DB port; vuln scanning |
| Botnets / hijacking | EV | Residential-proxy botnets for credential stuffing, DDoS-for-hire | Rate limiting on /web/login, CAPTCHA, CDN DDoS protection |
| DoS / DDoS | SR | Larger, layer-7 | Reverse proxy/CDN, worker limits, health checks |
| Spam / dictionary harvesting | EV | Mailbox validation now via OSINT, not blank emails | SPF/DKIM/DMARC p=reject on company domains used by Odoo outgoing mail |
| Splogs, click fraud, web cramming | EV/OB | Ad fraud still exists; not ERP-relevant | Out of scope |
| Email / caller-ID / SMS spoofing | SR | Feeds BEC and vishing | DMARC; never act on contact data in the request; call-back to master-data number |
| IP / ARP / DNS spoofing, MITM | EV | TLS everywhere made classic MITM harder; now AiTM phishing proxies | HTTPS + HSTS; TLS to DB; DNSSEC/registrar lock |
| Zero-day | SR | Mass exploitation within hours of disclosure | Asset inventory, emergency patch path, staging |
| XSS | SR | Still common in custom widgets/QWeb `t-raw`/`Markup` misuse | Code review rule: no unescaped user content; CSP headers |
| Buffer overflow | EV | Rare in Python app layer; matters in native deps | Keep base image/libs patched |
| SQL injection | SR | Custom modules using `cr.execute` with string formatting | Ban f-string SQL; use `SQL()` wrapper (Odoo 17+) / params; review gate |
| Masquerading / shared login | SR | Shared accounts, logged-in unattended sessions | Named users, MFA, short session timeout, device log review (`res_device_log`) |
| Piggybacking (Wi-Fi, tailgating) | SR | Physical access to till/back office | Badge access, CCTV over cash points |
| Password cracking | EV | Offline cracking of leaked hashes; mostly replaced by stuffing/infostealers | MFA, strong hashing (Odoo uses passlib pbkdf2), breach-password checks |
| War dialing / phreaking | OB | Modems gone; VoIP toll fraud persists | PBX hardening if telephony integrated |
| War driving / evil twin | EV | Rogue AP still used in public places | Admin access only over VPN/ZTNA; no ERP admin from public Wi-Fi |
| Data diddling | SR | Core insider risk | Field tracking, post-lock immutability, approval on master-data edits |
| Data leakage / podslurping | EV | USB replaced by cloud sync, personal email, exports, screenshots | Restrict export rights, DLP, log large exports, watermark reports |
| Salami / round-down | EV | Custom-code or FX/rounding manipulation | Code review, rounding account monitoring |
| Economic espionage | SR | Customer lists, pricing, supplier terms | Least-privilege menus, record rules by team/company |
| Cyber-extortion | EV | Ransomware + data-leak extortion | See modern list |
| Cyber-bullying, sexting, misinformation | SR (HR) | Not ERP controls | HR policy |
| Internet auction / pump-and-dump | EV | Marketplace and crypto scams | Out of scope |
| Software piracy | EV | SaaS licence compliance; Odoo Enterprise licence use | Licence inventory |
| Social engineering (traits: compassion, greed, trust, urgency, sloth, vanity) | SR | Still the lead vector; AI makes lures fluent | Training + process controls that do not depend on judgement |
| Identity theft | SR | Synthetic identities, account takeover | KYC on high-value customers, refund to original method only |
| Pretexting / help-desk resets | SR | Help-desk social engineering for MFA reset | Out-of-band verification for password/MFA reset |
| Posing (fake business) | SR | Fake vendors, fake job sites | Vendor onboarding due diligence (licence, TRN, bank letter) |
| Phishing / spear-phishing | EV | AiTM kits, QR phishing, OAuth consent phishing | Phishing-resistant MFA (passkeys/FIDO2) |
| Vishing | EV | Deepfake voice | Call-back + dual approval on payments |
| Carding | SR | Card-testing via e-commerce/payment links | Velocity limits on payment links, 3DS, provider fraud tools |
| Pharming / typosquatting | SR | Lookalike domains for invoices and portals | Domain monitoring; register lookalikes |
| QR code replacement | SR | "Quishing" on printed invoices/payment stickers | Payment QR generated by system and verified; customers told official channels |
| Tabnapping | EV | Reverse tabnabbing via `target=_blank` | `rel="noopener"` on external links |
| Scavenging / shoulder surfing | SR | Printed reports, screen views | Clean desk, screen privacy, shred |
| Lebanese looping, skimming, chipping | EV | Card skimming at POS; chip/contactless reduced it | Certified terminals, tamper checks |
| Eavesdropping / packet sniffing | EV | Mostly defeated by TLS; risk on internal plain-text links | TLS internally (DB, SMTP) |
| Spyware / adware / keyloggers | EV | Infostealers harvesting browser sessions and saved passwords | EDR on finance PCs; no saved passwords in browsers |
| Scareware | EV | Tech-support scams | Training; remote-access tools blocked |
| Ransomware | EV (major) | See modern list; book under-rated it | Immutable offline backups, restore tests |
| Trojan horse / malicious module | SR | Malicious third-party Odoo apps, npm/PyPI packages | Vet modules; pin and hash dependencies |
| Time/logic bombs | SR | Insider code before departure | Change review, two-person merge, offboarding code audit |
| Trap/back doors | SR | Hidden admin users, debug routes, API keys | Periodic review of `res_users` (active, internal), API keys, `auth='none'` routes |
| Steganography | SR (niche) | Exfiltration channel | DLP; low ERP priority |
| Rootkits | EV | Server persistence | Host hardening, rebuild from image after compromise |
| Superzapping | SR | DB superuser, Odoo shell, server actions with code | Restrict DB/shell access; log `psql` sessions (pgaudit); no prod shell for finance staff |
| Virus / worm | EV | Commodity; worms now in ransomware lateral movement | EDR, segmentation |
| Bluesnarfing / bluebugging | OB | Patched in modern phones | Mobile device management for app users |

### 3b. Modern techniques the book lacks
| Technique | How it hits an ERP | ERP-level control |
|---|---|---|
| Ransomware + double/triple extortion | Encrypts DB and filestore; steals data first, threatens leak | Offline/immutable backups (filestore too); tested restore; segmented DB host; least-privilege service accounts; incident playbook |
| Business email compromise | Fake CEO/vendor email triggers payment or invoice redirect | Payment release needs a second approver; no payment to bank details received by email without call-back to master-data phone |
| Vendor bank-detail change fraud | Attacker or insider edits `res_partner_bank` before a run | Bank changes need second approver (`allow_out_payment` set by someone other than editor); cooling-off period; notify vendor at old contact |
| MFA fatigue / push bombing | Repeated pushes until user approves | Number matching or FIDO2; alert on many denied prompts |
| Session-token theft / AiTM phishing kits | Steals session cookie, bypasses MFA | Phishing-resistant MFA, short session lifetime, re-auth for payments/bank edits, device log anomaly review |
| Deepfake voice/video CEO fraud | "CFO" on a call orders urgent transfer | Rule: no payment authority over voice/video; out-of-band confirmation; code words |
| Supply-chain / dependency compromise | Malicious Odoo app, pip package, CI token | Pinned deps with hashes, vendor review, separate deploy key, SBOM |
| Credential stuffing | Reused passwords on /web/login or portal | MFA for internal users, rate limiting, breached-password check, alert on login bursts |
| Cloud misconfiguration | Public backups bucket, exposed DB manager, open PG port | `list_db=False`, strong `admin_passwd`, no public DB port, private backup storage, config scanning |
| API abuse | XML-RPC/JSON-2 API keys with admin rights, scripted mass export or writes | Dedicated low-privilege integration users, scoped keys, key rotation, monitor API volume per user |
| Insider exfiltration via SaaS | Exports to personal Drive/ChatGPT/WhatsApp | Restrict export group, log exports, DLP on endpoints, offboarding revokes sessions immediately |
| AI/LLM prompt injection against ERP-connected assistants | Text in an email, invoice PDF, partner note or chatter instructs the assistant to change bank details, approve, or leak data | Assistant runs as a low-privilege user; read-only by default; any write/payment needs human confirmation; treat ERP content as data; log tool calls |
| Infostealer malware | Steals browser-saved passwords/sessions from finance PCs | EDR; forbid saved passwords; session revocation on detection |
| Authorised push payment / instant payment scams | Irrevocable instant transfers leave no float to recall | Approval before release, not after; payee name check where the bank offers it |

---

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


