import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 0
)
""")

conn.commit()
conn.close()


def get_balance(user_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT balance FROM users WHERE user_id=?",
        (user_id,)
    )

    row = cursor.fetchone()
    conn.close()

    if row:
        return row[0]

    return 0


def add_balance(user_id, amount):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO users(user_id, balance)
        VALUES(?, 0)
        """,
        (user_id,)
    )

    cursor.execute(
        """
        UPDATE users
        SET balance = balance + ?
        WHERE user_id=?
        """,
        (amount, user_id)
    )

    conn.commit()
    conn.close()


print("Database tayyor!")