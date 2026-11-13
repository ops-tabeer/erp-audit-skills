# Evidence workbook and report

## Chat summary (first)

1. One line: what was found, at what confidence.
2. How it was done: the mechanisms, each in one sentence a non-accountant understands.
3. Proven items table (entry, what it proves, amount).
4. Estimate in three tiers: Proven / Probable / To verify, per currency.
5. Others involved: named only with evidence, phrased as "needs to explain", and people cleared.
6. Next actions: freeze access, count cash, get slips, contact customers, bank matching.
7. Corrections to anything said earlier.

## Excel workbook (one sheet each)

| Sheet | Content |
|---|---|
| Summary | Scope, data source and cut-off, estimate table built with formulas (SUMIFS on the evidence sheets), method, others involved, links to sheets |
| Proven | # / entry / finding / amount / evidence / see-sheet; total with SUM |
| One sheet per mechanism | Every row with full context columns: dates, local time entered, user, customer, request vs paid, approver, attachments, change-log text, red-flag text. Amber = flagged, red = proven |
| Verify_* | Items that need an external statement, with yellow input columns (statement date, ref, amount, matched Y/N) |
| <Name>_Link | Cross-user interactions for interviews |
| AuditTrail | Odoo change log rows (reset, cancel, re-date) |
| JournalLines | Full debit/credit lines of every entry referenced, keyed by id so names from other companies don't leak in |
| NightActivity | Entries per hour vs peers, with share-at-night formula |
| DeletedEntries | Missing sequence numbers with neighbouring entries |
| AccessRights | The person's security groups |

Formatting: Arial 10, header fill, frozen header row, auto-filter, money format `#,##0.00`, dates
`dd-mmm-yyyy`, times shown in local time and labelled as such.

## Wording rules

- "Proven" only for what the records show by themselves. Otherwise "indicates", "consistent with", "needs explanation".
- Quote entry numbers exactly. Give company and currency where names repeat.
- Say what was **not** checked (e.g. no bank statements) and what would close the gap.
- Mention who prepared it, the data source and cut-off date, and that the analysis was read-only.
