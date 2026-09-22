"""
Generates the skeleton of docs/02_data_dictionary.md.

Reads sql/01_schema.sql for column types, keys and constraints, and the CSVs in
data/ for row counts and null counts. Emits markdown with everything mechanical
filled in and a blank Description column for you to complete.

Run:  python tools/gen_data_dictionary.py > docs/02_data_dictionary.md
"""
import re
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "sql" / "01_schema.sql"
DATA = ROOT / "data"

TABLE_ORDER = ["outlets", "platforms", "menu_items", "menu_item_prices",
               "customers", "orders", "order_items", "promotions",
               "item_availability", "wastage", "expenses", "daily_operations"]

GRAIN = {
    "outlets": "one row per physical outlet",
    "platforms": "one row per platform per commercial-terms period",
    "menu_items": "one row per menu item",
    "menu_item_prices": "one row per item x platform x effective price period",
    "customers": "one row per masked, platform-scoped customer reference",
    "orders": "one row per order",
    "order_items": "one row per line item within an order",
    "promotions": "one row per promotional campaign",
    "item_availability": "one row per item x outlet x date",
    "wastage": "one row per outlet x date x waste type",
    "expenses": "one row per outlet x month x expense category (outlet_id NULL = company-level)",
    "daily_operations": "one row per outlet x date",
}


def parse_schema(text):
    tables = {}
    for m in re.finditer(r"CREATE TABLE (\w+) \((.*?)\n\) ENGINE", text, re.S):
        name, body = m.group(1), m.group(2)
        # join physical lines whose parentheses are unbalanced (multi-line ENUMs,
        # multi-line CHECK constraints) into single logical lines
        logical, buf, depth = [], "", 0
        for raw in body.split("\n"):
            t = raw.strip()
            if not t:
                continue
            buf = (buf + " " + t).strip() if buf else t
            depth += t.count("(") - t.count(")")
            if depth <= 0:
                logical.append(buf)
                buf, depth = "", 0
        if buf:
            logical.append(buf)
        body = "\n".join(logical)
        cols, pk, fks, uniques, checks = [], [], {}, [], []
        depth = 0            # paren depth for multi-line CHECK constraints
        pending = ""
        for line in body.split("\n"):
            s = line.strip().rstrip(",")
            if not s or s.startswith("--"):
                continue
            if depth > 0:                       # still inside a multi-line clause
                pending += " " + s
                depth += s.count("(") - s.count(")")
                if depth <= 0:
                    checks.append(pending.strip())
                    pending, depth = "", 0
                continue
            if "CHECK" in s.upper() or s.upper().startswith("CONSTRAINT CHK"):
                d = s.count("(") - s.count(")")
                if d > 0:
                    pending, depth = s, d
                else:
                    checks.append(s)
                continue
            if s.upper().startswith("PRIMARY KEY"):
                pk = [c.strip() for c in re.search(r"\((.*?)\)", s).group(1).split(",")]
            elif "FOREIGN KEY" in s.upper():
                f = re.search(r"FOREIGN KEY \s*\((\w+)\)\s*REFERENCES\s+(\w+)\s*\((\w+)\)", s)
                if f:
                    fks[f.group(1)] = f"{f.group(2)}.{f.group(3)}"
            elif s.upper().startswith("UNIQUE KEY"):
                u = re.search(r"\((.*?)\)\s*$", s)
                if u:
                    uniques.append([c.strip() for c in u.group(1).split(",")])
            elif s.upper().startswith("KEY "):
                pass
            else:
                c = re.match(r"(\w+)\s+(.+)", s)
                if c and not c.group(1).upper() in ("KEY", "CONSTRAINT", "UNIQUE"):
                    cols.append((c.group(1), c.group(2).strip()))
        tables[name] = dict(cols=cols, pk=pk, fks=fks, uniques=uniques, checks=checks)
    return tables


def csv_stats(table):
    p = DATA / f"{table}.csv"
    if not p.exists():
        return 0, {}
    with open(p, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        hdr = r.fieldnames or []
        nulls = {h: 0 for h in hdr}
        n = 0
        for row in r:
            n += 1
            for h in hdr:
                if row[h] == "" or row[h] is None:
                    nulls[h] += 1
    return n, nulls


def split_type(raw):
    t = raw.split("NOT NULL")[0].split("NULL")[0].split("DEFAULT")[0].strip().rstrip(",")
    nullable = "NOT NULL" not in raw.upper()
    default = ""
    d = re.search(r"DEFAULT\s+(\S+)", raw, re.I)
    if d:
        default = d.group(1).rstrip(",")
    return t, nullable, default


def main():
    tables = parse_schema(SCHEMA.read_text())
    total = 0
    out = []
    out.append("# Data Dictionary\n")
    out.append("Database: `etable_analytics` — MySQL 8.0, InnoDB, utf8mb4\n")
    out.append("> Column types, keys and null counts below are generated from "
               "`sql/01_schema.sql` and the source CSVs. Descriptions are written "
               "by hand.\n")
    out.append("## Table overview\n")
    out.append("| Table | Grain | Rows | Columns |")
    out.append("|---|---|--:|--:|")
    counts = {}
    for t in TABLE_ORDER:
        n, _ = csv_stats(t)
        counts[t] = n
        total += n
        out.append(f"| `{t}` | {GRAIN.get(t,'TODO')} | {n:,} | {len(tables[t]['cols'])} |")
    out.append(f"| **Total** | | **{total:,}** | |\n")

    for t in TABLE_ORDER:
        info = tables[t]
        n, nulls = csv_stats(t)
        out.append(f"\n---\n\n## `{t}`\n")
        out.append(f"**Grain:** {GRAIN.get(t,'TODO')}  ")
        out.append(f"**Rows:** {n:,}  ")
        out.append(f"**Primary key:** {', '.join('`'+c+'`' for c in info['pk']) or 'TODO'}")
        if len(info["pk"]) > 1:
            out.append("  *(natural composite key — no surrogate id)*")
        out.append("\n**Why this table exists:** TODO — one sentence tying it to a "
                   "Tier 1 or Tier 2 anchor.\n")
        out.append("| Column | Type | Null | Key | Nulls in data | Description |")
        out.append("|---|---|:-:|:-:|--:|---|")
        for cname, craw in info["cols"]:
            ctype, nullable, default = split_type(craw)
            key = ""
            if cname in info["pk"]:
                key = "PK"
            if cname in info["fks"]:
                key = (key + " FK") .strip()
            for u in info["uniques"]:
                if cname in u:
                    key = (key + " UQ").strip()
            nn = nulls.get(cname, 0)
            nullpct = f"{nn:,}" + (f" ({100*nn/n:.0f}%)" if n and nn else "")
            fkref = f" → `{info['fks'][cname]}`" if cname in info["fks"] else ""
            out.append(f"| `{cname}` | {ctype} | {'Y' if nullable else 'N'} | "
                       f"{key or '—'} | {nullpct or '0'} | TODO{fkref} |")
        if info["fks"]:
            out.append("\n**Foreign keys:** " + ", ".join(
                f"`{k}` → `{v}`" for k, v in info["fks"].items()))
        if info["checks"]:
            out.append("\n**Check constraints:**")
            for c in info["checks"]:
                out.append(f"- `{c}`")
    print("\n".join(out))


if __name__ == "__main__":
    main()
