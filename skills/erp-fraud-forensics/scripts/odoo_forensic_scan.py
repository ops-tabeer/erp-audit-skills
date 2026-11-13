#!/usr/bin/env python3
"""Read-only forensic scan of an Odoo (17/18/19) PostgreSQL database.

Runs transaction-level fraud tests (cash refunds, manual cash-outs, fabricated
liabilities, back-dating, resets, sequence gaps, refund channel mismatch,
self-service refunds, vendor bank changes, duplicate bills, payments to staff)
and writes one CSV per test plus a Markdown summary with a per-user roll-up.

Safety: the connection is opened READ ONLY. Nothing is written to the database.
Account codes are never hard-coded; accounts are identified by account_type and
by the default accounts of cash / bank journals.

Usage:
  python odoo_forensic_scan.py --db mydb --out ./scan [--login user@x.com]
      [--company "Branch name"] [--since 2025-11-01] [--tz-offset 4]
      [--night-start 22 --night-end 7] [--backdate-days 3]
Connection uses libpq defaults (PGHOST, PGUSER, PGPASSWORD...) unless --host etc. given.
"""
import argparse
import csv
import datetime as dt
import os
import sys

try:
    import psycopg2
except ImportError:  # pragma: no cover
    sys.exit("psycopg2 is required (pip install psycopg2-binary, or use the Odoo venv's python)")


# --------------------------------------------------------------------------- setup
def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--db", required=True)
    p.add_argument("--host")
    p.add_argument("--port")
    p.add_argument("--user")
    p.add_argument("--password", help="prefer PGPASSWORD env var")
    p.add_argument("--out", required=True, help="output directory (created)")
    p.add_argument("--login", help="focus on one user login (others still shown in roll-up)")
    p.add_argument("--company", help="substring of company name to restrict to")
    p.add_argument("--since", default=None, help="accounting date from (YYYY-MM-DD); default 13 months ago")
    p.add_argument("--tz-offset", type=float, default=4.0, help="hours to add to UTC create_date for local time (UAE=4, PH=8)")
    p.add_argument("--night-start", type=int, default=22)
    p.add_argument("--night-end", type=int, default=7)
    p.add_argument("--backdate-days", type=int, default=3, help="flag entries created more than N days after their date")
    p.add_argument("--max-rows", type=int, default=5000, help="cap rows per CSV")
    return p.parse_args()


class DB:
    def __init__(self, a):
        kw = {"dbname": a.db}
        for k in ("host", "port", "user", "password"):
            if getattr(a, k):
                kw[k] = getattr(a, k)
        self.conn = psycopg2.connect(**kw)
        self.conn.set_session(readonly=True, autocommit=True)
        self.cur = self.conn.cursor()

    def q(self, sql, params=None):
        self.cur.execute(sql, params or {})
        cols = [d[0] for d in self.cur.description]
        return cols, self.cur.fetchall()

    def has_table(self, t):
        return self.q("select to_regclass(%(t)s) is not null", {"t": t})[1][0][0]

    def has_col(self, t, c):
        return self.q("select count(*) from information_schema.columns where table_name=%(t)s and column_name=%(c)s",
                      {"t": t, "c": c})[1][0][0] > 0


# --------------------------------------------------------------------------- helpers
def build_ctx(db, a):
    ctx = {}
    # account code expression (Odoo 18+: code_store jsonb per company; <=17: code column)
    if db.has_col("account_account", "code_store"):
        ctx["acode"] = "coalesce(a.code_store->>(l.company_id::text), '')"
    else:
        ctx["acode"] = "a.code"
    ctx["aname"] = "(a.name->>'en_US')" if db.has_col("account_account", "name") and \
        db.q("select data_type from information_schema.columns where table_name='account_account' and column_name='name'")[1][0][0] == "jsonb" \
        else "a.name"
    ctx["origin_pay"] = "origin_payment_id" if db.has_col("account_move", "origin_payment_id") else "payment_id"
    ctx["memo"] = "memo" if db.has_col("account_payment", "memo") else "ref"
    ctx["pay_state"] = "ap.state" if db.has_col("account_payment", "state") else "pm.state"
    ctx["paid_states"] = "('paid','in_process','posted')"
    ctx["trk_field"] = "field_id" if db.has_col("mail_tracking_value", "field_id") else "field"
    since = a.since or (dt.date.today().replace(day=1) - dt.timedelta(days=395)).isoformat()
    ctx["since"] = since
    ctx["tz"] = f"interval '{a.tz_offset} hours'"
    ns, ne = a.night_start, a.night_end
    ctx["night"] = (f"(extract(hour from {{ts}} + interval '{a.tz_offset} hours') >= {ns} or "
                    f"extract(hour from {{ts}} + interval '{a.tz_offset} hours') < {ne})")
    # company filter
    if a.company:
        _, rows = db.q("select id from res_company where name ilike %(c)s", {"c": f"%{a.company}%"})
        ctx["company_ids"] = [r[0] for r in rows] or [-1]
    else:
        _, rows = db.q("select id from res_company")
        ctx["company_ids"] = [r[0] for r in rows]
    # till (cash journal) and bank accounts
    _, rows = db.q("""select j.default_account_id, j.type from account_journal j
                      where j.default_account_id is not null and j.type in ('cash','bank')""")
    ctx["till_accounts"] = [r[0] for r in rows if r[1] == "cash"] or [-1]
    ctx["bank_accounts"] = [r[0] for r in rows if r[1] == "bank"] or [-1]
    _, rows = db.q("select id from account_account where account_type='asset_cash'")
    ctx["cash_type_accounts"] = [r[0] for r in rows] or [-1]
    ctx["focus_uid"] = None
    if a.login:
        _, rows = db.q("select id from res_users where login=%(l)s", {"l": a.login})
        if not rows:
            sys.exit(f"login {a.login} not found")
        ctx["focus_uid"] = rows[0][0]
    return ctx


