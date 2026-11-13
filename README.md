# ERP audit skills for Claude

Three [Claude skills](https://docs.claude.com/en/docs/claude-code/skills) that help you investigate fraud,
design internal controls and harden security in **Odoo 17-19**. They also give guidance for SAP S/4HANA,
Oracle, Dynamics 365 and NetSuite.

| Skill | Use it when you say… | What it brings |
|---|---|---|
| [`erp-fraud-forensics`](skills/erp-fraud-forensics/SKILL.md) | "audit this cashier", "find suspicious entries", "how much was taken, who else was involved" | Investigation workflow, a read-only Odoo scan with 14 tests (fabricated refund liabilities, cash refunds to the wrong channel, back-dating, amount edits after posting, deleted entries…), and an evidence-workbook layout |
| [`erp-controls-compliance`](skills/erp-controls-compliance/SKILL.md) | "design a refund workflow", "review this module", "is this compliant?" | Current standards and regulations (checked Nov 2026), guardrails for building money-moving Odoo modules, a segregation-of-duties matrix, and controls for each business cycle |
| [`erp-security-hardening`](skills/erp-security-hardening/SKILL.md) | "is our Odoo safe?", "who has admin rights?", "prepare for ISO 27001" | A read-only health check with 10 checks (2FA, admins, SoD, dormant/shared logins, audit trail, bank reconciliation, data exposure, `odoo.conf`, custom-code routes, DB role) and a hardening checklist |

## Install

Claude Code reads skills from `~/.claude/skills/` (for your user) or `.claude/skills/` (for one project):

```bash
git clone https://github.com/ops-tabeer/erp-audit-skills.git
mkdir -p ~/.claude/skills
cp -R erp-audit-skills/skills/* ~/.claude/skills/
```

Restart Claude Code. Each skill triggers automatically when a request matches its description, or you can
ask for it by name ("use the erp-fraud-forensics skill…").

The scripts need Python 3 and `psycopg2`. Odoo's own virtualenv already has it.

## Running the scripts directly

Both scripts open a **read-only** PostgreSQL connection and never write to the database. Run them against
a restored copy, not production.

```bash
# Fraud scan: one CSV per test plus SUMMARY.md with a per-user roll-up
python skills/erp-fraud-forensics/scripts/odoo_forensic_scan.py \
  --db my_odoo_copy --out ./scan --login cashier@example.com --since 2026-01-01 --tz-offset 4

# Controls & security check: CONTROLS_REPORT.md plus one CSV per check
python skills/erp-security-hardening/scripts/odoo_controls_check.py \
  --db my_odoo_copy --out ./controls --conf /path/to/odoo.conf --addons /path/to/custom_addons
```

The connection uses the usual libpq settings (`PGHOST`, `PGUSER`, `PGPASSWORD`…) unless you pass
`--host`, `--port`, `--user` or `--password`. Secret values from `odoo.conf` are never printed.

## Important notes

- **A flag is an indicator, not proof.** Every finding needs a person to trace it to source documents
  before anyone is accused. The forensic skill separates *proven*, *probable* and *to verify* amounts.
- **Not legal or tax advice.** `erp-controls-compliance/references/standards-current.md` records what was
  confirmed in November 2026 and marks unsettled items (for example, the UAE PDPL executive regulations).
  Check primary sources and your advisers before relying on a date, threshold or penalty.
- **Source material.** The control and fraud content is adapted, in our own words, from the ideas in
  Romney & Steinbart, *Accounting Information Systems* (13th ed., Pearson, 2014), then corrected and
  updated to current standards. No text from the book is reproduced. We aren't affiliated with the
  authors or publisher, and recommend the book itself.
- Account codes are never hard-coded. Accounts are identified by `account_type` and journal settings, so
  the scripts work with any chart of accounts.

## Layout

```
skills/
  erp-fraud-forensics/      SKILL.md, scripts/odoo_forensic_scan.py, references/, evals/
  erp-controls-compliance/  SKILL.md, references/, evals/
  erp-security-hardening/   SKILL.md, scripts/odoo_controls_check.py, references/, evals/
```

Each `evals/` folder holds a test case in the `claude plugin eval` format (a prompt plus graders). Run them
with `claude plugin eval skills/<skill> --allow-tools Write,Edit,Bash` after replacing the `<placeholders>`
in `prompt.md`.

## Contributing

Open a pull request against a feature branch. For new detection tests, include the reasoning (what fraud
pattern it catches) and keep everything read-only.

## Licence

MIT, see [LICENSE](LICENSE).
