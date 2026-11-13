# Current standards, laws and dates (checked November 2026)

This file overrides anything older in the other references. The book (Romney & Steinbart 13e, 2014)
predates most of these. Each row says what the book taught, what is current, and how sure we are.
"Confirmed" means checked against the issuing body or several independent professional sources in
November 2026. "Unsettled" means sources disagree: say so to the user and point them to the primary
source rather than quoting a number.

## Control and audit frameworks

| Topic | Book (2014) | Current | Status |
|---|---|---|---|
| Internal control | COSO 2013 (5 components, 17 principles) | COSO Internal Control 2013 is still current | Confirmed |
| Enterprise risk | COSO ERM 2004 "cube" | COSO ERM 2017, *Integrating with Strategy and Performance* (5 components, 20 principles) | Confirmed |
| IT governance | COBIT 5 | COBIT 2019 (40 objectives, design factors, focus areas) | Confirmed |
| Info-security management | ISO 27001:2005 | ISO/IEC 27001:2022 + 27002:2022 (93 Annex A controls in 4 themes: organisational, people, physical, technological); transition from 2013 ended Oct 2025 | Confirmed |
| Cyber framework | none | NIST CSF 2.0 (Feb 2024) adds **Govern** to Identify/Protect/Detect/Respond/Recover | Confirmed |
| Controls catalogue | none | CIS Controls v8.1 (2024), Implementation Groups IG1-IG3; NIST SP 800-53 Rev 5 | Confirmed |
| Service-org reports | SAS 70 / SSAE 16 | SSAE 18 (SOC 1); SOC 2 on the 2017 Trust Services Criteria with revised points of focus (2022) | Confirmed |
| Internal audit | IIA IPPF, "three lines of defence" | IIA **Global Internal Audit Standards** (issued Jan 2024, effective 9 Jan 2025); IIA Three Lines Model (2020) | Confirmed |
| External audit – fraud | SAS 99 | **ISA 240 (Revised)**: issued July 2025, effective for periods beginning on or after **15 Dec 2026**; US: AU-C 240 / PCAOB AS 2401 | Confirmed |
| External audit – IT | implicit | ISA 315 (Revised 2019): risks from IT and IT general controls must be identified | Confirmed |
| Web app security | OWASP Top 10 (2010) | OWASP Top 10:2025 (final Jan 2026). A01 Broken Access Control, A02 Security Misconfiguration, A03 Software Supply Chain Failures; new: Mishandling of Exceptional Conditions; SSRF folded into A01 | Confirmed top 3; check exact order of the rest on owasp.org |
| Card data | PCI DSS 2.0 | PCI DSS **v4.0.1**; all future-dated requirements mandatory since 31 Mar 2025 (incl. 6.4.3 / 11.6.1 payment-page script control, MFA for all CDE access) | Confirmed |

## Identity and passwords

| Book | Current (NIST SP 800-63B-4, final July/Aug 2025) |
|---|---|
| Complex passwords, change every 30-90 days | **Length over complexity**; no composition rules; **no forced periodic change** (change on suspected compromise); screen against breached/common-password lists; allow paste and password managers |
| Passwords + maybe a token | MFA for every privileged and remote user; **phishing-resistant** authenticators (FIDO2/WebAuthn passkeys, PIV) are the top tier; SMS OTP is a restricted fallback |
| Minimum length | Sources disagree on the exact figure (8 with MFA / 15 password-only is the most cited reading): set **≥12** in Odoo and require 2FA, or **15** where an account is password-only. Check section 3.1.1.2 of the NIST text before quoting a number. |

## Fraud statistics (for context only, never as evidence)

- ACFE *Occupational Fraud 2026: A Report to the Nations*: 2,402 cases across 143 countries. Organisations lose an estimated **5% of revenue** a year. ACFE's own key findings give a **median loss of about USD 150,000**, with asset misappropriation in about 45% of cases. Tips remain the most common way fraud is detected, but no source confirmed the exact share, so don't quote a percentage.

## UAE

| Topic | Current | Status |
|---|---|---|
| **E-invoicing** (Ministerial Decision 244 of 2025 and related decisions) | Pilot / voluntary from **1 Jul 2026**. Businesses with revenue **≥ AED 50 m**: appoint an Accredited Service Provider (ASP) by **30 Oct 2026** (extended from 31 Jul), mandatory from **1 Jan 2027**. Under AED 50 m: mandatory **1 Jul 2027**. Government entities: **1 Oct 2027**. Peppol 5-corner model, PINT-AE data. Late ASP appointment or implementation: AED 5,000 per month (Cabinet Decision 106 of 2025). | Confirmed by several professional sources; one vendor (Sovos) gives conflicting SME dates, so check the MoF/FTA text |
| VAT / Tax Procedures | Federal Decree-Law 17 of 2025 amended the Tax Procedures Law (effective 1 Jan 2026); Executive Regulation amendments effective **1 Apr 2026** add **+2 years retention** where a refund claim is pending | Confirmed |
| Record retention | VAT records: generally **5 years** after the tax period (10 for real-estate records); Corporate Tax: **7 years** after the tax period. Treat 7 years as the safe default for accounting records, and never hard-delete accounting data. | Baseline periods unsettled across sources: say "at least 7 years; confirm with the tax adviser" |
| Data protection | Federal Decree-Law **45/2021 (PDPL)** is in force as law, but whether its Executive Regulations have been issued is **unsettled**. Some 2026 sources say they have not; others cite a 1 Jan 2027 deadline with conflicting instrument numbers. A new federal AI & data authority (2026) is expected to enforce it. Free zones have their own regimes: **DIFC DP Law 5 of 2020**, **ADGM DP Regulations 2021**. | Unsettled: design to GDPR-equivalent controls (lawful basis, minimisation, access control, 72-hour breach readiness) and check the UAE Data Office / Official Gazette |
| Cybercrime | Federal Decree-Law 34/2021 on Combatting Rumours and Cybercrimes | Confirmed (law); check articles before citing |
| Payroll | Wage Protection System (WPS) via MOHRE for mainland staff | Confirmed |

## Philippines

| Topic | Current | Status |
|---|---|---|
| E-invoicing (EOPT Act RA 11976; RR 11-2025, RR 26-2025, RMC 98-2026) | Mandatory **structured e-invoice issuance** for covered taxpayers (Large Taxpayers, e-commerce, CAS/CBA users) by **31 Dec 2026** (extended from 14 Mar 2026). Transmitting sales data to the BIR EIS is a separate obligation. | Confirmed by several sources; no further extension found as of Nov 2026 |
| Data privacy | Data Privacy Act 2012 (RA 10173) + IRR; NPC Circular 16-03 breach notice to NPC **and** data subjects within **72 hours** | Confirmed |
| Books of account | Computerised Accounting System (CAS) registration/acknowledgement with the BIR before the ERP is the official book | Confirmed in principle; check current RR |

## Saudi Arabia (if KSA entity is active)

- PDPL in force since 14 Sep 2023, with enforcement from Sep 2024. SDAIA breach notice within 72 hours. ZATCA e-invoicing (FATOORA) Phase 2 integration is running in waves.

## How to cite

When a user asks for a compliance statement, quote the row, its status, and the primary source to
confirm it. Never present an "unsettled" item as settled, and never invent a penalty figure.