def P(ctx, **extra):
    d = {"since": ctx["since"], "cids": ctx["company_ids"], "tills": ctx["till_accounts"],
         "banks": ctx["bank_accounts"], "cashacc": ctx["cash_type_accounts"]}
    d.update(extra)
    return d


# --------------------------------------------------------------------------- checks
# Each check returns dict(key, title, why, severity, cols, rows, amount_col, user_col)
def chk_manual_cash_out(db, ctx):
    sql = f"""
    select m.name entry, m.date, (m.create_date + {ctx['tz']}) created_local, c.name company, u.login creator,
           round(cl.credit,2) cash_out, {ctx['acode'].replace('l.', 'o.')}||' '||{ctx['aname']} debit_account,
           coalesce(rp.name,'') partner_on_line, left(translate(coalesce(o.name,''), chr(10)||chr(9), '  '),160) label,
           (select count(*) from ir_attachment x where x.res_model='account.move' and x.res_id=m.id) attachments,
           {ctx['night'].format(ts='m.create_date')} night,
           ((m.create_date + {ctx['tz']})::date - m.date) lag_days
    from account_move_line cl
    join account_move m on m.id=cl.move_id
    join res_company c on c.id=m.company_id join res_users u on u.id=m.create_uid
    join account_move_line o on o.move_id=m.id and o.debit>0 and o.id<>cl.id
    join account_account a on a.id=o.account_id
    left join res_partner rp on rp.id=o.partner_id
    where m.state='posted' and m.move_type='entry' and m.{ctx['origin_pay']} is null
      and cl.account_id = any(%(tills)s) and cl.credit>0
      and o.account_id <> all(%(tills)s) and o.account_id <> all(%(banks)s) and o.account_id <> all(%(cashacc)s)
      and m.date >= %(since)s and m.company_id = any(%(cids)s)
      and __TYPE_FILTER__
    order by u.login, m.date"""
    hi = sql.replace("__TYPE_FILTER__", "a.account_type in ('liability_current','liability_payable','liability_non_current','asset_receivable','income','income_other')")
    cols, rows = db.q(hi, P(ctx))
    res = [dict(key="F01_manual_cash_out_refund_type", severity="HIGH",
                title="Cash taken out of a till by manual journal against refund/deposit/payable/receivable/revenue accounts",
                why="Refunds, deposit returns and payable settlements should be payments with a partner, an approved request and "
                    "evidence. A manual journal that credits the till against these accounts, often with no partner or attachment, "
                    "is how fabricated refunds are paid out.",
                cols=cols, rows=rows, amount_col="cash_out", user_col="creator")]
    lo = sql.replace("__TYPE_FILTER__", "a.account_type like 'expense%%' and (select count(*) from ir_attachment x where x.res_model='account.move' and x.res_id=m.id)=0 and cl.credit >= %(petty)s")
    cols, rows = db.q(lo, P(ctx, petty=500))
    res.append(dict(key="F01b_cash_expenses_no_receipt", severity="LOW",
                title="Expenses of 500 or more paid from a till with no receipt attached",
                why="Petty-cash expenses are normal; ones with no receipt attached cannot be checked. Sample them per user and month.",
                cols=cols, rows=rows, amount_col="cash_out", user_col="creator"))
    return res


