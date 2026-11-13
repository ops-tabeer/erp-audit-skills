# Information security baseline: still valid / update / obsolete, with ERP controls

> Adapted in our own words from Romney & Steinbart, *Accounting Information Systems* 13th ed. (2014), ch. 8 and 10, and updated for 2026.
> Items marked **(VERIFY)** were not confirmed against a primary source when this was written: check before stating them as fact.
> `standards-current.md` (erp-controls-compliance skill) holds the confirmed versions of standards, laws and dates and wins on any conflict.
> Odoo names confirmed in Odoo 19 source: `account.lock_exception`, `account.move.checked`, `res.company.restrictive_audit_trail`,
> `hard_lock_date`, `account.journal.restrict_mode_hash_table`, `account.move.inalterable_hash`, `res.partner.bank.allow_out_payment` (tracked),
> `auth_totp.policy` = employee_required | all_required (module auth_totp_mail), `auth_passkey` (LGPL), `base.group_allow_export`,
> payment states draft/in_process/paid/canceled/rejected, `hr.version` (replaces contract fields in 19).

## 4. Information security: STILL VALID / UPDATE / OBSOLETE

### 4.1 Concepts
- **STILL VALID**
  - Security underpins confidentiality, privacy, processing integrity and availability.
  - Security is a management and governance issue, not just a technical one.
  - The life cycle: assess, set policy, implement, monitor.
  - Defence in depth.
  - Preventive controls will eventually fail, so detection and response matter.
  - Insiders are a major threat.
  - Culture and tone at the top matter.
- **UPDATE: time-based model (P > D + C).** The idea is still useful. Today it is
  expressed as dwell time, **MTTD/MTTR** (mean time to detect / respond), and "assume
  breach". As the book admits, P can drop to zero when a zero-day appears. That is why
  modern programmes invest in detection, response and recovery (CSF Detect, Respond and
  Recover) and in limiting blast radius through segmentation and least privilege.
- **UPDATE: targeted-attack steps.** The book's six steps (recon, social engineering,
  scan/map, research, execute, cover tracks) are a simplified kill chain. Use **MITRE
  ATT&CK** tactics, which add credential access, lateral movement, exfiltration and
  impact (ransomware). Add today's dominant vectors:
  - phishing that captures credentials and MFA codes (adversary-in-the-middle);
  - business email compromise and invoice/bank-detail fraud, which hit SoD conflict #2
    directly;
  - exploitation of internet-facing apps and VPNs;
  - stolen session tokens;
  - supply-chain compromise of software, SaaS and MSPs;
  - deepfake voice and video for social engineering, which also undermines the book's
    voice-print caller check.

### 4.2 Authentication
- **OBSOLETE (book Focus 8-1):** forced change every 90 days (30 for sensitive users),
  mandatory mixed character types, and password-history-driven rotation.
- **CURRENT (NIST SP 800-63B; Rev 4 finalised 2025, VERIFY exact numbers):**
  - Length matters more than complexity. Minimum 15 characters when the password is the
    only factor, minimum 8 when it is used with MFA. Accept at least 64 characters, all
    printable and Unicode characters, and spaces.
  - **No composition rules** and **no periodic rotation**. Force a change only on
    evidence of compromise.
  - Screen new passwords against **breached, common and context-specific** lists.
  - Allow paste and password managers. No password hints or knowledge-based questions.
  - Rate-limit failed attempts rather than relying on hard lockouts that attackers can
    trigger to cause denial of service.
- **MFA:** required for all remote and privileged access, and in practice for all users
  of a finance system.
  - Prefer **phishing-resistant** factors: FIDO2/WebAuthn security keys and
    **passkeys** (synced or device-bound), or PKI smart cards.
  - TOTP apps are acceptable but phishable.
  - SMS and voice OTP are restricted, legacy options.
  - Push MFA needs number matching to resist fatigue attacks.
- **Book's "multimodal" examples:** user ID + password is not multi-anything, because a
  user ID is not a secret. Biometrics are now normally used to *unlock a local
  authenticator* (a passkey), not matched on a server. That removes most of the book's
  valid worry about central template storage.
- **Device authentication:** MAC allow-lists are obsolete because MACs are trivially
  spoofed and randomised. Use certificate-based device identity (802.1X / EAP-TLS) and
  MDM/UEM device-compliance checks.
