import sqlite3
import json
from pathlib import Path


def main():
    repo_root = Path(__file__).resolve().parents[1]
    db_path = repo_root / "test.db"

    if not db_path.exists():
        print(f"DB not found: {db_path}")
        return

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, email, name, role, created_at, last_login FROM users ORDER BY email")
        rows = cur.fetchall()
        out = [dict(r) for r in rows]
        print(json.dumps(out, default=str))
    finally:
        conn.close()


if __name__ == '__main__':
    main()
