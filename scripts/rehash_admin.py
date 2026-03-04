import os
import sqlite3
from pathlib import Path

from backend.core.security import hash_password


def main():
    repo_root = Path(__file__).resolve().parents[1]
    # repo_root points to the `backend` folder; test.db lives directly inside it
    db_path = repo_root / "test.db"

    if not db_path.exists():
        print(f"DB not found: {db_path}")
        return

    email = "admin@gmail.com"
    new_password = "Password123!"

    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, email FROM users WHERE lower(email)=?", (email.lower(),))
        row = cur.fetchone()
        if not row:
            print(f"User not found: {email}")
            return

        user_id = row[0]
        new_hash = hash_password(new_password)

        cur.execute("UPDATE users SET hashed_password=? WHERE id=?", (new_hash, user_id))
        conn.commit()

        print(f"Updated user {email} ({user_id}) with new hashed password.")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