def chk_fabricated_liability(db, ctx):
    # Manual JE: Dr revenue/contra-revenue/expense, Cr current liability without partner; then same creator pays
    # the same liability account from a till or bank with a matching amount within 60 days.
    sql = f"""
    with lia as (
      select m.id mid, m.name, m.date, m.create_date, m.create_uid, cl.account_id, cl.credit amt, m.company_id,
             left(translate(coalesce(cl.name,''), chr(10)||chr(9), '  '),140) label
      from account_move m join account_move_line cl on cl.move_id=m.id
      join account_account la on la.id=cl.account_id
      where m.state='posted' and m.move_type='entry' and m.{ctx['origin_pay']} is null
        and cl.credit>0 and cl.partner_id is null and la.account_type in ('liability_current','liability_payable')
        and exists (select 1 from account_move_line d join account_account da on da.id=d.account_id
                    where d.move_id=m.id and d.debit>0 and da.account_type in ('income','income_other','expense','expense_direct_cost'))
        and m.date >= %(since)s and m.company_id = any(%(cids)s)),
    pay as (
      select m.id mid, m.name, m.date, m.create_date, m.create_uid, dl.account_id, dl.debit amt
      from account_move m join account_move_line dl on dl.move_id=m.id
      where m.state='posted' and dl.debit>0
        and exists (select 1 from account_move_line x where x.move_id=m.id and x.credit>0
                    and (x.account_id = any(%(tills)s) or x.account_id = any(%(banks)s) or x.account_id = any(%(cashacc)s))))
    select lia.name liability_entry, lia.date liability_date, (lia.create_date + {ctx['tz']}) liability_created_local,
           uc.login creator, (select {ctx['acode'].replace('l.', 'lia.')}||' '||{ctx['aname']} from account_account a where a.id=lia.account_id) liability_account,
           round(lia.amt,2) amount, lia.label,
           pay.name payout_entry, pay.date payout_date, (pay.create_date + {ctx['tz']}) payout_created_local, up.login payout_by,
           round(pay.amt,2) payout_amount,
           (select count(*) from ir_attachment x where x.res_model='account.move' and x.res_id=lia.mid) liability_attachments
    from lia
    left join lateral (select * from pay where pay.account_id=lia.account_id and abs(pay.amt-lia.amt)<=1
                       and pay.date between lia.date and lia.date + 60 order by pay.date limit 1) pay on true
    join res_users uc on uc.id=lia.create_uid left join res_users up on up.id=pay.create_uid
    order by (pay.create_uid = lia.create_uid) desc nulls last, uc.login, lia.date"""
    cols, rows = db.q(sql, P(ctx))
    # keep the strong signal: paid out by the same person, or not paid at all is noise -> keep only matched
    ci, pi = cols.index("creator"), cols.index("payout_by")
    rows = [r for r in rows if r[cols.index("payout_entry")] and r[ci] == r[pi]]
    return dict(key="F02_liability_created_then_paid", severity="HIGH",
                title="Liability created by manual entry against revenue/expense (no partner) and paid out by the same user",
                why="Pattern of fabricated refunds: book a refund/security liability with no customer, then take the same amount "
                    "out of cash or bank. Strongest when the same user created and paid it, at night, with no attachment.",
                cols=cols, rows=rows, amount_col="payout_amount", user_col="payout_by")


def chk_cash_refunds(db, ctx):
    sql = f"""
    with inbound as (
      select ap.partner_id, ap.company_id,
             sum(case when j.type='cash' then ap.amount else 0 end) in_cash,
             sum(case when j.type<>'cash' then ap.amount else 0 end) in_noncash
      from account_payment ap join account_journal j on j.id=ap.journal_id
      where ap.payment_type='inbound' and {ctx['pay_state'].replace('pm.','ap.')} in {ctx['paid_states']}
      group by 1,2)
    select pm.name payment, ap.date, (pm.create_date + {ctx['tz']}) created_local, j.code journal, c.name company,
           u.login creator, rp.name partner, round(ap.amount,2) amount, left(coalesce(ap.{ctx['memo']},''),120) memo,
           round(coalesce(i.in_cash,0),2) partner_paid_cash, round(coalesce(i.in_noncash,0),2) partner_paid_noncash,
           case when coalesce(i.in_cash,0)=0 and coalesce(i.in_noncash,0)>0 then 'refunded in cash, customer only ever paid non-cash'
                when coalesce(i.in_cash,0)+coalesce(i.in_noncash,0)=0 then 'no inbound payment from this partner'
                when ap.amount > coalesce(i.in_cash,0)+coalesce(i.in_noncash,0)+1 then 'refund exceeds all payments received'
                else '' end channel_flag,
           {ctx['night'].format(ts='pm.create_date')} night,
           ((pm.create_date + {ctx['tz']})::date - ap.date) lag_days,
           (select count(*) from account_payment d where d.partner_id=ap.partner_id and d.id<>ap.id
              and d.payment_type='outbound' and abs(d.amount-ap.amount)<0.01 and abs(d.date-ap.date)<=30
              and {ctx['pay_state'].replace('pm.','d.').replace('ap.','d.')} in {ctx['paid_states']}) same_amount_30d
    from account_payment ap join account_move pm on pm.id=ap.move_id join account_journal j on j.id=ap.journal_id
    join res_company c on c.id=ap.company_id join res_users u on u.id=ap.create_uid join res_partner rp on rp.id=ap.partner_id
    left join inbound i on i.partner_id=ap.partner_id and i.company_id=ap.company_id
    where ap.payment_type='outbound' and ap.partner_type='customer' and j.type='cash'
      and {ctx['pay_state'].replace('pm.','ap.')} in {ctx['paid_states']}
      and ap.date >= %(since)s and ap.company_id = any(%(cids)s)
    order by u.login, ap.date"""
    cols, rows = db.q(sql, P(ctx))
    return dict(key="F03_cash_refunds", severity="HIGH",
                title="Customer refunds paid from a cash till",
                why="Cash refunds are the easiest way to take money out. Flags: customer never paid in cash, refund larger than "
                    "receipts, same amount refunded twice within 30 days, entered at night or days later.",
                cols=cols, rows=rows, amount_col="amount", user_col="creator")


