#!/usr/bin/env python3
"""Read-only controls & security baseline check for an Odoo (17/18/19) database.

Checks (each PASS / WARN / FAIL with evidence):
  K01 accounting integrity settings per company: restrictive audit trail, lock dates, hash-secured journals
  K02 bank reconciliation evidence per bank journal (statement lines, last statement, unreconciled items)
  K03 identity: 2FA (TOTP) enrolment & enforcement policy, passkeys, password minimum length, login throttling
  K04 privileged users (Settings admin, Access Rights, Accounting admin) and admins who also post transactions
  K05 activity-based segregation-of-duties conflicts (last 180 days)
  K06 dormant and shared/generic accounts, API keys
  K07 data exposure: public attachments, portal access tokens on invoices, outgoing mail server encryption
  K08 server configuration file (optional --conf): list_db, admin_passwd hashed, proxy_mode, dbfilter, workers, limits
  K09 custom code (optional --addons DIR): public/no-auth routes, csrf=False, sudo() in public routes, secrets/raw bodies logged
  K10 PostgreSQL role used by Odoo: superuser / create-role / create-db privileges
Writes CONTROLS_REPORT.md and one CSV per check into --out. Never prints secret values.

Usage: python odoo_controls_check.py --db mydb --out ./controls [--conf /etc/odoo/odoo.conf] [--days 180]
"""
import argparse
import configparser
import csv
import datetime as dt
import os
import re
import sys

try:
    import psycopg2
except ImportError:  # pragma: no cover
    sys.exit("psycopg2 is required (use the Odoo venv's python)")

GENERIC_LOGIN = re.compile(r"^(admin|administrator|cashier\w*|accounts?\w*|finance|info|ops|support|sales|typing|reception|"
                           r"frontdesk|office|test\w*|demo|user\d*|staff|team|hr|it|airticket|booking\w*)@", re.I)


def args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--db", required=True)
    for k in ("host", "port", "user", "password"):
        p.add_argument(f"--{k}")
    p.add_argument("--out", required=True)
    p.add_argument("--conf", help="path to odoo.conf to review (read locally; values of secrets are never printed)")
    p.add_argument("--days", type=int, default=180, help="activity window for SoD and dormancy")
    p.add_argument("--addons", action="append", default=[], help="custom addons directory to scan for unsafe routes (repeatable)")
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

    def q(self, sql, p=None):
        self.cur.execute(sql, p or {})
        return [d[0] for d in self.cur.description], self.cur.fetchall()

    def one(self, sql, p=None):
        return self.q(sql, p)[1][0][0]

    def has_table(self, t):
        return self.one("select to_regclass(%(t)s) is not null", {"t": t})

    def has_col(self, t, c):
        return self.one("select count(*)>0 from information_schema.columns where table_name=%(t)s and column_name=%(c)s",
                        {"t": t, "c": c})

    def param(self, key, default=None):
        _, r = self.q("select value from ir_config_parameter where key=%(k)s", {"k": key})
        return r[0][0] if r else default

    def group_users(self, xmlid):
        mod, name = xmlid.split(".")
        _, r = self.q("""select u.id, u.login from res_groups_users_rel rel join res_users u on u.id=rel.uid
                         join ir_model_data d on d.model='res.groups' and d.res_id=rel.gid
                         where d.module=%(m)s and d.name=%(n)s and u.active and not u.share and u.id > 1""",
                      {"m": mod, "n": name})
        return r


