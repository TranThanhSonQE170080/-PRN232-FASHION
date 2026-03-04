import sqlite3
from pathlib import Path


def main():
    repo_root = Path(__file__).resolve().parents[1]
    db_path = repo_root / "test.db"

    if not db_path.exists():
        print(f"DB not found: {db_path}")
        return

    email = "admin@gmail.com"

    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, role FROM users WHERE lower(email)=?", (email.lower(),))
        row = cur.fetchone()
        if not row:
            print(f"User not found: {email}")
            return

        user_id, current_role = row
        if current_role == "admin":
            print(f"User {email} is already admin (id={user_id}).")
            return

        cur.execute("UPDATE users SET role = ? WHERE id = ?", ("admin", user_id))
        conn.commit()
        print(f"Updated user {email} ({user_id}) role: {current_role} -> admin")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