def chk_timing(db, ctx, a):
    sql = f"""
    select m.name entry, m.date, (m.create_date + {ctx['tz']}) created_local, j.code journal, j.type journal_type,
           c.name company, u.login creator, round(m.amount_total,2) amount,
           {ctx['night'].format(ts='m.create_date')} night,
           ((m.create_date + {ctx['tz']})::date - m.date) lag_days, left(coalesce(m.ref,''),100) ref
    from account_move m join account_journal j on j.id=m.journal_id join res_company c on c.id=m.company_id
    join res_users u on u.id=m.create_uid
    where m.state='posted' and m.date >= %(since)s and m.company_id = any(%(cids)s)
      and (j.type in ('cash','bank') or exists(select 1 from account_move_line l where l.move_id=m.id and l.account_id = any(%(tills)s)))
      and ({ctx['night'].format(ts='m.create_date')} or ((m.create_date + {ctx['tz']})::date - m.date) > %(bd)s)
    order by u.login, m.date"""
    cols, rows = db.q(sql, P(ctx, bd=a.backdate_days))
    return dict(key="F04_night_or_backdated_cash_bank", severity="MEDIUM",
                title=f"Cash/bank entries created at night or more than {a.backdate_days} days after their accounting date",
                why="Entries made after hours or back-dated are how books are adjusted after a cash count or a review. "
                    "Compare with each user's normal working pattern.",
                cols=cols, rows=rows, amount_col="amount", user_col="creator")


def chk_resets(db, ctx):
    f = ctx["trk_field"]
    sql = f"""
    select m.name entry, j.code journal, m.date entry_date_now, round(m.amount_total,2) amount, m.state current_state,
           (mm.date + {ctx['tz']}) changed_local, coalesce(u.login, p.name) changed_by, fld.name field,
           coalesce(t.old_value_char, t.old_value_datetime::date::text) old_value,
           coalesce(t.new_value_char, t.new_value_datetime::date::text) new_value, cu.login entry_creator
    from mail_tracking_value t join ir_model_fields fld on fld.id=t.{f}
    join mail_message mm on mm.id=t.mail_message_id
    join account_move m on m.id=mm.res_id join account_journal j on j.id=m.journal_id
    join res_users cu on cu.id=m.create_uid
    left join res_partner p on p.id=mm.author_id left join res_users u on u.partner_id=mm.author_id and u.share=false
    where mm.model='account.move' and m.company_id = any(%(cids)s) and m.date >= %(since)s
      and ((fld.name='state' and (t.old_value_char ilike 'posted' or t.new_value_char ilike 'cancel%%'))
           or fld.name='date')
      and (j.type in ('cash','bank') or exists(select 1 from account_move_line l where l.move_id=m.id and l.account_id = any(%(tills)s)))
    order by coalesce(u.login, p.name), mm.date"""
    cols, rows = db.q(sql, P(ctx))
    return dict(key="F05_reset_cancel_redate", severity="MEDIUM",
                title="Posted cash/bank entries reset to draft, cancelled or re-dated (Odoo change log)",
                why="Resetting and re-dating posted cash entries changes what a past cash count would have shown. "
                    "Each reset is a chance to change figures: check F13 for the amount changes Odoo logged.",
                cols=cols, rows=rows, amount_col="amount", user_col="changed_by")


def chk_sequence_gaps(db, ctx):
    sql = """
    with s as (
      select m.journal_id, m.sequence_prefix, m.sequence_number n, m.name, m.date, m.create_uid, m.create_date
      from account_move m where m.sequence_prefix is not null and m.name <> '/' and m.company_id = any(%(cids)s)
        and m.date >= %(since)s),
    b as (select journal_id, sequence_prefix, min(n) lo, max(n) hi, count(*) cnt from s group by 1,2
          having max(n)-min(n)+1 > count(*)),
    g as (select b.journal_id, b.sequence_prefix, gs n from b, generate_series(b.lo, b.hi) gs
          where not exists (select 1 from s where s.journal_id=b.journal_id and s.sequence_prefix=b.sequence_prefix and s.n=gs))
    select j.code journal, j.type journal_type, c.name company, g.sequence_prefix||lpad(g.n::text, 4, '0') missing_number,
           (select s.name||' '||s.date||' '||u.login from s join res_users u on u.id=s.create_uid
             where s.journal_id=g.journal_id and s.sequence_prefix=g.sequence_prefix and s.n<g.n order by s.n desc limit 1) entry_before,
           (select s.name||' '||s.date||' '||u.login from s join res_users u on u.id=s.create_uid
             where s.journal_id=g.journal_id and s.sequence_prefix=g.sequence_prefix and s.n>g.n order by s.n limit 1) entry_after
    from g join account_journal j on j.id=g.journal_id join res_company c on c.id=j.company_id
    where j.type in ('cash','bank','sale')
    order by c.name, j.code, g.sequence_prefix, g.n"""
    cols, rows = db.q(sql, P(ctx))
    return dict(key="F06_sequence_gaps", severity="MEDIUM",
                title="Missing numbers in cash, bank and sales journal sequences (deleted entries)",
                why="Odoo numbers entries when posted; a gap means an entry was deleted (or a draft numbered and removed). "
                    "Odoo keeps no deletion log, so use server logs or a backup from that date to see what it was.",
                cols=cols, rows=rows, amount_col=None, user_col=None)