class Report:
    def __init__(self, out):
        self.out, self.items = out, []
        os.makedirs(out, exist_ok=True)

    def add(self, code, title, status, finding, fix, cols=None, rows=None, ref=""):
        if cols is not None:
            with open(os.path.join(self.out, f"{code}.csv"), "w", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(cols)
                w.writerows([[v.isoformat() if hasattr(v, "isoformat") else v for v in r] for r in rows])
        self.items.append((code, title, status, finding, fix, ref))

    def write(self, header):
        icon = {"FAIL": "FAIL", "WARN": "WARN", "PASS": "PASS", "INFO": "INFO"}
        lines = [header, "", "| # | Check | Status | Finding |", "|---|---|---|---|"]
        for c, t, s, f, _, _ in self.items:
            lines.append(f"| {c} | {t} | **{icon[s]}** | {f} |")
        lines += ["", "## How to fix", ""]
        for c, t, s, f, fix, ref in self.items:
            if s in ("FAIL", "WARN"):
                lines.append(f"- **{c} {t}**: {fix}" + (f" _(Standard: {ref})_" if ref else ""))
        lines += ["", "CSV evidence for each check is in this folder. This scan is read-only."]
        open(os.path.join(self.out, "CONTROLS_REPORT.md"), "w").write("\n".join(lines) + "\n")
        return lines


def main():
    a = args()
    db, rep = DB(a), Report(a.out)
    since = dt.date.today() - dt.timedelta(days=a.days)

    # ---------------- K01 accounting integrity
    has_rat = db.has_col("res_company", "restrictive_audit_trail")
    has_hard = db.has_col("res_company", "hard_lock_date")
    cols, rows = db.q(f"""
      select c.name,
             {'c.restrictive_audit_trail' if has_rat else 'null'} restrictive_audit_trail,
             {'c.hard_lock_date' if has_hard else 'null'} hard_lock_date,
             c.fiscalyear_lock_date,
             (select count(*) from account_journal j where j.company_id=c.id and j.type in ('sale','purchase')) sp_journals,
             (select count(*) from account_journal j where j.company_id=c.id and j.type in ('sale','purchase') and j.restrict_mode_hash_table) sp_hashed,
             (select count(*) from account_move m where m.company_id=c.id and m.state='posted') posted_moves
      from res_company c order by c.name""")
    active = [r for r in rows if r[6] > 0]
    no_rat = [r[0] for r in active if has_rat and not r[1]]
    stale = []
    for r in active:
        lock = max([d for d in (r[2], r[3]) if d] or [None]) if (r[2] or r[3]) else None
        if not lock or (dt.date.today() - lock).days > 75:
            stale.append(f"{r[0]} ({lock or 'none'})")
    unhashed = [r[0] for r in active if r[4] and r[5] < r[4]]
    status = "FAIL" if no_rat or stale else ("WARN" if unhashed else "PASS")
    rep.add("K01", "Accounting integrity settings", status,
            f"{len(no_rat)} active companies without Restrictive Audit Trail; {len(stale)} with no lock date or lock older than 75 days; "
            f"{len(unhashed)} with sales/purchase journals not hash-secured.",
            "Accounting > Settings: enable Restrictive Audit Trail (blocks deleting posted entries and their logs). Close each month: "
            "set the lock date within ~15 days of month end and the hard lock after the audit. Enable 'Secure Posted Entries with Hash' "
            "on sales/purchase journals (and run the integrity report).",
            cols, rows, "COSO 2013 Principle 10/13; ISO 27001:2022 A.8.15; UAE Tax Procedures record-keeping")

    # ---------------- K02 bank reconciliation
    cols, rows = db.q("""
      select c.name company, j.code, j.name->>'en_US' journal,
             (select count(*) from account_bank_statement_line s where s.journal_id=j.id) stmt_lines,
             (select max(m.date) from account_bank_statement_line s join account_move m on m.id=s.move_id where s.journal_id=j.id) last_stmt,
             (select count(*) from account_bank_statement_line s where s.journal_id=j.id and not s.is_reconciled) unreconciled,
             (select count(*) from account_move m where m.journal_id=j.id and m.state='posted' and m.date >= %(s)s) moves_in_window,
             (select round(sum(l.balance),2) from account_move_line l where l.account_id=j.default_account_id and l.parent_state='posted') gl_balance
      from account_journal j join res_company c on c.id=j.company_id
      where j.type='bank' and j.active order by c.name, j.code""", {"s": since})
    used = [r for r in rows if r[6] > 0]
    never = [r for r in used if r[3] == 0]
    old = [r for r in used if r[4] and (dt.date.today() - r[4]).days > 35]
    rep.add("K02", "Bank & gateway reconciliation", "FAIL" if never or old else "PASS",
            f"{len(used)} bank/gateway journals with activity in the window; {len(never)} have NO statements at all; "
            f"{len(old)} last reconciled more than 35 days ago.",
            "Import or sync bank, card-acquirer and BNPL (Tabby/Tamara) statements at least weekly and reconcile every line; review "
            "unreconciled items and clearing-account balances at month end; reviewer must not be a cashier.",
            cols, rows, "COSO 2013 Principle 12 (control activities); book ch.12-13 independent checks")

    # ---------------- K03 identity
    internal = db.one("select count(*) from res_users where active and not share and id > 1")
    totp = db.one("select count(*) from res_users where active and not share and id > 1 and totp_secret is not null") \
        if db.has_col("res_users", "totp_secret") else 0
    passkeys = db.one("select count(distinct create_uid) from auth_passkey_key") if db.has_table("auth_passkey_key") else 0
    policy = db.param("auth_totp.policy", "not set")
    minlen = int(db.param("auth_password_policy.minlength", "0") or 0)
    mods = dict(db.q("select name, state from ir_module_module where name in ('auth_password_policy','auth_totp','auth_totp_mail','auth_passkey')")[1])
    missing = [m for m in ('auth_password_policy', 'auth_totp_mail') if mods.get(m) != 'installed']
    cooldown = db.param("base.login_cooldown_after", "default")
    admins_wo_2fa = db.q("""select u.login from res_users u join res_groups_users_rel r on r.uid=u.id
                            join ir_model_data d on d.model='res.groups' and d.res_id=r.gid and d.module='base' and d.name in ('group_system','group_erp_manager')
                            where u.active and not u.share and u.id>1 and u.totp_secret is null group by u.login""")[1] \
        if db.has_col("res_users", "totp_secret") else []
    st = "FAIL" if (totp + passkeys) < internal * 0.9 or minlen < 8 or admins_wo_2fa else ("WARN" if minlen < 12 else "PASS")
    rep.add("K03", "Authentication", st,
            f"{totp}/{internal} internal users have TOTP, {passkeys} have passkeys; enforcement policy = {policy}; "
            f"password min length = {minlen or 'not set'}; login throttle after {cooldown} failures; "
            f"{len(admins_wo_2fa)} administrators without 2FA; modules not installed: {', '.join(missing) or 'none'}.",
            "Install auth_totp_mail and set 'Enforce two-factor authentication' for all employees (policy employee_required), "
            "or roll out passkeys (auth_passkey). Set auth_password_policy.minlength to at least 12 (15 if any account is password-only); "
            "do not force periodic password changes; keep login throttling on. Administrators first.",
            ["login"], admins_wo_2fa, "NIST SP 800-63B-4 (2025); CIS Controls v8.1 #6; PCI DSS 4.0.1 req. 8")

    # ---------------- K04 privileged users
    priv = {}
    for x, label in (("base.group_system", "Settings admin"), ("base.group_erp_manager", "Access-rights admin"),
                     ("account.group_account_manager", "Accounting admin")):
        for uid, login in db.group_users(x):
            priv.setdefault(login, [uid, set()])[1].add(label)
    rows = []
    for login, (uid, labels) in sorted(priv.items()):
        n_moves = db.one("select count(*) from account_move where create_uid=%(u)s and date >= %(s)s", {"u": uid, "s": since})
        n_pay = db.one("select count(*) from account_payment where create_uid=%(u)s and date >= %(s)s", {"u": uid, "s": since})
        rows.append((login, ", ".join(sorted(labels)), n_moves, n_pay))
    transacting = [r for r in rows if r[2] + r[3] > 20]
    rep.add("K04", "Privileged access", "FAIL" if len([r for r in rows if 'Settings admin' in r[1]]) > 3 or transacting else "WARN",
            f"{len(rows)} users hold admin-level groups; {len(transacting)} of them also post day-to-day transactions.",
            "Keep Settings/Access-rights admin to 1-2 named people who do not process transactions; give accountants "
            "'Accountant' not 'Administrator'; use a separate named admin login for configuration; review quarterly.",
            ["login", "admin groups", f"entries last {a.days}d", f"payments last {a.days}d"], rows,
            "ISO 27001:2022 A.5.15/A.8.2; COBIT 2019 DSS05/APO07; SOX/ICFR SoD")

    # ---------------- K05 activity-based SoD
    conflicts = [
        ("created credit notes", "select distinct create_uid from account_move where move_type='out_refund' and state='posted' and date>=%(s)s",
         "paid customer refunds", "select distinct create_uid from account_payment where payment_type='outbound' and partner_type='customer' and date>=%(s)s"),
        ("received customer cash", "select distinct ap.create_uid from account_payment ap join account_journal j on j.id=ap.journal_id where j.type='cash' and ap.payment_type='inbound' and ap.date>=%(s)s",
         "posted manual journals on cash", "select distinct m.create_uid from account_move m join account_journal j on j.id=m.journal_id where j.type in ('general','cash') and m.move_type='entry' and m.origin_payment_id is null and m.date>=%(s)s and exists(select 1 from account_move_line l join account_journal cj on cj.default_account_id=l.account_id and cj.type='cash' where l.move_id=m.id)"),
        ("created/edited vendor bank accounts", "select distinct create_uid from res_partner_bank where create_date>=%(s)s",
         "paid suppliers", "select distinct create_uid from account_payment where payment_type='outbound' and partner_type='supplier' and date>=%(s)s"),
        ("reset posted entries to draft", "select distinct u.id from mail_tracking_value t join ir_model_fields f on f.id=t.field_id join mail_message mm on mm.id=t.mail_message_id join res_users u on u.partner_id=mm.author_id where mm.model='account.move' and f.name='state' and t.old_value_char ilike 'posted' and mm.date>=%(s)s",
         "posted cash/bank payments", "select distinct create_uid from account_payment where date>=%(s)s"),
        ("holds Settings/Access-rights admin", "select rel.uid from res_groups_users_rel rel join ir_model_data d on d.model='res.groups' and d.res_id=rel.gid where d.module='base' and d.name in ('group_system','group_erp_manager')",
         "posted accounting transactions", "select distinct create_uid from account_move where date>=%(s)s and move_type<>'entry' or (move_type='entry' and date>=%(s)s)"),
    ]
    if not db.has_col("account_move", "origin_payment_id"):
        conflicts = [c[:3] + (c[3].replace("origin_payment_id", "payment_id"),) if "origin_payment_id" in c[3] else c for c in conflicts]
    rows = []
    for a_lbl, a_sql, b_lbl, b_sql in conflicts:
        try:
            _, ra = db.q(a_sql, {"s": since})
            _, rb = db.q(b_sql, {"s": since})
        except Exception as e:  # schema differences
            rows.append(("(check skipped)", a_lbl, b_lbl, str(e).splitlines()[0]))
            continue
        both = {r[0] for r in ra} & {r[0] for r in rb}
        for uid in sorted(both):
            if uid and uid > 1:
                login = db.one("select login from res_users where id=%(u)s", {"u": uid})
                rows.append((login, a_lbl, b_lbl, ""))
    real = [r for r in rows if not r[0].startswith("(")]
    rep.add("K05", "Segregation of duties (by actual activity)", "FAIL" if real else "PASS",
            f"{len(real)} user/conflict pairs found in the last {a.days} days.",
            "Split the duties, or where the team is too small add a compensating control: a second-person approval in the "
            "workflow (enforced server-side), a daily exception report reviewed by someone outside the cash function, and "
            "customer notifications for every refund.",
            ["login", "duty A", "duty B", "note"], rows, "COSO 2013 Principle 10; book ch.7 SoD")

    # ---------------- K06 dormant / shared accounts, API keys
    has_log = db.has_table("res_users_log")
    cols, rows = db.q(f"""
      select u.login, p.name, u.create_date::date,
             {'(select max(l.create_date)::date from res_users_log l where l.create_uid=u.id)' if has_log else 'null'} last_login,
             (select count(*) from res_users_apikeys k where k.user_id=u.id) api_keys
      from res_users u join res_partner p on p.id=u.partner_id
      where u.active and not u.share and u.id > 1 order by 4 nulls first""") if db.has_table("res_users_apikeys") else ([], [])
    dormant = [r for r in rows if not r[3] or (dt.date.today() - r[3]).days > 90]
    generic = [r for r in rows if GENERIC_LOGIN.match(r[0] or "")]
    keys = [r for r in rows if r[4]]
    flagged = [(r[0], r[1], r[2], r[3], r[4], ", ".join(x for x, c in (("dormant", r in dormant), ("generic/shared login", r in generic),
                                                                       ("has API keys", r in keys)) if c)) for r in rows if r in dormant or r in generic or r in keys]
    rep.add("K06", "Dormant, shared and API accounts", "FAIL" if generic else ("WARN" if dormant or keys else "PASS"),
            f"{len(dormant)} active users with no login in 90 days (or never); {len(generic)} generic/role logins "
            f"(e.g. cashier@, info@) that hide who did what; {len(keys)} users with API keys.",
            "Give every person a named login (no shared cashier@/info@ accounts); archive leavers on their last day "
            "(tie to offboarding); review API keys quarterly and use a dedicated integration user with minimal groups.",
            ["login", "name", "created", "last login", "api keys", "flags"], flagged, "ISO 27001:2022 A.5.16-5.18; CIS v8.1 #5")

    # ---------------- K07 data exposure
    pub = db.one("""select count(*) from ir_attachment where public
                     and coalesce(url,'') not like '/web/assets/%%' and coalesce(res_model,'') not in ('ir.ui.view','ir.ui.menu')
                     and coalesce(mimetype,'') not in ('text/css','application/javascript','text/javascript')
                     and coalesce(res_field,'') not in ('icon','image_1920','image_128','image_256','image_512','image_1024')""")
    tok = db.one("select count(*) from account_move where access_token is not null") if db.has_col("account_move", "access_token") else 0
    cols, rows = db.q("select name, smtp_host, smtp_port, smtp_encryption, active from ir_mail_server") if db.has_table("ir_mail_server") else ([], [])
    plain = [r for r in rows if r[4] and (r[3] or "none") == "none" and "neutraliz" not in (r[0] or "").lower()
             and (r[1] or "") not in ("invalid", "localhost")]
    rep.add("K07", "Data exposure", "FAIL" if plain else ("WARN" if pub > 0 else "PASS"),
            f"{pub} public attachments (excluding web assets and icons); {tok} invoices/entries with a shareable portal link token; "
            f"{len(plain)} active outgoing mail servers without TLS.",
            "Review public attachments (passports and ID scans must never be public); restrict who can share portal links; "
            "use STARTTLS/SSL on every mail server; keep passport/ID fields in a restricted group and out of chatter tracking.",
            cols, rows, "UAE PDPL (Decree-Law 45/2021); Philippines DPA 2012; GDPR Art.32")

    # ---------------- K08 server config
    if a.conf:
        cp = configparser.ConfigParser(interpolation=None)
        cp.read(a.conf)
        o = cp["options"] if cp.has_section("options") else {}
        g = lambda k, d=None: (o.get(k, d) if hasattr(o, "get") else d)
        rows = []
        def chk(k, ok, why):
            rows.append((k, "set" if k in o else "absent", "ok" if ok else "FIX", why))
        ap = g("admin_passwd")
        chk("admin_passwd", bool(ap) and ap.startswith("$pbkdf2"), "master password must be set and stored hashed ($pbkdf2-sha512$...), never plain text")
        chk("list_db", str(g("list_db", "True")).lower() in ("false", "0"), "hide database selector/manager in production")
        chk("dbfilter", bool(g("dbfilter")), "restrict which databases the server serves")
        chk("proxy_mode", str(g("proxy_mode", "False")).lower() in ("true", "1"), "required behind nginx/HTTPS so client IPs and HTTPS are correct")
        chk("workers", int(g("workers", "0") or 0) > 0, "multi-process mode with memory/time limits; 0 = threaded dev mode")
        chk("limit_time_real", bool(g("limit_time_real")), "kill runaway requests")
        chk("log_level / logfile", bool(g("logfile")) or bool(g("syslog")), "send logs to a file/syslog that is shipped off-box and retained")
        chk("db_sslmode", str(g("db_sslmode", "prefer")).lower() in ("require", "verify-ca", "verify-full") or g("db_host", "") in ("", "localhost", "127.0.0.1", "False"),
            "use TLS to a remote PostgreSQL")
        bad = [r for r in rows if r[2] == "FIX"]
        rep.add("K08", "Server configuration", "FAIL" if bad else "PASS",
                f"{len(bad)} of {len(rows)} settings need attention in {os.path.basename(a.conf)} (values not shown).",
                "Fix the settings marked FIX in K08.csv; store the config file readable only by the odoo user (chmod 640).",
                ["setting", "present", "result", "why"], rows, "CIS Controls v8.1 #4 secure configuration; OWASP ASVS 5.0")
    else:
        rep.add("K08", "Server configuration", "INFO", "Not checked (pass --conf path/to/odoo.conf).",
                "Run again with --conf.", None, None)

    # ---------------- K09 custom code routes
    if a.addons:
        route_re = re.compile(r"@http\.route\((?P<args>[^)]*)\)", re.S)
        rows = []
        for root_dir in a.addons:
            for dp, _, files in os.walk(os.path.expanduser(root_dir)):
                if "/tests" in dp or "/static" in dp:
                    continue
                for fn in files:
                    if not fn.endswith(".py"):
                        continue
                    path = os.path.join(dp, fn)
                    try:
                        src = open(path, encoding="utf-8", errors="ignore").read()
                    except OSError:
                        continue
                    for m in route_re.finditer(src):
                        args_ = m.group("args")
                        line = src.count("\n", 0, m.start()) + 1
                        public = re.search(r"auth\s*=\s*['\"](public|none)['\"]", args_)
                        nocsrf = re.search(r"csrf\s*=\s*False", args_)
                        body = src[m.end(): m.end() + 4000].split("\n    @http.route", 1)[0]
                        flags = []
                        if public:
                            flags.append(f"auth={public.group(1)}")
                        if nocsrf:
                            flags.append("csrf=False")
                        if public and ".sudo()" in body:
                            flags.append("sudo() in public route")
                        if re.search(r"_logger\.\w+\([^)]*(headers|httprequest\.data|get_data\(|\bkw\b|\bpost\b|api_key|Authorization)", body):
                            flags.append("logs headers/body/params")
                        if public and not re.search(r"(token|signature|hmac|api_key|secret)", body, re.I):
                            flags.append("no token/signature check seen")
                        if flags:
                            rows.append((os.path.relpath(path, os.path.expanduser(root_dir)), line, args_.strip().split(",")[0][:80], "; ".join(flags)))
        risky = [r for r in rows if "auth=" in r[3] and ("no token" in r[3] or "sudo()" in r[3] or "logs" in r[3])]
        rep.add("K09", "Custom code: exposed routes and logging", "FAIL" if risky else ("WARN" if rows else "PASS"),
                f"{len(rows)} routes with public/no-auth or csrf=False; {len(risky)} of them lack a visible token/signature check, "
                f"use sudo(), or log request data.",
                "For each public route: require a shared secret/HMAC signature or IP allow-list at nginx, never sudo() on data "
                "the caller controls, never auto-create records from unauthenticated input, and log only method/path/IP (mask "
                "Authorization, X-API-Key, api_key). Remove test/debug routes. Review is static: confirm each finding by reading the code.",
                ["file", "line", "route", "flags"], rows, "OWASP Top 10:2025 A01/A09; OWASP API Security Top 10 2023")
    else:
        rep.add("K09", "Custom code: exposed routes and logging", "INFO", "Not checked (pass --addons path/to/custom_addons).",
                "Run again with --addons.", None, None)

    # ---------------- K10 database role
    try:
        cols, rows = db.q("""select r.rolname, r.rolsuper, r.rolcreaterole, r.rolcreatedb
                             from pg_database d join pg_roles r on r.oid=d.datdba where d.datname=current_database()""")
        conf_user = None
        if a.conf:
            cp2 = configparser.ConfigParser(interpolation=None); cp2.read(a.conf)
            conf_user = cp2["options"].get("db_user") if cp2.has_section("options") else None
        if conf_user and conf_user not in [r[0] for r in rows]:
            rows += db.q("select rolname, rolsuper, rolcreaterole, rolcreatedb from pg_roles where rolname=%(u)s", {"u": conf_user})[1]
        bad = [r for r in rows if r[1] or r[2]]
        rep.add("K10", "PostgreSQL role privileges", "FAIL" if bad else ("WARN" if any(r[3] for r in rows) else "PASS"),
                f"Odoo database owner/config role(s): " + ", ".join(f"{r[0]} (superuser={r[1]}, createrole={r[2]}, createdb={r[3]})" for r in rows),
                "Run Odoo as a dedicated non-superuser role that owns only its databases (ALTER ROLE <role> NOSUPERUSER NOCREATEROLE; "
                "keep CREATEDB only if databases are restored through Odoo). Test on a copy first. pg_hba.conf: local/private "
                "network only with scram-sha-256.",
                cols, rows, "CIS PostgreSQL Benchmark; ISO 27001:2022 A.8.2")
    except Exception as e:
        rep.add("K10", "PostgreSQL role privileges", "INFO", f"Not checked ({str(e).splitlines()[0]}).", "", None, None)

    lines = rep.write(f"# Odoo controls & security check: {a.db}\n\nRun {dt.datetime.now():%Y-%m-%d %H:%M}, activity window {a.days} days. Read-only.")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
