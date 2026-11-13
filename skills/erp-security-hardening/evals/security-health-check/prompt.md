---
tags: [skill-creator]
max_turns: 40
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Run a security health check of our Odoo setup: database <db-copy> on localhost (read-only, do not change anything), the config file <path-to-odoo.conf> and our custom addons at <path-to-custom-addons>. Write report.md with the top 10 fixes in priority order, each with exact steps (menu path or config line), and what standard it maps to. Never print passwords or secrets.
