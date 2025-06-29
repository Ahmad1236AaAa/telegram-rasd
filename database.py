import sqlite3
from datetime import datetime

conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT,
    balance REAL DEFAULT 0
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    from_account TEXT,
    to_account TEXT,
    amount REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    note TEXT
)
""")
conn.commit()

def create_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
    conn.commit()

def add_account(user_id, name):
    cursor.execute("SELECT COUNT(*) FROM accounts WHERE user_id = ?", (user_id,))
    count = cursor.fetchone()[0]
    if count >= 5:
        return "❌ لا يمكنك إضافة أكثر من 5 حسابات."
    cursor.execute("INSERT INTO accounts (user_id, name) VALUES (?, ?)", (user_id, name))
    conn.commit()
    return f"✅ تم إضافة الحساب: {name}"

def add_transaction(user_id, from_acc, to_acc, amount, note=""):
    cursor.execute("SELECT name FROM accounts WHERE user_id = ? AND name = ?", (user_id, from_acc))
    if not cursor.fetchone():
        return "❌ حساب المصدر غير موجود."
    cursor.execute("SELECT name FROM accounts WHERE user_id = ? AND name = ?", (user_id, to_acc))
    if not cursor.fetchone():
        return "❌ حساب الوجهة غير موجود."
    
    cursor.execute("INSERT INTO transactions (user_id, from_account, to_account, amount, note) VALUES (?, ?, ?, ?, ?)",
                   (user_id, from_acc, to_acc, amount, note))
    # تحديث الأرصدة (بشكل مبسط)
    cursor.execute("UPDATE accounts SET balance = balance - ? WHERE user_id = ? AND name = ?", (amount, user_id, from_acc))
    cursor.execute("UPDATE accounts SET balance = balance + ? WHERE user_id = ? AND name = ?", (amount, user_id, to_acc))
    conn.commit()
    return f"💰 تمت المعاملة من {from_acc} إلى {to_acc} بقيمة {amount}$"
    cursor.execute("SELECT name, balance FROM accounts WHERE user_id = ?", (user_id,))
    accounts = cursor.fetchall()
    response = "📄 كشف الحساب الكلي:\n"
    total = 0
    for acc in accounts:
        response += f"🔹 {acc[0]}: {acc[1]:.2f}$\n"
        total += acc[1]
    response += f"============\n💼 المجموع: {total:.2f}$"
    return response
def get_user_accounts(user_id):
    cursor.execute("SELECT name FROM accounts WHERE user_id = ?", (user_id,))
    return [row[0] for row in cursor.fetchall()]

def get_latest_transactions(user_id, limit=10):
    cursor.execute("SELECT id FROM transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit))
    return [row[0] for row in cursor.fetchall()]




def get_debtors_report(user_id):
    cursor.execute("SELECT name, balance FROM accounts WHERE user_id = ? AND balance > 0", (user_id,))
    accounts = cursor.fetchall()
    response = "🔴 الحسابات التي تدين لنا:\n"
    total = 0
    for acc in accounts:
        response += f"🔹 {acc[0]}: {acc[1]:.2f}$\n"
        total += acc[1]
    response += f"============\n💼 المجموع: {total:.2f}$"
    return response

def get_creditors_report(user_id):
    cursor.execute("SELECT name, balance FROM accounts WHERE user_id = ? AND balance < 0", (user_id,))
    accounts = cursor.fetchall()
    response = "🟢 الحسابات التي نحن مدينون لها:\n"
    total = 0
    for acc in accounts:
        response += f"🔹 {acc[0]}: {abs(acc[1]):.2f}$\n"
        total += abs(acc[1])
    response += f"============\n💼 المجموع: {total:.2f}$"
    return response

def get_account_statement(user_id, account_name):
    cursor.execute("SELECT from_account, to_account, amount, note, created_at FROM transactions WHERE user_id = ? AND (from_account = ? OR to_account = ?) ORDER BY created_at DESC LIMIT 10", (user_id, account_name, account_name))
    transactions = cursor.fetchall()
    
    cursor.execute("SELECT balance FROM accounts WHERE user_id = ? AND name = ?", (user_id, account_name))
    balance = cursor.fetchone()[0] if cursor.fetchone() else 0

    response = f"📄 كشف حساب {account_name}:\n"
    for tx in transactions:
        date_obj = datetime.strptime(tx[4].split('.')[0], '%Y-%m-%d %H:%M:%S')
        formatted_date = date_obj.strftime('%d/%m - %I:%M %p')
        response += f"- {formatted_date} | من: {tx[0]} | إلى: {tx[1]} | مبلغ: {tx[2]:.2f}$ | ملاحظة: {tx[3]}\n"
    response += f"\n💼 الرصيد النهائي: {balance:.2f}$"
    return response

def get_latest_transactions_details(user_id, limit=10):
    cursor.execute("SELECT id, from_account, to_account, amount, note, created_at FROM transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit))
    transactions = cursor.fetchall()
    response = "📋 آخر 10 معاملات:\n"
    for tx in transactions:
        date_obj = datetime.strptime(tx[5].split(".")[0], 
                                       "%Y-%m-%d %H:%M:%S")
        formatted_date = date_obj.strftime("%d/%m - %I:%M %p")
        response += f"#{tx[0]} | {formatted_date} | من: {tx[1]} | إلى: {tx[2]} | مبلغ: {tx[3]:.2f}$ | ملاحظة: {tx[4]}\n"
    return response

def get_main_balance(user_id):
    cursor.execute("SELECT balance FROM accounts WHERE user_id = ? AND name = 'صندوق'", (user_id,))
    balance = cursor.fetchone()
    if balance:
        return f"💰 رصيد الخزنة الرئيسية (الصندوق): {balance[0]:.2f}$"
    else:
        return "❌ لم يتم العثور على حساب 'صندوق'. يرجى إضافته أولاً."




def get_transaction_by_id(user_id, transaction_id):
    cursor.execute("SELECT id, from_account, to_account, amount, note FROM transactions WHERE user_id = ? AND id = ?", (user_id, transaction_id))
    return cursor.fetchone()

def update_transaction(user_id, transaction_id, field, new_value):
    # Get current transaction details to revert balances if amount is changed
    cursor.execute("SELECT from_account, to_account, amount FROM transactions WHERE user_id = ? AND id = ?", (user_id, transaction_id))
    old_from_acc, old_to_acc, old_amount = cursor.fetchone()

    if field == 'amount':
        # Revert old transaction's effect
        cursor.execute("UPDATE accounts SET balance = balance + ? WHERE user_id = ? AND name = ?", (old_amount, user_id, old_from_acc))
        cursor.execute("UPDATE accounts SET balance = balance - ? WHERE user_id = ? AND name = ?", (old_amount, user_id, old_to_acc))
        # Apply new transaction's effect
        cursor.execute("UPDATE accounts SET balance = balance - ? WHERE user_id = ? AND name = ?", (new_value, user_id, old_from_acc))
        cursor.execute("UPDATE accounts SET balance = balance + ? WHERE user_id = ? AND name = ?", (new_value, user_id, old_to_acc))

    cursor.execute(f"UPDATE transactions SET {field} = ? WHERE user_id = ? AND id = ?", (new_value, user_id, transaction_id))
    conn.commit()
    return True

def delete_transaction_db(user_id, transaction_id):
    cursor.execute("SELECT from_account, to_account, amount FROM transactions WHERE user_id = ? AND id = ?", (user_id, transaction_id))
    transaction = cursor.fetchone()
    if transaction:
        from_acc, to_acc, amount = transaction
        cursor.execute("UPDATE accounts SET balance = balance + ? WHERE user_id = ? AND name = ?", (amount, user_id, from_acc))
        cursor.execute("UPDATE accounts SET balance = balance - ? WHERE user_id = ? AND name = ?", (amount, user_id, to_acc))
        cursor.execute("DELETE FROM transactions WHERE user_id = ? AND id = ?", (user_id, transaction_id))
        conn.commit()
        return True
    return False


