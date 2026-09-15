import sqlite3

def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            username TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def add_balance(user_id, amount, username=None):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if row:
        new_balance = row[0] + amount
        cursor.execute("UPDATE users SET balance = ?, username = COALESCE(?, username) WHERE user_id = ?", (new_balance, username, user_id))
    else:
        cursor.execute("INSERT INTO users (user_id, balance, username) VALUES (?, ?, ?)", (user_id, max(0, amount), username))
    
    conn.commit()
    conn.close()

def get_user_id_by_input(user_input):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    
    user_input = user_input.strip()
    if user_input.isdigit():
        conn.close()
        return int(user_input)
    
    clean_username = user_input.replace("@", "")
    cursor.execute("SELECT user_id FROM users WHERE LOWER(username) = LOWER(?)", (clean_username,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None
