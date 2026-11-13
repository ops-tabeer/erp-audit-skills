---
tags: [skill-creator]
max_turns: 40
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

We have a local copy of our Odoo 19 database called <db-copy> (PostgreSQL on localhost). I want a quick fraud screen of our branch cashier, login cashier@example.com, for cash manipulation between <start-date> and <end-date>. Work read-only — do not modify the database. Give me a short findings.md with the top suspicious patterns, specific entry numbers, a rough estimate split by how sure you are, and whether anyone else seems involved.