- **Odoo 19 specifics:**
  - `auth_totp` provides TOTP 2FA per user.
  - Enforcement module `auth_totp_mail_enforce` / the *Enforce two-factor authentication*
    setting (employees or all) **(VERIFY name)**.
  - `auth_passkey` adds passkeys (added in 18) **(VERIFY in 19 community)**.
  - `auth_password_policy` sets a minimum length. Set it to at least 12-15. Core has no
    breached-password check, so use the IdP for that.
  - Login cooldown after failures.
  - SSO via `auth_oauth` (OIDC/OAuth2). SAML needs enterprise or a third-party module
    **(VERIFY)**.
  - Best pattern: SSO through an IdP (Entra ID, Google, Okta) that enforces
    phishing-resistant MFA and conditional access, and disable local passwords for
    employees.

### 4.3 Authorisation and identity
- **STILL VALID:**
  - Authentication (who you are) is separate from authorisation (what you may do).
  - Access control matrix and compatibility test.
  - Update rights on job change to avoid privilege creep.
  - Workflow-embedded authorisation is stronger than static rights; this is the book's
    BPM point.
  - Separate admin and daily accounts.
  - Change default passwords.
- **UPDATE:**
  - **Identity-centric security:** identity is the new perimeter. Centralise identities in
    an IdP. Automate joiner-mover-leaver from HR. Run **access reviews/recertification**
    at least quarterly for privileged access and twice a year for finance roles.
  - **RBAC plus ABAC:** in an ERP, roles plus record rules (company, branch, team).
  - **Privileged access management (PAM):** just-in-time and time-bound elevation; a
    password vault for shared and service accounts; session recording for production and
    database access; break-glass accounts sealed and alerted on use. For Odoo, treat
    `base.group_system`, the `admin` user, the master password, PostgreSQL superuser and
    the server's OS root as PAM-scope secrets.
  - **Service accounts and API keys:** inventory and scope them, set expiry, rotate.
    - Odoo `res.users.apikeys` are tied to a user and inherit that user's rights. Use a
      dedicated, least-privileged integration user per integration.
    - Odoo 19 introduces the JSON-2 external API with bearer API keys and deprecates
      XML-RPC/JSON-RPC (removal announced for a later version) **(VERIFY timeline)**.

### 4.4 Network and perimeter
- **UPDATE: perimeter model → zero trust (NIST SP 800-207).**
  - Never trust by network location. Authenticate and authorise every request using
    identity, device health and context.
  - Use micro-segmentation. Replace the VPN-into-flat-LAN model with ZTNA / identity-aware
    proxies.
  - The book's internal firewalls between departments are an early form of segmentation.
    The idea is valid; the tooling has changed.
- **STILL VALID:**
  - Layered filtering.
  - Web application firewall in front of web apps.
  - IPS/IDS concepts, signature vs anomaly detection.
  - A DMZ still exists conceptually for anything internet-facing.
- **Book error:** it refers to HTML "get"/"put" commands. These are **HTTP** methods.
- **OBSOLETE:** dial-up/RADIUS for modem users, war dialing for rogue modems, and
  noninformative SSIDs as a meaningful control.
- **UPDATE (wireless):**
  - Use WPA3-Enterprise (or WPA2-Enterprise with 802.1X/EAP-TLS) for corporate devices
    and an isolated guest network.
  - Rogue-AP detection through wireless IDS in the AP management platform.
  - The book's "rogue modem" lesson now applies to rogue cloud apps and shadow SaaS, and
    to unmanaged remote-access tools. Find these with CASB/SSE and DNS filtering.
- **For an Odoo host:**
  - Expose only 443 via a reverse proxy (nginx) with TLS. Keep Odoo's own ports internal.
  - No public PostgreSQL. SSH by key only, from restricted sources.
  - Rate limiting on `/web/login`.
  - Remember that other workloads on a shared VPS widen the attack surface. Isolate them
    with containers, separate users and firewall rules.

### 4.5 Endpoint and malware
- **UPDATE:** signature antivirus → **EDR/XDR**: behavioural detection, isolation and
  rollback, managed 24x7 by an MDR provider for small firms.
