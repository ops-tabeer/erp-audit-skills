---
name: erp-fraud-forensics
description: Forensic audit of an ERP (Odoo 17-19 first, also SAP, Oracle, Dynamics 365, NetSuite) to find how cash or money was manipulated and who was involved. Use this whenever the user suspects or has caught an employee stealing, skimming, faking refunds, manipulating cash, padding payroll or vendor payments, back-dating or deleting entries, or asks to "audit a user", "investigate the cashier/accounts team", "find suspicious entries", "estimate the loss", "check if anyone else was involved", or wants an evidence workbook for HR, police or auditors, even if they don't say "forensic".
---

# ERP fraud forensics

Turn a suspicion ("we caught X manipulating cash") into evidence: how it was done, which entries,
how much, and who else was involved. The method targets the patterns that matter most in
practice: fabricated refund liabilities paid from the till at night, cash refunds against BNPL or bank
requests, back-dating, credit notes outside the refund workflow, and deleted entries.

## Ground rules

- **Read-only, local copy.** Work on a restored copy of the database. Every script opens a read-only
  connection. Never write, fix or delete anything in the ERP during an investigation: that destroys
  evidence and may breach the user's own rules. If the copy is old, say how old (latest `create_date`)
  and offer to give the user dump/restore commands. Don't connect to servers yourself.
- **Don't guess who.** If the user hasn't named the person, ask, or offer an evidence-based screen of all
  accounting users. Naming someone without evidence harms innocent people.
- **Flags are not proof.** Separate three tiers: *Proven* (provable from records alone: duplicate, fake
  reference, overpayment), *Probable* (cash only that person controlled, with no customer, receipt or second
  approver), and *To verify* (needs bank/Tabby statements or customer confirmation). Withdraw false positives
  explicitly and say why.
- **Sensitive output.** Reports name staff and customers. Keep them as local files and don't publish or
  upload them unless asked.

## Workflow

1. **Scope.** Who (login), which companies and tills, which period. Find the latest entry date in the copy.
   Ask what the user already knows (how they were caught), because it tells you where to start.
2. **Profile the user.** Security groups (admin rights are a finding in themselves), volumes by journal type,
   hour-of-day pattern in local time (Odoo stores UTC: add the offset, UAE +4, PH +8), and comparison with peers.
3. **Run the scan**:
   `python scripts/odoo_forensic_scan.py --db <copy> --out <dir> --login <user> --since <date> --tz-offset 4`
   (use the Odoo venv's python; libpq env vars for connection). It writes one CSV per test plus `SUMMARY.md`
   with a per-user roll-up. The tests and their meaning are in the summary. Read
   `references/fraud-schemes.md` for the schemes behind them.
4. **Trace every high flag to its source**, the step that turns indicators into proof:
   - For a cash-out: open the full journal lines, the liability it consumed, who created that liability
     and when, and whether the same order or customer was refunded elsewhere (search labels for the order
     number across all entries).
   - For a refund: the refund request (what the customer asked for, payable vs paid, every payment on it),
     and the customer's original payment channel.
   - For timing and edits: the change log (`mail_tracking_value`) shows resets, cancellations, date changes
     **and line-amount changes** (field `balance` on `account.move.line`, logged against the entry) with user
     and time. A deposit raised after posting (cash credited more without more cash reaching the bank) or a
     refund increased minutes after creation is a strong signal.
   - For gaps: neighbouring entries bracket when a deleted entry existed; backups or server logs show what it was.
   - Check opening balances: a "legacy" liability that never existed at go-live proves the liability was made up.
5. **Check for accomplices.** Who approved this person's items, who paid what this person approved, who
   reset their entries. Interaction alone isn't collusion: report it as "needs explanation", never as guilt.
   Clear people explicitly when the evidence supports it (for example, bank payouts with real transfer references).
6. **Estimate** in the three tiers, per currency (Philippines companies are PHP). Never add across currencies.
7. **Report.** Executive summary in chat, plus an Excel evidence workbook (load the xlsx skill). Use
   `references/report-structure.md` for the sheet layout and wording.

## Traps that produced wrong answers before

- **Entry names and refund numbers repeat across companies** (the same cash entry number, e.g. CSH1/2026/00023, or the same
  refund-request number can exist in several companies). Always join on database ids, or on name plus company.
- **Internal order numbers in vendor-bill references** make "duplicate bill" tests explode. Exclude refs
  equal to a sale or purchase order name.
- **Go-live opening-balance loads** dominate amount totals. Exclude or label them.
- **Transfer credits** (credit from a cancelled order moved to a new order of the same customer) look like
  short-booked cash. Check the credit note's source before flagging.
- **No bank statements in the ERP** means bank-side items can't be verified. Say so, and list them for
  matching against the statement.
- **Combine the scan with free exploration.** The scan covers known patterns. Also look at what the cash
  actually paid for (incentives or commissions to third parties with no partner or receipt, salary paid by the
  cashier to himself, money cycling through staff advances or salary cards). In testing, each approach found
  things the other missed.
- **Never hard-code account codes.** Identify accounts by `account_type` and by journal default accounts.

## References

- `references/fraud-schemes.md`: fraud theory, 17 ERP schemes with detection logic, worked example of a cashier with accounting-admin rights.
- `references/cycle-analytics.md`: more SQL test ideas per cycle (revenue, expenditure, payroll, GL, cash & treasury).
- `references/attack-techniques.md`: cyber and abuse techniques (BEC, bank-detail change, MFA fatigue, AI prompt injection) and their ERP controls.
- `references/other-erps.md`: where the same data lives in SAP, Oracle, Dynamics 365 and NetSuite.
- `references/report-structure.md`: evidence workbook layout and wording rules.
- For control fixes after the investigation, use the `erp-controls-compliance` and `erp-security-hardening` skills.
