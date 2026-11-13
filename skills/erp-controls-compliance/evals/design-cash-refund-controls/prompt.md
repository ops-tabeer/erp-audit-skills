---
tags: [skill-creator]
max_turns: 40
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

We're adding a 'Pay refund in cash' button to our custom Odoo 19 refund-request module at <path-to-module>. Before we code it, write design.md: what controls this button must enforce, as a table of risk → control → where in Odoo → how we test it, plus the exact server-side checks the Python code should do. We're a travel agency in the UAE and the Philippines taking BNPL (Tabby, Tamara), card and cash. Don't modify any code.