def chk_self_service(db, ctx):
    sql = f"""
    select cn.name credit_note, cn.date cn_date, c.name company, u.login user_login, rp.name partner,
           round(cn.amount_total,2) cn_amount, pm.name refund_payment, ap.date refund_date, j.code refund_journal,
           round(ap.amount,2) refund_amount, left(coalesce(cn.ref,''),100) cn_reason
    from account_move cn join res_users u on u.id=cn.create_uid join res_company c on c.id=cn.company_id
    join res_partner rp on rp.id=cn.partner_id
    join account_payment ap on ap.partner_id=cn.partner_id and ap.company_id=cn.company_id and ap.create_uid=cn.create_uid
         and ap.payment_type='outbound' and ap.date between cn.date and cn.date + 30
         and {ctx['pay_state'].replace('pm.','ap.')} in {ctx['paid_states']}
    join account_move pm on pm.id=ap.move_id join account_journal j on j.id=ap.journal_id
    where cn.move_type='out_refund' and cn.state='posted' and cn.date >= %(since)s and cn.company_id = any(%(cids)s)
    order by u.login, cn.date"""
    cols, rows = db.q(sql, P(ctx))
    return dict(key="F07_self_service_refund", severity="MEDIUM",
                title="Same user raised the credit note and paid the refund (no second person)",
                why="Segregation of duties: issuing a credit note and paying the money out should be different people. "
                    "Check each against an approved refund request and the customer's receiving account.",
                cols=cols, rows=rows, amount_col="refund_amount", user_col="user_login")


def chk_vendor_bank(db, ctx):
    sql = f"""
    select rp.name vendor, b.acc_number, (b.create_date + {ctx['tz']}) bank_created_local, ub.login bank_created_by,
           pm.name payment, ap.date payment_date, round(ap.amount,2) amount, up.login paid_by,
           (ap.date - (b.create_date + {ctx['tz']})::date) days_after_bank_added,
           (select string_agg(distinct p2.name, '; ') from res_partner_bank b2 join res_partner p2 on p2.id=b2.partner_id
             where b2.sanitized_acc_number=b.sanitized_acc_number and b2.partner_id<>b.partner_id) same_account_used_by
    from account_payment ap join account_move pm on pm.id=ap.move_id join res_partner rp on rp.id=ap.partner_id
    join res_partner_bank b on b.partner_id=ap.partner_id
    join res_users ub on ub.id=b.create_uid join res_users up on up.id=ap.create_uid
    where ap.payment_type='outbound' and ap.partner_type='supplier' and {ctx['pay_state'].replace('pm.','ap.')} in {ctx['paid_states']}
      and ap.date >= %(since)s and ap.company_id = any(%(cids)s)
      and ap.date between (b.create_date + {ctx['tz']})::date and (b.create_date + {ctx['tz']})::date + 30
    order by ap.date"""
    cols, rows = db.q(sql, P(ctx))
    # shared bank accounts across partners (vendor vs employee/customer)
    cols2, rows2 = db.q("""
    select b.sanitized_acc_number account, count(distinct b.partner_id) partners, string_agg(distinct p.name, '; ') partner_names
    from res_partner_bank b join res_partner p on p.id=b.partner_id
    where coalesce(b.sanitized_acc_number,'')<>'' group by 1 having count(distinct b.partner_id)>1 order by 2 desc""")
    rows = rows + [tuple(["(shared account) " + str(r[2]), r[0], None, None, None, None, None, None, None, r[1]]) for r in rows2]
    return dict(key="F08_vendor_bank_changes", severity="HIGH",
                title="Supplier paid within 30 days of a bank account being added, and bank accounts shared by several partners",
                why="Bank-detail change fraud (business email compromise or insider) shows as a new account followed quickly by a "
                    "payment. A vendor account shared with an employee or another vendor is a ghost-vendor indicator.",
                cols=cols, rows=rows, amount_col="amount", user_col="paid_by")


