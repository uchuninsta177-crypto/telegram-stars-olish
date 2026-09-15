import sqlite3

DB_PATH = "bot.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 0
            )
        """
        )
        conn.commit()


def add_balance(user_id: int, amount: int, username: str = None):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT balance, username FROM users WHERE user_id = ?", (user_id,)
        )
        row = cursor.fetchone()

        if username and username.startswith("@"):
            username = username[1:]

        if row:
            new_balance = max(0, row[0] + amount)
            if username:
                cursor.execute(
                    "UPDATE users SET balance = ?, username = ? WHERE user_id = ?",
                    (new_balance, username, user_id),
                )
            else:
                cursor.execute(
                    "UPDATE users SET balance = ? WHERE user_id = ?",
                    (new_balance, user_id),
                )
        else:
            cursor.execute(
                "INSERT INTO users (user_id, username, balance) VALUES (?, ?, ?)",
                (user_id, username, max(0, amount)),
            )

        conn.commit()


def get_balance(user_id: int) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT balance FROM users WHERE user_id = ?", (user_id,)
        )
        row = cursor.fetchone()
        return row[0] if row else 0


def get_user_id_by_input(user_input: str):
    user_input = user_input.strip()

    with get_connection() as conn:
        cursor = conn.cursor()

        if user_input.isdigit():
            user_id = int(user_input)
            cursor.execute(
                "SELECT user_id FROM users WHERE user_id = ?", (user_id,)
            )
            row = cursor.fetchone()
            return row[0] if row else None

        if user_input.startswith("@"):
            user_input = user_input[1:]

        cursor.execute(
            "SELECT user_id FROM users WHERE LOWER(username) = LOWER(?)",
            (user_input,),
        )
        row = cursor.fetchone()

        return row[0] if row else None