- **Endpoint policy:**
  - Application allow-listing where feasible.
  - Full-disk encryption (BitLocker/FileVault).
  - Automatic OS and browser updates.
  - Local admin rights removed (the book's two-account rule is now LAPS/JIT admin).
  - USB storage restricted (the book's parking-lot USB attack is still valid).
- **Mobile/BYOD (Focus 8-2):** the advice is still valid in substance. It is now delivered
  through MDM/UEM, app protection policies (containers), conditional access and remote
  wipe. Phone passcodes and biometrics replace "password per corporate policy".
- **Hardening:** still valid. Use CIS Benchmarks / DISA STIGs, configuration-management
  tooling, and drift detection (ISO 27001:2022 A.8.9). Secunia PSI, which the book
  recommends, was discontinued; use OS-native update management and vulnerability
  scanners.

### 4.6 Secure software (book: buffer overflow, SQL injection, XSS)
- **STILL VALID:** treat all input as untrusted. Build security into development (BAI03).
  Manage purchased-software risk (APO10).
- **UPDATE:**
  - OWASP Top 10 (2021; a 2025 edition was released **(VERIFY)**).
  - **OWASP API Security Top 10 (2023):** broken object-level authorisation, broken auth,
    excessive data exposure, missing rate limits, SSRF.
  - Secure SDLC: NIST SSDF SP 800-218.
  - Tooling: SAST/DAST, dependency scanning and SBOMs, signed builds.
  - ISO 27001:2022 A.8.28 secure coding.
- **Odoo specifics:**
  - Never build SQL with string formatting. Use the ORM or `SQL()` wrappers / parameters
    (`odoo.tools.SQL` in 17+).
  - Avoid `t-raw`/`Markup` on user data.
  - Check every `sudo()` in controllers.
  - Use `auth='user'` on routes and add CSRF checks on non-JSON POST.
  - Validate access in controllers with `check_access` (19) / `check_access_rights`
    (older) **(VERIFY API name)**.
  - Never trust record IDs that come from the client.
- **API security:**
  - Authenticate every call with OAuth2/OIDC or scoped API keys.
  - Enforce object-level authorisation and rate limits.
  - Validate input against a schema.
  - Log calls with the caller's identity.
  - Version and retire endpoints.
  - Verify webhook signatures (HMAC) and protect against replay. This applies to payment
    provider callbacks such as Tabby.

### 4.7 Encryption and key management (book defers detail to ch. 9)
- **CURRENT baseline:**
  - **AES-256** (AES-GCM) at rest.
  - **TLS 1.2 minimum, TLS 1.3 preferred**, with HSTS, on every external and internal
    hop. TLS 1.0/1.1 are deprecated (RFC 8996).
  - **Retire** DES, 3DES, RC4, MD5 and **SHA-1** for signatures. Use SHA-256 or better.
  - RSA ≥ 2048 (3072 for long-lived keys) or ECDSA/Ed25519.
  - Password storage with an adaptive hash: Argon2id, scrypt, bcrypt or PBKDF2 with high
    iterations. Odoo uses `passlib` pbkdf2-sha512.
- **Plan for post-quantum:** NIST FIPS 203/204/205 were published Aug 2024 (ML-KEM,
  ML-DSA, SLH-DSA). Keep a crypto inventory and aim for crypto-agility.
- **Key management:**
  - Keys live in a KMS or HSM (cloud KMS, or an HSM for payment keys), separate from the
    data they protect.
  - Rotation schedule; split knowledge or dual control for master keys.
  - Certificate inventory and automated renewal (ACME). Note the industry move to much
    shorter TLS certificate lifetimes **(VERIFY CA/B Forum schedule)**.
- **Secrets management:**
  - No secrets in Git, in the `odoo.conf` checked into the repo, in `ir.config_parameter`
    readable by admins, or in tickets.
  - Use a vault (HashiCorp Vault, cloud secret manager) or root-only env files.
  - Scan repos for secrets (gitleaks, GitHub push protection).
  - Rotate on staff exit.
- **Backups:** encrypt them, and keep the decryption key somewhere other than with the
  backup.

### 4.8 Detection, logging and monitoring
- **STILL VALID:**
  - Logs only help if reviewed.
  - Review failed logins and failed access attempts.
  - Protect logs from modification ("audit the audit trail").
  - The book already mentions log normalisation and correlation tools.
- **UPDATE:**
  - **Central logging / SIEM** (or a managed SOC/MDR for small firms) collecting identity
    provider logs, ERP application logs, reverse-proxy logs, OS auth logs, EDR alerts and
    cloud audit logs.
  - Store logs in write-once / immutable form, with retention set by regulation (often
    1 year hot and longer cold).
  - Use detections mapped to ATT&CK, UEBA anomaly detection, and SOAR playbooks.
  - Time-sync everything (NTP), or correlation fails.
- **ERP-specific alerts:**
  - Vendor bank account change.
  - New admin or group-membership change.
  - Login from a new country (the book's "employee is badged in but logging in from
    abroad" idea).
  - Mass export of partner or employee data.
  - Posting into a locked period by exception.
  - Payments to new beneficiaries.
- **Vulnerability management cadence (current common practice; align to policy):**
  - Authenticated scanning at least monthly, plus continuous scanning for internet-facing
    assets.
  - Remediation SLAs: CISA KEV and actively exploited issues within days (BOD 22-01 sets
    2 weeks for federal agencies; many firms target 48-72 h for internet-facing systems);
    critical within 14-15 days; high within 30 days; medium within 90 days.
  - Penetration test yearly and after major change, plus web-app testing for custom code.
  - Book's view: patching is corrective, and an IPS can buy time while patches are
    tested. Today patching sits under vulnerability management. Virtual patching via WAF
    or IPS is still a valid stopgap.

### 4.9 Response and recovery
- **STILL VALID:**
  - Run a CIRT that includes business decision-makers.
  - Phases: recognition, containment, recovery, follow-up.
  - Use out-of-band communication, because VoIP fails along with the network.
  - Practise the plan.
  - Bring in forensics early if prosecution is possible.
- **UPDATE:**
  - Follow NIST SP 800-61 Rev 3 (2025, aligned to CSF 2.0) **(VERIFY)**.
  - Keep playbooks for ransomware, BEC and credential compromise.
  - Know your regulatory breach-notification clocks: GDPR 72 h; SEC Form 8-K Item 1.05
    within 4 business days of the materiality determination, for registrants; and local
    law.
  - Keep cyber insurance contacts and retainer incident-response firms ready.
  - Run tabletop exercises at least yearly.
- **CISO reporting:** the book says report to the COO or CEO, independent of IT. That is
  still the preferred independence, and CSF 2.0's Govern function now asks for board-level
  oversight. Reporting to the CIO is common but is an independence weakness.
- **Backups vs ransomware (book defers to ch. 10):**
  - **3-2-1-1-0 rule:** 3 copies, on 2 media types, with 1 off-site, 1 **immutable or
    offline** (object lock / WORM / air-gapped), and **0** errors on verified restore
    tests.
  - Backup credentials must be separate from production admin credentials. Ransomware
    operators delete backups first.
  - A backup is not proven until it has been restored. Do quarterly restore drills
    covering the database and the filestore together. Odoo attachments live in the
    filestore, and a database-only backup loses evidence.
  - Define RPO and RTO per system.
  - Keep a prune or retention policy that cannot be shortened by one compromised
    account.

### 4.10 Cloud and virtualisation
- **STILL VALID:**
  - Cloud changes risk but does not remove the need for every control.
  - Authentication becomes the main barrier.
  - Obtain the provider's **SOC 2 Type 2**.
  - Use virtualisation to create a separate test environment (the book's fix for the
    case's programmers in production).
- **UPDATE:**
  - The **shared-responsibility model** applies.
    - In IaaS/VPS the customer owns the OS, patching, network rules, the app, identity and
      data.
    - In PaaS the provider owns the OS.
    - In SaaS (Odoo Online/Odoo.sh) the provider owns most of the stack, and the
      customer still owns users, roles, MFA, data, integrations and configuration.
  - Also review CSA STAR / CCM, ISO 27017/27018, and the provider's CUECs.
  - Cloud security posture management (CSPM) for misconfigurations.
  - Infrastructure as code with reviewed changes.
  - Tenant isolation is the provider's job; IAM misconfiguration is the customer's
    leading failure.

---


## 3. Availability

### 3.1 Book (ch. 10)
- Two goals: **minimise downtime** (preventive maintenance, fault tolerance e.g. RAID, data-centre
  design: fire suppression, HVAC, UPS, surge protection, physical access; trained operators;
  patching and antivirus) and **recover quickly** (backups, DRP, BCP).
- **RPO** = how much data you accept losing (drives backup frequency); **RTO** = how long you can
  run without the system (drives DR sophistication). Near-zero both -> real-time mirroring.
- Full vs incremental (changes since last backup, slower restore chain) vs differential (changes
  since last full, simpler restore). Keep on-site and off-site copies; encrypt and access-control
  backups like the original; **practise restores**.
- Archives are long-term records; the book says they are seldom encrypted because keys may be lost.
- DRP = restore IT (cold site, hot site, second data centre); BCP = restore the whole business
  (offices, people, phones). Document configuration changes; test at least annually; most plans
  fail their first test.
- Virtualisation shortens RTO; cloud gives redundancy but creates provider-failure and lock-in
  risk, so keep backups outside the provider.

### 3.2 Current practice
- **Ransomware changed the threat model**: attackers delete or encrypt reachable backups first.
  Hence **3-2-1-1-0**: 3 copies, 2 different media/services, 1 off-site, 1 **immutable or
  offline** (object lock / WORM, or air-gapped), **0** errors in verified restores.
- **Immutability**: S3 Object Lock (compliance mode), Backblaze B2 object lock, Azure immutable
  blobs. A sync to a consumer cloud drive with the same credentials as the server is off-site but
  not immutable: an attacker with root can delete it. Use append-only credentials from the server
  and a separate account to manage retention.
- **Encryption** of backups is now expected, with keys escrowed outside the backup system
  (password manager / KMS, two custodians). The book's "archives unencrypted" advice is obsolete.
- **HA vs DR**: replication (streaming replica, multi-AZ managed PostgreSQL) covers hardware
  failure but faithfully replicates corruption and deletes; only point-in-time backups cover
  those.
- **Patching**: risk-based SLAs (critical internet-facing within days), track OS, PostgreSQL,
  Python deps, Odoo source updates, nginx/TLS; CISA KEV list as a priority feed.
- **DR runbook** contents: contacts and decision rights, RTO/RPO per system, restore order, exact
  commands, DNS/TLS steps, secrets location, validation checklist, comms templates, last test
  date and result.
- **Shared hosts**: other workloads on the same server (containers, other apps) share failure
  and compromise domains; include them in capacity and blast-radius analysis.

### 3.3 Odoo specifics
- A backup is **database + filestore** (`data_dir/filestore/<db>`), taken consistently: the DB
  references attachments by checksum path; restoring one without the other gives missing
  attachments.
- **pg_dump** (logical, `-Fc`): portable, per-DB, good for daily/offsite and version upgrades;
  RPO = interval between dumps; restore time grows with size.
- **PITR**: base backup (`pg_basebackup`) + continuous **WAL archiving** via pgBackRest, WAL-G or
  Barman; RPO of minutes, recovery to a timestamp just before a bad change or attack. Filestore
  needs its own frequent snapshot/sync (filestore is append-mostly, so rsync/rclone incrementals
  work).
- Odoo's web database manager (`/web/database/backup`) produces dump+filestore zips; on
  production set `list_db = False`, a strong `admin_passwd`, and block `/web/database/*` at the
  proxy so it is not an exfiltration or drop-database route.
- **Retention**: e.g. 14 daily, 8 weekly, 12 monthly, plus pre-upgrade snapshots; prune only by
  explicit pattern on the backup set itself and log what was pruned.
- **Restore drill** (monthly or per release): restore latest offsite copy to an isolated host,
  `odoo-bin neutralize`, start Odoo, then verify: row counts of key tables vs production at
  backup time, latest posted entry date, attachment sample opens, hash integrity report passes,
  trial balance equals the production figure. Record actual RTO achieved and the RPO gap.
- Monitor: backup job success, size delta (sudden drop = failure, sudden jump = something odd),
  age of newest offsite copy, WAL archive lag.

---


## 6. Quick checklist a skill can run against an Odoo 19 finance deployment

1. **MFA:** enforced for all internal users (TOTP, passkey or IdP SSO). Admins use
   phishing-resistant factors.
2. **Password policy:** minimum length ≥12-15 in `auth_password_policy`. No forced rotation
   configured in custom code.
3. **Privileged groups:** `base.group_system` and `base.group_erp_manager` held by named
   users only. None of them also holds daily finance posting rights. The `admin` user's
   password is vaulted.
4. **Audit trail** setting on. Posted-entry deletion blocked. Hash/secure-entries run on
   sales journals. Sequence gap report is clean.
5. **Lock dates:** set monthly. Hard lock after the annual close. Exceptions reviewed.
6. **Approval workflows:** PO double validation with a threshold. Refund and credit-note
   approval with requester ≠ approver enforced server-side. Manual JE review flag used.
7. **Vendor bank changes:** tracked. Trust flag restricted. Weekly review report.
8. **Payroll:** HR master data and payroll payment held by different users. Monthly
   variance review.
9. **SoD matrix** (section 3) run against effective groups per company. Accepted conflicts
   registered with compensating controls.
10. **Leavers:** users archived and API keys revoked on exit (no deletion). Quarterly
    access recertification.
11. **Code and config changes:** PR review, no direct pushes to main, server actions with
    code restricted, production view/action edits reconciled to tickets.
12. **Server:** `list_db=False`, strong master password, TLS 1.2+ at the proxy, no public
    PostgreSQL, logs shipped off-box, patch SLA met.
13. **Backups:** database + filestore, encrypted, one immutable/offline copy, a restore test
    within the last quarter, backup credentials separate from production.
14. **Integrations:** a dedicated least-privilege user per API key, webhook signature checks,
    secrets outside Git and outside admin-readable parameters.
15. **Evidence:** attachments on the record (invoice PDF, approval email, bank-change
    confirmation) so an auditor can trace each one from the transaction.

