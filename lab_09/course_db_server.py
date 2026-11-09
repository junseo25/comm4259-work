#!/usr/bin/env python3
"""COMM 4259 course database: a small MCP server for Lab 9.

It loads WineQuality.csv (in the same folder as this file) into a read-only
SQLite database in memory, and offers Claude Code three tools:
    list_tables     the tables and their row counts
    describe_table  the columns of one table, with three example rows
    run_query       one read-only SQL query (SELECT or WITH), at most 200 rows

It uses only the Python standard library: nothing to install. It does not use
the network, and it cannot change any file. Column names with spaces are stored
with underscores (for example, "fixed acidity" becomes fixed_acidity).

Add it from your comm4259-work folder:
    claude mcp add course-db -- python lab_09/course_db_server.py
"""
import csv
import json
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TABLES = {"wine": HERE / "WineQuality.csv"}
MAX_ROWS = 200
PROTOCOLS = ["2025-06-18", "2025-03-26", "2024-11-05"]


# Build the database in memory from the CSV files
def number_or_text(values):
    try:
        [float(v) for v in values if v != ""]
        return "REAL"
    except ValueError:
        return "TEXT"


def build_db():
    db = sqlite3.connect(":memory:")
    for table, path in TABLES.items():
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
        names = [h.strip().replace(" ", "_") for h in rows[0]]
        data = rows[1:]
        types = [number_or_text([r[i] for r in data]) for i in range(len(names))]
        cols = ", ".join(f'"{n}" {t}' for n, t in zip(names, types))
        db.execute(f'CREATE TABLE "{table}" ({cols})')
        convert = [float if t == "REAL" else str for t in types]
        db.executemany(f'INSERT INTO "{table}" VALUES ({", ".join("?" * len(names))})',
                       [[None if v == "" else c(v) for c, v in zip(convert, r)] for r in data])
    db.commit()
    db.execute("PRAGMA query_only = ON")   # from here on, nothing can change the data
    return db


DB = build_db()


# The three tools
def as_table(cursor, rows):
    header = [d[0] for d in cursor.description]
    lines = [",".join(header)] + [",".join("" if v is None else str(v) for v in r) for r in rows]
    return "\n".join(lines)


def list_tables(args):
    out = []
    for table in TABLES:
        n = DB.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        out.append(f"{table}: {n} rows")
    return "\n".join(out)


def describe_table(args):
    table = args.get("table", "")
    if table not in TABLES:
        raise ValueError(f"Unknown table {table!r}. Tables: {', '.join(TABLES)}")
    cols = DB.execute(f'PRAGMA table_info("{table}")').fetchall()
    text = "Columns:\n" + "\n".join(f"- {c[1]} ({c[2]})" for c in cols)
    cur = DB.execute(f'SELECT * FROM "{table}" LIMIT 3')
    return text + "\n\nExample rows:\n" + as_table(cur, cur.fetchall())


def run_query(args):
    sql = args.get("sql", "").strip().rstrip(";")
    if not sql.lower().startswith(("select", "with")):
        raise ValueError("Only one read-only query that starts with SELECT or WITH is allowed.")
    if ";" in sql:
        raise ValueError("Send one query at a time.")
    cur = DB.execute(sql)
    rows = cur.fetchmany(MAX_ROWS + 1)
    note = f"\n(showing the first {MAX_ROWS} rows)" if len(rows) > MAX_ROWS else ""
    return as_table(cur, rows[:MAX_ROWS]) + note


TOOLS = {
    "list_tables": (list_tables, "List the tables in the COMM 4259 course database and their row counts.",
                    {"type": "object", "properties": {}}),
    "describe_table": (describe_table, "Show the columns of one table, with their types and three example rows.",
                       {"type": "object", "properties": {"table": {"type": "string", "description": "Table name, for example wine"}},
                        "required": ["table"]}),
    "run_query": (run_query, "Run one read-only SQLite query (SELECT or WITH) and return at most 200 rows as CSV text.",
                  {"type": "object", "properties": {"sql": {"type": "string", "description": "One SQLite SELECT query"}},
                   "required": ["sql"]}),
}


# MCP messages: one JSON-RPC message per line on standard input and output
def handle(msg):
    method, params = msg.get("method"), msg.get("params") or {}
    if method == "initialize":
        asked = params.get("protocolVersion")
        return {"protocolVersion": asked if asked in PROTOCOLS else PROTOCOLS[0],
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "course-db", "version": "1.0"}}
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": [{"name": n, "description": d, "inputSchema": s} for n, (_, d, s) in TOOLS.items()]}
    if method == "tools/call":
        name = params.get("name")
        if name not in TOOLS:
            raise LookupError(f"Unknown tool {name!r}")
        try:
            return {"content": [{"type": "text", "text": TOOLS[name][0](params.get("arguments") or {})}], "isError": False}
        except (ValueError, sqlite3.Error) as e:
            return {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}
    raise LookupError(f"Method not found: {method}")


def main():
    for line in sys.stdin.buffer:
        if not line.strip():
            continue
        msg = json.loads(line)
        if "id" not in msg:          # a notification: no reply
            continue
        try:
            reply = {"jsonrpc": "2.0", "id": msg["id"], "result": handle(msg)}
        except LookupError as e:
            reply = {"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32601, "message": str(e)}}
        sys.stdout.buffer.write((json.dumps(reply) + "\n").encode("utf-8"))
        sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
