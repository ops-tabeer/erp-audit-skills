# Running the same forensic tests on other ERPs

The tests in `scripts/odoo_forensic_scan.py` are concepts first and SQL second. The table below gives the
usual starting point in each ERP. Names are the common standard objects; customer systems often differ,
so confirm with the client's data dictionary and use **read-only** extracts or reporting replicas, never
production write access.

| Concept | Odoo 17-19 | SAP S/4HANA / ECC | Oracle EBS / Fusion | Dynamics 365 F&O | NetSuite |
|---|---|---|---|---|---|
| Journal header / lines | `account_move` / `account_move_line` | BKPF / BSEG (S/4: ACDOCA Universal Journal) | GL_JE_HEADERS / GL_JE_LINES (Fusion: same in GL) | GeneralJournalEntry / GeneralJournalAccountEntry | Transaction / TransactionLine (SuiteQL) |
| Who / when created | `create_uid`, `create_date` (UTC) | BKPF-USNAM, CPUDT/CPUTM | CREATED_BY, CREATION_DATE | CreatedBy, CreatedDateTime | createdby, createddate |
| Change log | `mail_message` + `mail_tracking_value` | CDHDR / CDPOS change documents; SM20 security audit log | FND audit / Fusion audit reports | Database log (SysDatabaseLog) | System Notes (SystemNote) |
| Payments | `account_payment` | REGUH / REGUP (payment run), BSAK/BSAD | AP_CHECKS_ALL, AP_INVOICE_PAYMENTS_ALL; AR_CASH_RECEIPTS_ALL | VendPaym journals, BankAccountTrans | Transaction type VendPymt / CustPymt / CustRfnd |
| Credit notes / refunds | `account_move` move_type out_refund | Billing doc type G2 / FI doc type DG | AR credit memos (RA_CUSTOMER_TRX_ALL, class CM) | CustInvoiceJour (credit) | CustCred / CustRfnd |
| Vendor bank details | `res_partner_bank` (+ tracking) | LFBK (+ CDHDR object KRED) | IBY_EXT_BANK_ACCOUNTS | VendBankAccount | Entity bank details (Vendor), system notes |
| Users and roles | `res_users`, `res_groups_users_rel` | USR02, AGR_USERS, AGR_1251 | FND_USER, FND_USER_RESP_GROUPS / Fusion roles | SecurityUserRole | Employee + Role records |
| Period locks | lock dates on `res_company`, `account_lock_exception` | OB52 posting periods (T001B) | GL_PERIOD_STATUSES | LedgerFiscalCalendarPeriod status | Accounting periods (locked/closed) |
| Number-range gaps | `sequence_prefix`/`sequence_number` | NRIV number ranges; BKPF-BELNR gaps per BUKRS/GJAHR/BLART | DOC_SEQUENCE_VALUE | NumberSequenceTable | tranid sequences |
| Built-in SoD tooling | none (use the controls check) | SAP GRC Access Control | Oracle Risk Management / AAC | Segregation of duties rules (System admin) | none built-in (SuiteApps) |

Tips:
- SAP: posting time in BKPF is server local time, not UTC. ACDOCA removes the BSEG split in S/4.
  Use document type (BLART) to tell manual journals (SA) from payment documents.
- Oracle: org_id (multi-org) is the equivalent of Odoo company_id, so always filter by it.
- Dynamics: voucher numbers repeat across legal entities (DataAreaId), the same trap as Odoo entry names
  repeating across companies.
- NetSuite: use SuiteQL through a read-only role, and System Notes give field-level history for most records.