def chk_duplicate_bills(db, ctx):
    # A reference equal to an internal order number (auto-created bills per order line) is not a supplier invoice number.
    internal = []
    for t in ("sale_order", "purchase_order"):
        if db.has_table(t):
            internal.append(f"select lower(regexp_replace(name,'[^a-zA-Z0-9]','','g')) from {t}")
    excl = f"and b1.nref not in ({' union '.join(internal)})" if internal else ""
    sql = """
    with b as (
      select m.id, m.partner_id, m.company_id, m.name, coalesce(m.invoice_date, m.date) d, m.ref, m.amount_total amt, m.create_uid,
             lower(regexp_replace(coalesce(m.ref,''),'[^a-zA-Z0-9]','','g')) nref
      from account_move m
      where m.move_type='in_invoice' and m.state='posted' and m.amount_total > 0 and m.partner_id is not null
        and m.date >= %(since)s and m.company_id = any(%(cids)s))
    select rp.name vendor, b1.name bill_1, b1.d date_1, b1.ref ref_1, b2.name bill_2, b2.d date_2, b2.ref ref_2,
           round(b2.amt,2) amount, u1.login created_1, u2.login created_2,
           'same vendor reference and amount' match
    from b b1 join b b2 on b2.partner_id=b1.partner_id and b2.company_id=b1.company_id and b2.id>b1.id
         and abs(b2.amt-b1.amt)<0.01
         and b1.nref<>'' and b1.nref=b2.nref
    join res_partner rp on rp.id=b1.partner_id join res_users u1 on u1.id=b1.create_uid join res_users u2 on u2.id=b2.create_uid
    where true __EXCL__
    order by rp.name, b1.d""".replace("__EXCL__", excl)
    cols, rows = db.q(sql, P(ctx))
    return dict(key="F09_duplicate_vendor_bills", severity="MEDIUM",
                title="Possible duplicate vendor bills (same vendor, same amount, same vendor reference)",
                why="Duplicate bills get paid twice and the second payment diverted. Confirm against the supplier statement.",
                cols=cols, rows=rows, amount_col="amount", user_col="created_2")


def chk_payments_to_staff(db, ctx):
    emp = "or ap.partner_id in (select work_contact_id from hr_employee where work_contact_id is not null)" \
        if db.has_table("hr_employee") and db.has_col("hr_employee", "work_contact_id") else ""
    sql = f"""
    select pm.name payment, ap.date, j.code journal, ap.payment_type, ap.partner_type, rp.name partner, round(ap.amount,2) amount,
           u.login created_by, left(coalesce(ap.{ctx['memo']},''),100) memo,
           (ap.partner_id = (select partner_id from res_users where id=ap.create_uid)) paid_to_self
    from account_payment ap join account_move pm on pm.id=ap.move_id join account_journal j on j.id=ap.journal_id
    join res_partner rp on rp.id=ap.partner_id join res_users u on u.id=ap.create_uid
    where {ctx['pay_state'].replace('pm.','ap.')} in {ctx['paid_states']} and ap.payment_type='outbound'
      and ap.date >= %(since)s and ap.company_id = any(%(cids)s)
      and (ap.partner_id in (select partner_id from res_users where share=false) {emp})
    order by paid_to_self desc, u.login, ap.date"""
    cols, rows = db.q(sql, P(ctx))
    return dict(key="F10_payments_to_staff", severity="MEDIUM",
                title="Outbound payments to partners who are internal users or employees",
                why="Refunds or vendor payments to staff, and above all to the person who made the payment, need a business reason "
                    "(salary and expense claims normally go through payroll/expenses, not customer refunds).",
                cols=cols, rows=rows, amount_col="amount", user_col="created_by")


def chk_amount_edits(db, ctx):
    f = ctx["trk_field"]
    sql = f"""
    select m.name entry, c.name company, j.code journal, m.date, (mm.date + {ctx['tz']}) changed_local,
           coalesce(u.login, p.name) changed_by, cu.login entry_creator,
           string_agg(t.old_value_float::text || ' > ' || t.new_value_float::text, ', ' order by t.id) balance_changes,
           max(abs(t.new_value_float) - abs(t.old_value_float)) max_increase,
           ((mm.date - m.create_date) < interval '1 hour') within_1h_of_creation
    from mail_tracking_value t join ir_model_fields fld on fld.id=t.{f} and fld.name='balance' and fld.model='account.move.line'
    join mail_message mm on mm.id=t.mail_message_id and mm.model='account.move'
    join account_move m on m.id=mm.res_id join account_journal j on j.id=m.journal_id join res_company c on c.id=m.company_id
    join res_users cu on cu.id=m.create_uid
    left join res_partner p on p.id=mm.author_id left join res_users u on u.partner_id=mm.author_id and u.share=false
    where m.company_id = any(%(cids)s) and m.date >= %(since)s
      and exists(select 1 from account_move_line l where l.move_id=m.id and (l.account_id = any(%(tills)s) or l.account_id = any(%(banks)s)))
    group by m.id, m.name, c.name, j.code, m.date, mm.id, mm.date, u.login, p.name, cu.login, m.create_date
    order by coalesce(u.login, p.name), mm.date"""
    cols, rows = db.q(sql, P(ctx))
    return dict(key="F13_amount_edits_cash_bank", severity="HIGH",
                title="Line amounts changed on cash/bank entries (Odoo change log)",
                why="Raising a cash-to-bank deposit after posting lowers book cash without cash reaching the bank; raising a refund "
                    "or payout after creation takes more cash out. Match every changed deposit to the bank statement.",
                cols=cols, rows=rows, amount_col="max_increase", user_col="changed_by")


