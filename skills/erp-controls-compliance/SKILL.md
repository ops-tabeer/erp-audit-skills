---
name: erp-controls-compliance
description: Design, review and fix internal controls and regulatory compliance in Odoo and other ERPs (SAP, Oracle, Dynamics 365, NetSuite). It covers COSO 2013 / COSO ERM 2017 / COBIT 2019 / ISO 27001:2022 / SOC 2, segregation of duties, revenue, expenditure, payroll, GL and cash/treasury controls, refunds and payment-gateway (Tabby/Tamara) reconciliation, lock dates and audit trail, data privacy (UAE PDPL, Philippines DPA, GDPR), UAE and Philippines e-invoicing and record retention. Use it when building or reviewing a custom module that moves money or stores personal data, designing an approval or refund workflow, preparing for an audit, writing an internal-controls policy, or asking "is this compliant", "what controls do we need", "how do we stop this happening again", or "what is outdated in our process".
---

# ERP controls & compliance

Knowledge from a classic accounting-information-systems textbook (Romney & Steinbart 13e, 2014),
rewritten in our own words and **updated to November 2026** standards, mapped onto Odoo 19 and other
ERPs. Use it to decide which controls a process needs, and to build them into the system rather than
into a policy document nobody reads.

## How to approach a request

1. **Name the process and the risk.** For example: "cash refunds at a branch till: risk = cash taken out
   against fake or duplicate refunds". Risks come from the fraud triangle (pressure, opportunity,
   rationalisation). Controls remove opportunity.
2. **Pick controls in this order of strength:** preventive and automated in the system (blocks, server-side
   validation) → separation of duties → detective reports reviewed by someone independent → manual policy.
   Prefer one strong preventive control over several weak detective ones.
3. **Map to the platform.** For Odoo, read `references/odoo-dev-guardrails.md` before writing or reviewing
   code that touches money or personal data. For other ERPs, translate the same control to that system's
   native feature and say which.
4. **Check it is current.** Before citing a standard, law, date or threshold, check
   `references/standards-current.md`. It records what is confirmed and what is unsettled (for example,
   UAE PDPL executive regulations). Never present an unsettled item as fact, and never invent penalties.
5. **Make it testable.** Every control gets a test: an automated test in the module, a SQL exception
   report, or a scan check (`erp-fraud-forensics` / `erp-security-hardening` scripts).

## Core rules for money-moving features (summary of the guardrails)

- Approvals are enforced server-side, and the same person can't request, approve and pay.
- Refunds go back through the original channel, capped at the approved payable, paid once.
- Amounts and journals come from the upstream document, and changing them needs a reason.
- Nothing financial is deleted: reverse, cancel or archive. Restrictive audit trail on, hash-secured
  journals, gap-free sequences.
- Periods lock monthly, with the hard lock after audit. Back-dating needs a reason.
- Manual journals to cash, refund or deposit liabilities are restricted, need a partner and an attachment.
- No hard-coded account codes: use account types or per-company settings.
- Personal identity data sits behind a group, is never public, is never in chatter, and is anonymised at end of retention.

## References (read what the task needs)

| File | Use it for |
|---|---|
| `references/standards-current.md` | Current versions of frameworks, NIST 800-63B-4, PCI DSS 4.0.1, OWASP 2025, ISA 240 (Revised), ACFE 2026, UAE/PH e-invoicing, retention, PDPL status. **Wins on conflicts.** |
| `references/odoo-dev-guardrails.md` | Building or reviewing custom Odoo modules; PR checklist; required tests |
| `references/frameworks-and-controls.md` | COSO/COBIT/ISO mapping, control-activity catalogue with Odoo patterns, 20-row SoD conflict matrix with compensating controls |
| `references/cycle-controls.md` | Threats → controls per cycle (revenue, expenditure, payroll, GL, cash & treasury, gateways/BNPL), with Odoo implementation |
| `references/privacy-and-integrity.md` | Privacy regimes, passport/ID handling, input/processing/output controls |
| `references/audit-programme.md` | Risk-based ERP audit programme (planning, ITGC, application controls, analytics), DevOps change management |
| `references/outdated-in-the-book.md` | What the 2014 book teaches that is now wrong, and what replaced it |

Items marked **(VERIFY)** in the references weren't confirmed. Check the primary source before relying on them.

## Output

- For a design question: the control set as a table (risk → control → type → where in the ERP → test),
  then the implementation steps.
- For a code review: findings against the guardrails checklist, with file:line references.
- For a policy or audit pack: write for the named audience, cite the standards row and its status, and
  list what is out of scope.
