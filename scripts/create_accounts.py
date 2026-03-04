import sqlite3
from pathlib import Path
from typing import List, Dict

from backend.core.security import hash_password


ACCOUNTS: List[Dict[str, str]] = [
    {"email": "user@example.com", "password": "Password123!", "role": "user"},
    {"email": "admin2@example.com", "password": "AdminPass123!", "role": "admin"},
]


def main():
    repo_root = Path(__file__).resolve().parents[1]
    db_path = repo_root / "test.db"

    if not db_path.exists():
        print(f"DB not found: {db_path}")
        return

    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        for acct in ACCOUNTS:
            email = acct["email"].lower().strip()
            cur.execute("SELECT id, role FROM users WHERE lower(email)=?", (email,))
            row = cur.fetchone()
            if row:
                user_id, current_role = row
                # update role and hashed_password
                new_hash = hash_password(acct["password"])
                cur.execute("UPDATE users SET role=?, hashed_password=? WHERE id=?", (acct["role"], new_hash, user_id))
                print(f"Updated existing user {email} ({user_id}) -> role={acct['role']}")
            else:
                import uuid

                user_id = str(uuid.uuid4())
                new_hash = hash_password(acct["password"])
                cur.execute(
                    "INSERT INTO users (id, email, name, role, hashed_password) VALUES (?, ?, ?, ?, ?)",
                    (user_id, email, None, acct["role"], new_hash),
                )
                print(f"Created user {email} ({user_id}) role={acct['role']}")

        conn.commit()
    finally:
        conn.close()


if __name__ == '__main__':
    main()