def chk_self_payment(db, ctx):
    sql = f"""
    with u as (select u.id, u.login, regexp_split_to_array(lower(p.name), '\\s+') toks
               from res_users u join res_partner p on p.id=u.partner_id where not u.share and u.id > 1)
    select m.name entry, m.date, c.name company, u.login creator, round(cl.credit,2) cash_out,
           left(translate(coalesce(o.name,''), chr(10)||chr(9), '  '),160) label,
           (select count(*) from ir_attachment x where x.res_model='account.move' and x.res_id=m.id) attachments
    from account_move_line cl join account_move m on m.id=cl.move_id join res_company c on c.id=m.company_id
    join u on u.id=m.create_uid
    join account_move_line o on o.move_id=m.id and o.debit>0 and o.id<>cl.id
    where m.state='posted' and cl.account_id = any(%(tills)s) and cl.credit>0
      and m.date >= %(since)s and m.company_id = any(%(cids)s)
      and (select count(*) from unnest(u.toks) t where length(t) >= 4 and lower(coalesce(o.name,'')||' '||coalesce(m.ref,'')) like '%%'||t||'%%') >= 1
      and (o.partner_id is null or o.partner_id = (select partner_id from res_users where id=m.create_uid))
      and o.account_id <> all(%(tills)s) and o.account_id <> all(%(banks)s) and o.account_id <> all(%(cashacc)s)
    order by u.login, m.date"""
    cols, rows = db.q(sql, P(ctx))
    return dict(key="F14_cash_paid_to_self", severity="MEDIUM",
                title="Cash paid from a till where the label names the person who entered it",
                why="A cashier paying their own salary, advance or refund from the till they control needs a second person "
                    "and a payroll cross-check (e.g. WPS paid as well). Name matching is fuzzy: confirm each row.",
                cols=cols, rows=rows, amount_col="cash_out", user_col="creator")


def chk_custom_workflows(db, ctx):
    """Optional tests for custom refund / payment-proof workflows when those tables exist."""
    out = []
    if db.has_table("sale_payment_proof"):
        sql = f"""
        select so.name sale_order, rp.name customer, round(pr.amount,2) agent_recorded, j.type agent_journal_type, j.code agent_journal,
               pm.name payment, j2.code booked_journal, round(ap.amount,2) booked_amount, u.login cashier,
               case when j.type='cash' and j2.type<>'cash' then 'cash proof booked to bank/gateway'
                    when ap.amount < pr.amount - 1 then 'booked less than recorded' else '' end flag
        from sale_payment_proof pr join account_journal j on j.id=pr.journal_id
        join account_payment ap on ap.id=pr.payment_id join account_move pm on pm.id=ap.move_id
        join account_journal j2 on j2.id=ap.journal_id join sale_order so on so.id=pr.order_id
        join res_partner rp on rp.id=so.partner_id join res_users u on u.id=ap.create_uid
        where ap.company_id = any(%(cids)s) and ap.date >= %(since)s and ap.state<>'canceled'
          and ((j.type='cash' and j2.type<>'cash') or ap.amount < pr.amount - 1)
        order by u.login, ap.date"""
        cols, rows = db.q(sql, P(ctx))
        out.append(dict(key="F11_payment_proof_mismatch", severity="HIGH",
                        title="Agent's payment proof vs what the cashier booked (custom sale_payment_proof)",
                        why="Customer cash recorded by the agent but booked to a bank journal or for less never reaches the till. "
                            "Verify each against the bank statement.",
                        cols=cols, rows=rows, amount_col="agent_recorded", user_col="cashier"))
    if db.has_table("refund_request"):
        sql = f"""
        select rr.name refund_request, c.name company, rr.payment_method requested_method, rr.total_refund_payable payable,
               pm.name payment, j.code journal, j.type journal_type, round(ap.amount,2) amount, u.login paid_by,
               au.login accounts_approver,
               case when j.type='cash' and coalesce(rr.payment_method,'')<>'cash' then 'paid in cash, customer asked for '||coalesce(rr.payment_method,'?')
                    else '' end channel_flag,
               (au.id = ap.create_uid) self_approved
        from refund_request rr
        join account_payment ap on ap.company_id=rr.company_id and ap.{ctx['memo']} ilike 'Refund: '||rr.name||' %%'
             and ap.payment_type='outbound' and ap.state in {ctx['paid_states']}
        join account_move pm on pm.id=ap.move_id join account_journal j on j.id=ap.journal_id
        join res_company c on c.id=rr.company_id join res_users u on u.id=ap.create_uid
        left join res_users au on au.id=rr.accounts_user_id
        where rr.company_id = any(%(cids)s) and ap.date >= %(since)s
          and ((j.type='cash' and coalesce(rr.payment_method,'')<>'cash') or au.id = ap.create_uid
               or rr.id in (select r2.id from refund_request r2 join account_payment a2 on a2.company_id=r2.company_id
                            and a2.{ctx['memo']} ilike 'Refund: '||r2.name||' %%' and a2.payment_type='outbound'
                            and a2.state in {ctx['paid_states']} group by r2.id having sum(a2.amount) > max(r2.total_refund_payable)+1))
        order by u.login, ap.date"""
        cols, rows = db.q(sql, P(ctx))
        out.append(dict(key="F12_refund_request_exceptions", severity="HIGH",
                        title="Refund-request exceptions: wrong channel, self-approved, or paid above payable (custom refund_request)",
                        why="A refund should be paid through the channel the customer asked for, approved by someone else, and "
                            "never exceed the approved payable.",
                        cols=cols, rows=rows, amount_col="amount", user_col="paid_by"))
    return out


