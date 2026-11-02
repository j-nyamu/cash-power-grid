"""Run the numbered SQL files in order against a MySQL server (for example Aiven).

Setup (PowerShell, from the folder that holds the .sql files):
    pip install pymysql sqlparse
    python run_sql.py

Add --reset to DROP the whole cashpower database first (development only; you must type RESET).

You are asked for the host, port, user and password. To skip the prompts, set
DB_HOST, DB_PORT, DB_USER and DB_PASSWORD as environment variables.
Optional: set DB_CA to the path of Aiven's CA certificate (ca.pem) to verify the server.
Never commit passwords or certificates.
"""
import getpass
import os
import pathlib
import sys

import pymysql
import sqlparse

FILES = [
    "00_database.sql",
    "01_auth.sql",
    "02_meters.sql",
    "03_usage.sql",
    "04_activity.sql",
    "05_changes.sql",
]

HERE = pathlib.Path(__file__).resolve().parent


def statements(path):
    """Split a SQL file into statements, skipping chunks that are only comments."""
    text = path.read_text(encoding="utf-8")
    for chunk in sqlparse.split(text):
        if sqlparse.format(chunk, strip_comments=True).strip():
            yield chunk.strip()


def main():
    files = list(FILES)
    if "--reset" in sys.argv:
        answer = input("This DROPS the whole cashpower database and all its data. Type RESET to continue: ")
        if answer.strip() != "RESET":
            sys.exit("Cancelled.")
        files = ["reset_dev.sql"] + files

    host = os.environ.get("DB_HOST") or input("Host: ").strip()
    port = int(os.environ.get("DB_PORT") or input("Port: ").strip())
    user = os.environ.get("DB_USER") or input("User [avnadmin]: ").strip() or "avnadmin"
    password = os.environ.get("DB_PASSWORD") or getpass.getpass("Password: ")
    ca = os.environ.get("DB_CA")

    # Aiven requires SSL. With a CA file the server is verified; without it the
    # connection is encrypted but the certificate is not checked.
    ssl = {"ca": ca} if ca else {"check_hostname": False}

    conn = pymysql.connect(host=host, port=port, user=user, password=password,
                           ssl=ssl, autocommit=True, connect_timeout=15)
    print("Connected.")

    for name in files:
        path = HERE / name
        if not path.exists():
            print(f"Missing file: {name}")
            sys.exit(1)
        print(f"Running {name}")
        with conn.cursor() as cur:
            for stmt in statements(path):
                try:
                    cur.execute(stmt)
                except Exception as exc:
                    print(f"\nFAILED in {name}: {exc}\n--- statement ---\n{stmt[:400]}")
                    sys.exit(1)

    with conn.cursor() as cur:
        cur.execute("USE cashpower")
        cur.execute("SHOW TABLES")
        tables = [row[0] for row in cur.fetchall()]
    print(f"\nDone. {len(tables)} tables in cashpower:")
    for t in tables:
        print(" -", t)


if __name__ == "__main__":
    main()