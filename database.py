import sqlite3

def init_db():
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def add_balance(user_id: int, amount: int, username: str = None):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    
    # User mavjudligini tekshiramiz
    cursor.execute("SELECT balance, username FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if row:
        new_balance = row[0] + amount
        if username:
            cursor.execute("UPDATE users SET balance = ?, username = ? WHERE user_id = ?", (new_balance, username, user_id))
        else:
            cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
    else:
        cursor.execute("INSERT INTO users (user_id, username, balance) VALUES (?, ?, ?)", (user_id, username, max(0, amount)))
        
    conn.commit()
    conn.close()

def get_balance(user_id: int) -> int:
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

# ID yoki Username orqali User ID ni topish
def get_user_id_by_input(user_input: str) -> int:
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    
    user_input = user_input.strip()
    
    # Agar faqat raqam kiritilgan bo'lsa (User ID deb qaraladi)
    if user_input.isdigit():
        conn.close()
        return int(user_input)
    
    # Agar @username kiritilgan bo'lsa
    if user_input.startswith("@"):
        user_input = user_input[1:]  # @ belgisini olib tashlaymiz
        
    cursor.execute("SELECT user_id FROM users WHERE LOWER(username) = LOWER(?)", (user_input,))
    row = cursor.fetchone()
    conn.close()
    
    return row[0] if row else None