# --------------------------------------------------------------------------- output
def fmt(v):
    if isinstance(v, (dt.datetime,)):
        return v.strftime("%Y-%m-%d %H:%M")
    if isinstance(v, dt.date):
        return v.isoformat()
    return v


def main():
    a = parse_args()
    os.makedirs(a.out, exist_ok=True)
    db = DB(a)
    ctx = build_ctx(db, a)
    checks = [chk_manual_cash_out, chk_fabricated_liability, chk_cash_refunds, lambda d, c: chk_timing(d, c, a),
              chk_resets, chk_amount_edits, chk_sequence_gaps, chk_self_service, chk_vendor_bank, chk_duplicate_bills,
              chk_payments_to_staff, chk_self_payment]
    results, skipped = [], []
    for fn in checks:
        try:
            r = fn(db, ctx)
            results.extend(r if isinstance(r, list) else [r])
        except Exception as e:  # keep going on schema differences
            db.conn.rollback() if not db.conn.autocommit else None
            skipped.append((getattr(fn, "__name__", "check"), str(e).splitlines()[0]))
    try:
        results.extend(chk_custom_workflows(db, ctx))
    except Exception as e:
        skipped.append(("custom_workflow_checks", str(e).splitlines()[0]))

    focus = None
    if ctx["focus_uid"]:
        focus = a.login
    rollup = {}
    lines = [f"# Odoo forensic scan: {a.db}", "",
             f"Accounting dates from **{ctx['since']}**. Local time = UTC{a.tz_offset:+g}h. Night = {a.night_start}:00–{a.night_end}:00. "
             f"Companies scanned: {len(ctx['company_ids'])}. Read-only connection.", ""]
    if focus:
        lines += [f"Focus user: **{focus}** (rows for other users are kept in the CSVs).", ""]
    lines += ["| Test | Severity | Rows | Amount | Title |", "|---|---|---|---|---|"]
    for r in results:
        cols, rows = r["cols"], r["rows"]
        path = os.path.join(a.out, f"{r['key']}.csv")
        with open(path, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            for row in rows[: a.max_rows]:
                w.writerow([fmt(v) for v in row])
        amt = 0.0
        if r["amount_col"] and r["amount_col"] in cols:
            ai = cols.index(r["amount_col"])
            amt = sum(float(x[ai] or 0) for x in rows)
        if r["user_col"] and r["user_col"] in cols:
            ui = cols.index(r["user_col"])
            ai = cols.index(r["amount_col"]) if r["amount_col"] in cols else None
            for x in rows:
                u = x[ui] or "(unknown)"
                d = rollup.setdefault(u, {})
                cnt, s = d.get(r["key"], (0, 0.0))
                d[r["key"]] = (cnt + 1, s + (float(x[ai] or 0) if ai is not None else 0))
        lines.append(f"| {r['key']} | {r['severity']} | {len(rows)} | {amt:,.2f} | {r['title']} |")
    lines += ["", "## Per-user roll-up (rows flagged per test)", ""]
    keys = [r["key"] for r in results if r["user_col"]]
    lines.append("| User | " + " | ".join(k.split('_')[0] for k in keys) + " | High-severity amount |")
    lines.append("|---|" + "---|" * len(keys) + "---|")
    sev = {r["key"]: r["severity"] for r in results}
    order = sorted(rollup.items(), key=lambda kv: -sum(v[1] for k, v in kv[1].items() if sev.get(k) == "HIGH"))
    for u, d in order:
        hi = sum(v[1] for k, v in d.items() if sev.get(k) == "HIGH")
        mark = " **(focus)**" if focus and u == focus else ""
        lines.append(f"| {u}{mark} | " + " | ".join(str(d.get(k, (0, 0))[0] or "") for k in keys) + f" | {hi:,.2f} |")
    lines += ["", "## What each test means", ""]
    for r in results:
        lines.append(f"- **{r['key']}**: {r['why']}")
    if skipped:
        lines += ["", "## Skipped (schema differences)", ""] + [f"- {n}: {e}" for n, e in skipped]
    lines += ["", "Amounts are in each company's currency; do not add across currencies without converting. "
              "A flag is an indicator to investigate, not proof."]
    with open(os.path.join(a.out, "SUMMARY.md"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines[:12 + len(results)]))
    print(f"\nWrote {len(results)} CSVs and SUMMARY.md to {a.out}")


if __name__ == "__main__":
    main()
