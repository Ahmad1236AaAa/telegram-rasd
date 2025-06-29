import sqlite3
from datetime import datetime, timedelta
import re

conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

# إنشاء الجداول
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
    balance REAL DEFAULT 0,
    account_type TEXT DEFAULT 'general',
    UNIQUE(user_id, name)
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    transaction_type TEXT,
    from_account TEXT,
    to_account TEXT,
    amount REAL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

def create_user(user_id):
    """إنشاء مستخدم جديد"""
    cursor.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
    conn.commit()

def validate_amount(amount_str):
    """التحقق من صحة المبلغ المدخل"""
    try:
        amount = float(amount_str)
        if amount <= 0:
            return None, "❌ المبلغ يجب أن يكون أكبر من الصفر"
        return amount, None
    except ValueError:
        return None, "❌ يرجى إدخال مبلغ صحيح (رقم)"

def validate_account_name(name):
    """التحقق من صحة اسم الحساب"""
    if not name or len(name.strip()) == 0:
        return False, "❌ اسم الحساب لا يمكن أن يكون فارغاً"
    
    if len(name.strip()) > 50:
        return False, "❌ اسم الحساب طويل جداً (الحد الأقصى 50 حرف)"
    
    # منع الأحرف الخاصة التي قد تسبب مشاكل
    if re.search(r'[<>:"/\\|?*]', name):
        return False, "❌ اسم الحساب يحتوي على أحرف غير مسموحة"
    
    return True, None

def detect_account_type(account_name):
    """تحديد نوع الحساب بناءً على الاسم"""
    name_lower = account_name.lower()
    
    # حسابات نقدية (أصول)
    cash_keywords = ['صندوق', 'نقد', 'كاش', 'خزنة', 'محفظة']
    bank_keywords = ['بنك', 'مصرف', 'حساب_جاري', 'توفير']
    
    # حسابات العملاء (لنا)
    customer_keywords = ['عميل', 'زبون', 'مشتري']
    
    # حسابات الموردين (لهم)
    supplier_keywords = ['مورد', 'بائع', 'مقاول']
    
    # حسابات المصاريف
    expense_keywords = ['مصروف', 'مصاريف', 'تكلفة', 'إيجار', 'راتب', 'كهرباء', 'ماء']
    
    # حسابات الإيرادات
    revenue_keywords = ['مبيعات', 'إيراد', 'دخل', 'ربح']
    
    for keyword in cash_keywords + bank_keywords:
        if keyword in name_lower:
            return 'asset'  # أصول
    
    for keyword in customer_keywords:
        if keyword in name_lower:
            return 'for_us'  # لنا
    
    for keyword in supplier_keywords:
        if keyword in name_lower:
            return 'for_them'  # لهم
    
    for keyword in expense_keywords:
        if keyword in name_lower:
            return 'expense'  # مصاريف
    
    for keyword in revenue_keywords:
        if keyword in name_lower:
            return 'revenue'  # إيرادات
    
    return 'general'  # عام

def add_account(user_id, name):
    """إضافة حساب جديد مع التحققات"""
    # التحقق من صحة اسم الحساب
    is_valid, error_msg = validate_account_name(name)
    if not is_valid:
        return error_msg
    
    name = name.strip()
    
    # التحقق من عدد الحسابات الحالية
    cursor.execute("SELECT COUNT(*) FROM accounts WHERE user_id = ?", (user_id,))
    count = cursor.fetchone()[0]
    if count >= 5:
        return "❌ لا يمكنك إضافة أكثر من 5 حسابات."
    
    # التحقق من عدم وجود حساب بنفس الاسم
    cursor.execute("SELECT COUNT(*) FROM accounts WHERE user_id = ? AND name = ?", (user_id, name))
    if cursor.fetchone()[0] > 0:
        return f"❌ يوجد حساب بالاسم '{name}' مسبقاً"
    
    # تحديد نوع الحساب
    account_type = detect_account_type(name)
    
    try:
        cursor.execute("INSERT INTO accounts (user_id, name, account_type) VALUES (?, ?, ?)", 
                      (user_id, name, account_type))
        conn.commit()
        
        # إضافة رمز لنوع الحساب
        type_emoji = {
            'asset': '💰',
            'for_us': '📈',
            'for_them': '📉',
            'expense': '💸',
            'revenue': '💵',
            'general': '📊'
        }
        
        return f"✅ تم إضافة الحساب: {name} {type_emoji.get(account_type, '📊')}"
    except sqlite3.Error as e:
        return f"❌ خطأ في إضافة الحساب: {str(e)}"

def update_account(user_id, old_name, new_name):
    """تعديل اسم حساب موجود"""
    # التحقق من صحة الاسم الجديد
    is_valid, error_msg = validate_account_name(new_name)
    if not is_valid:
        return error_msg
    
    new_name = new_name.strip()
    
    # التحقق من وجود الحساب القديم
    cursor.execute("SELECT COUNT(*) FROM accounts WHERE user_id = ? AND name = ?", (user_id, old_name))
    if cursor.fetchone()[0] == 0:
        return f"❌ الحساب '{old_name}' غير موجود"
    
    # التحقق من عدم وجود حساب بالاسم الجديد
    cursor.execute("SELECT COUNT(*) FROM accounts WHERE user_id = ? AND name = ?", (user_id, new_name))
    if cursor.fetchone()[0] > 0:
        return f"❌ يوجد حساب بالاسم '{new_name}' مسبقاً"
    
    try:
        # تحديد نوع الحساب الجديد
        new_account_type = detect_account_type(new_name)
        
        # تحديث اسم الحساب ونوعه
        cursor.execute("UPDATE accounts SET name = ?, account_type = ? WHERE user_id = ? AND name = ?", 
                      (new_name, new_account_type, user_id, old_name))
        
        # تحديث المعاملات المرتبطة
        cursor.execute("UPDATE transactions SET from_account = ? WHERE user_id = ? AND from_account = ?", 
                      (new_name, user_id, old_name))
        cursor.execute("UPDATE transactions SET to_account = ? WHERE user_id = ? AND to_account = ?", 
                      (new_name, user_id, old_name))
        
        conn.commit()
        
        type_emoji = {
            'asset': '💰',
            'for_us': '📈',
            'for_them': '📉',
            'expense': '💸',
            'revenue': '💵',
            'general': '📊'
        }
        
        return f"✅ تم تعديل الحساب من '{old_name}' إلى '{new_name}' {type_emoji.get(new_account_type, '📊')}"
    except sqlite3.Error as e:
        return f"❌ خطأ في تعديل الحساب: {str(e)}"

def delete_account(user_id, account_name):
    """حذف حساب وجميع المعاملات المرتبطة به"""
    # التحقق من وجود الحساب
    cursor.execute("SELECT COUNT(*) FROM accounts WHERE user_id = ? AND name = ?", (user_id, account_name))
    if cursor.fetchone()[0] == 0:
        return f"❌ الحساب '{account_name}' غير موجود"
    
    try:
        # حذف المعاملات المرتبطة بالحساب
        cursor.execute("DELETE FROM transactions WHERE user_id = ? AND (from_account = ? OR to_account = ?)", 
                      (user_id, account_name, account_name))
        deleted_transactions = cursor.rowcount
        
        # حذف الحساب
        cursor.execute("DELETE FROM accounts WHERE user_id = ? AND name = ?", (user_id, account_name))
        
        conn.commit()
        
        return f"✅ تم حذف الحساب '{account_name}' و {deleted_transactions} معاملة مرتبطة به"
    except sqlite3.Error as e:
        return f"❌ خطأ في حذف الحساب: {str(e)}"

def account_exists(user_id, account_name):
    """التحقق من وجود الحساب"""
    cursor.execute("SELECT COUNT(*) FROM accounts WHERE user_id = ? AND name = ?", (user_id, account_name))
    return cursor.fetchone()[0] > 0

def add_cash_in_transaction(user_id, to_account, amount_str, description=""):
    """إضافة معاملة دخول نقدي"""
    # التحقق من صحة المبلغ
    amount, error_msg = validate_amount(amount_str)
    if error_msg:
        return error_msg
    
    # التحقق من وجود الحساب
    if not account_exists(user_id, to_account):
        return f"❌ الحساب '{to_account}' غير موجود"
    
    try:
        # إضافة المعاملة
        cursor.execute("INSERT INTO transactions (user_id, transaction_type, to_account, amount, description) VALUES (?, ?, ?, ?, ?)",
                       (user_id, 'cash_in', to_account, amount, description))
        
        # تحديث الرصيد
        cursor.execute("UPDATE accounts SET balance = balance + ? WHERE user_id = ? AND name = ?", (amount, user_id, to_account))
        
        conn.commit()
        
        # الحصول على ID المعاملة
        transaction_id = cursor.lastrowid
        
        return f"✅ تمت معاملة الدخول #{transaction_id} إلى {to_account} بقيمة {amount:.2f} 💰"
    except sqlite3.Error as e:
        return f"❌ خطأ في إجراء المعاملة: {str(e)}"

def add_cash_out_transaction(user_id, from_account, amount_str, description=""):
    """إضافة معاملة خروج نقدي"""
    # التحقق من صحة المبلغ
    amount, error_msg = validate_amount(amount_str)
    if error_msg:
        return error_msg
    
    # التحقق من وجود الحساب
    if not account_exists(user_id, from_account):
        return f"❌ الحساب '{from_account}' غير موجود"
    
    try:
        # إضافة المعاملة
        cursor.execute("INSERT INTO transactions (user_id, transaction_type, from_account, amount, description) VALUES (?, ?, ?, ?, ?)",
                       (user_id, 'cash_out', from_account, amount, description))
        
        # تحديث الرصيد
        cursor.execute("UPDATE accounts SET balance = balance - ? WHERE user_id = ? AND name = ?", (amount, user_id, from_account))
        
        conn.commit()
        
        # الحصول على ID المعاملة
        transaction_id = cursor.lastrowid
        
        return f"✅ تمت معاملة الخروج #{transaction_id} من {from_account} بقيمة {amount:.2f} 💸"
    except sqlite3.Error as e:
        return f"❌ خطأ في إجراء المعاملة: {str(e)}"

def add_transfer_transaction(user_id, from_acc, to_acc, amount_str, description=""):
    """إضافة معاملة تحويل بين الحسابات"""
    # التحقق من صحة المبلغ
    amount, error_msg = validate_amount(amount_str)
    if error_msg:
        return error_msg
    
    # التحقق من وجود الحسابات
    if not account_exists(user_id, from_acc):
        return f"❌ الحساب '{from_acc}' غير موجود"
    
    if not account_exists(user_id, to_acc):
        return f"❌ الحساب '{to_acc}' غير موجود"
    
    # التحقق من أن الحساب المرسل والمستقبل مختلفان
    if from_acc == to_acc:
        return "❌ لا يمكن إجراء معاملة من نفس الحساب إلى نفسه"
    
    try:
        # إضافة المعاملة
        cursor.execute("INSERT INTO transactions (user_id, transaction_type, from_account, to_account, amount, description) VALUES (?, ?, ?, ?, ?, ?)",
                       (user_id, 'transfer', from_acc, to_acc, amount, description))
        
        # تحديث الأرصدة
        cursor.execute("UPDATE accounts SET balance = balance - ? WHERE user_id = ? AND name = ?", (amount, user_id, from_acc))
        cursor.execute("UPDATE accounts SET balance = balance + ? WHERE user_id = ? AND name = ?", (amount, user_id, to_acc))
        
        conn.commit()
        
        # الحصول على ID المعاملة
        transaction_id = cursor.lastrowid
        
        return f"✅ تمت معاملة التحويل #{transaction_id} من {from_acc} إلى {to_acc} بقيمة {amount:.2f} 🔄"
    except sqlite3.Error as e:
        return f"❌ خطأ في إجراء المعاملة: {str(e)}"

def get_transaction_by_id(user_id, transaction_id):
    """الحصول على معاملة محددة بواسطة ID"""
    cursor.execute("""
        SELECT id, transaction_type, from_account, to_account, amount, description, created_at 
        FROM transactions 
        WHERE user_id = ? AND id = ?
    """, (user_id, transaction_id))
    return cursor.fetchone()

def update_transaction(user_id, transaction_id, transaction_type, from_account, to_account, amount_str, description=""):
    """تعديل معاملة موجودة"""
    # التحقق من صحة المبلغ
    amount, error_msg = validate_amount(amount_str)
    if error_msg:
        return error_msg
    
    # الحصول على المعاملة القديمة
    old_transaction = get_transaction_by_id(user_id, transaction_id)
    if not old_transaction:
        return f"❌ المعاملة #{transaction_id} غير موجودة"
    
    old_id, old_type, old_from, old_to, old_amount, old_desc, old_date = old_transaction
    
    try:
        # التراجع عن تأثير المعاملة القديمة على الأرصدة
        if old_type == 'cash_in' and old_to:
            cursor.execute("UPDATE accounts SET balance = balance - ? WHERE user_id = ? AND name = ?", 
                          (old_amount, user_id, old_to))
        elif old_type == 'cash_out' and old_from:
            cursor.execute("UPDATE accounts SET balance = balance + ? WHERE user_id = ? AND name = ?", 
                          (old_amount, user_id, old_from))
        elif old_type == 'transfer' and old_from and old_to:
            cursor.execute("UPDATE accounts SET balance = balance + ? WHERE user_id = ? AND name = ?", 
                          (old_amount, user_id, old_from))
            cursor.execute("UPDATE accounts SET balance = balance - ? WHERE user_id = ? AND name = ?", 
                          (old_amount, user_id, old_to))
        
        # التحقق من وجود الحسابات الجديدة
        if transaction_type == 'cash_in':
            if not account_exists(user_id, to_account):
                return f"❌ الحساب '{to_account}' غير موجود"
            from_account = None
        elif transaction_type == 'cash_out':
            if not account_exists(user_id, from_account):
                return f"❌ الحساب '{from_account}' غير موجود"
            to_account = None
        else:  # transfer
            if not account_exists(user_id, from_account):
                return f"❌ الحساب '{from_account}' غير موجود"
            if not account_exists(user_id, to_account):
                return f"❌ الحساب '{to_account}' غير موجود"
            if from_account == to_account:
                return "❌ لا يمكن إجراء معاملة من نفس الحساب إلى نفسه"
        
        # تحديث المعاملة
        cursor.execute("""
            UPDATE transactions 
            SET transaction_type = ?, from_account = ?, to_account = ?, amount = ?, description = ?
            WHERE user_id = ? AND id = ?
        """, (transaction_type, from_account, to_account, amount, description, user_id, transaction_id))
        
        # تطبيق تأثير المعاملة الجديدة على الأرصدة
        if transaction_type == 'cash_in':
            cursor.execute("UPDATE accounts SET balance = balance + ? WHERE user_id = ? AND name = ?", 
                          (amount, user_id, to_account))
        elif transaction_type == 'cash_out':
            cursor.execute("UPDATE accounts SET balance = balance - ? WHERE user_id = ? AND name = ?", 
                          (amount, user_id, from_account))
        else:  # transfer
            cursor.execute("UPDATE accounts SET balance = balance - ? WHERE user_id = ? AND name = ?", 
                          (amount, user_id, from_account))
            cursor.execute("UPDATE accounts SET balance = balance + ? WHERE user_id = ? AND name = ?", 
                          (amount, user_id, to_account))
        
        conn.commit()
        
        return f"✅ تم تعديل المعاملة #{transaction_id} بنجاح"
    except sqlite3.Error as e:
        conn.rollback()
        return f"❌ خطأ في تعديل المعاملة: {str(e)}"

def delete_transaction(user_id, transaction_id):
    """حذف معاملة وإلغاء تأثيرها على الأرصدة"""
    # الحصول على المعاملة
    transaction = get_transaction_by_id(user_id, transaction_id)
    if not transaction:
        return f"❌ المعاملة #{transaction_id} غير موجودة"
    
    trans_id, trans_type, from_acc, to_acc, amount, description, created_at = transaction
    
    try:
        # إلغاء تأثير المعاملة على الأرصدة
        if trans_type == 'cash_in' and to_acc:
            cursor.execute("UPDATE accounts SET balance = balance - ? WHERE user_id = ? AND name = ?", 
                          (amount, user_id, to_acc))
        elif trans_type == 'cash_out' and from_acc:
            cursor.execute("UPDATE accounts SET balance = balance + ? WHERE user_id = ? AND name = ?", 
                          (amount, user_id, from_acc))
        elif trans_type == 'transfer' and from_acc and to_acc:
            cursor.execute("UPDATE accounts SET balance = balance + ? WHERE user_id = ? AND name = ?", 
                          (amount, user_id, from_acc))
            cursor.execute("UPDATE accounts SET balance = balance - ? WHERE user_id = ? AND name = ?", 
                          (amount, user_id, to_acc))
        
        # حذف المعاملة
        cursor.execute("DELETE FROM transactions WHERE user_id = ? AND id = ?", (user_id, transaction_id))
        
        conn.commit()
        
        return f"✅ تم حذف المعاملة #{transaction_id} وإلغاء تأثيرها على الأرصدة"
    except sqlite3.Error as e:
        conn.rollback()
        return f"❌ خطأ في حذف المعاملة: {str(e)}"

def get_user_accounts(user_id):
    """الحصول على حسابات المستخدم مع أنواعها"""
    cursor.execute("SELECT name, balance, account_type FROM accounts WHERE user_id = ? ORDER BY name", (user_id,))
    return cursor.fetchall()

def get_user_transactions(user_id, limit=10):
    """الحصول على معاملات المستخدم"""
    cursor.execute("""
        SELECT id, transaction_type, from_account, to_account, amount, description, created_at 
        FROM transactions 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ?
    """, (user_id, limit))
    return cursor.fetchall()

def format_datetime(datetime_str):
    """تنسيق التاريخ والوقت ليكون أوضح"""
    try:
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return datetime_str

def format_balance_status(balance):
    """تنسيق حالة الرصيد (لنا/لهم)"""
    if balance > 0:
        return f"{balance:.2f} (لهم) 💚"
    elif balance < 0:
        return f"{abs(balance):.2f} (لنا) 🔵"
    else:
        return f"{balance:.2f} (متوازن) ⚖️"

def calculate_advanced_balances(user_id):
    """حساب الأرصدة المتقدمة بناءً على أنواع الحسابات"""
    accounts = get_user_accounts(user_id)
    
    balances = {
        'assets': 0,           # الأصول (نقد، بنوك)
        'for_us': 0,          # لنا (أرصدة سالبة)
        'for_them': 0,        # لهم (أرصدة موجبة)
        'expenses': 0,         # المصاريف
        'revenues': 0,         # الإيرادات
        'general': 0,          # عام
        'total': 0,
        'total_cash': 0,       # إجمالي النقد
        'accounts_by_type': {
            'asset': [],
            'for_us': [],
            'for_them': [],
            'expense': [],
            'revenue': [],
            'general': []
        }
    }
    
    for acc_name, balance, acc_type in accounts:
        balances['total'] += balance
        balances['accounts_by_type'][acc_type].append((acc_name, balance))
        
        if acc_type == 'asset':
            balances['assets'] += balance
            balances['total_cash'] += balance
        elif acc_type == 'for_us':
            if balance < 0:
                balances['for_us'] += abs(balance)
            else:
                balances['for_them'] += balance
        elif acc_type == 'for_them':
            if balance < 0:
                balances['for_us'] += abs(balance)
            else:
                balances['for_them'] += balance
        elif acc_type == 'expense':
            balances['expenses'] += abs(balance) if balance < 0 else balance
        elif acc_type == 'revenue':
            balances['revenues'] += balance
        else:
            balances['general'] += balance
    
    return balances

def get_current_cash_balance(user_id):
    """الحصول على الرصيد النقدي الحالي"""
    cursor.execute("""
        SELECT SUM(balance) 
        FROM accounts 
        WHERE user_id = ? AND account_type = 'asset'
    """, (user_id,))
    
    result = cursor.fetchone()[0]
    return result if result is not None else 0

def get_financial_summary(user_id):
    """إنشاء ملخص مالي متقدم"""
    balances = calculate_advanced_balances(user_id)
    
    if not any(balances['accounts_by_type'].values()):
        return "📄 لا توجد حسابات مسجلة بعد.\nاستخدم @حساب [اسم الحساب] لإضافة حساب جديد."
    
    summary = "📊 **الملخص المالي الشامل**\n"
    summary += "=" * 35 + "\n\n"
    
    # الأصول النقدية
    if balances['accounts_by_type']['asset']:
        summary += "💰 **الأصول النقدية:**\n"
        for acc_name, balance in balances['accounts_by_type']['asset']:
            summary += f"   • {acc_name}: {format_balance_status(balance)}\n"
        summary += f"   **المجموع:** {balances['assets']:.2f}\n\n"
    
    # الحسابات (لنا)
    if balances['accounts_by_type']['for_us']:
        summary += "📈 **الحسابات (لنا/لهم):**\n"
        for acc_name, balance in balances['accounts_by_type']['for_us']:
            summary += f"   • {acc_name}: {format_balance_status(balance)}\n"
        summary += "\n"
    
    # الحسابات (لهم)
    if balances['accounts_by_type']['for_them']:
        summary += "📉 **حسابات الموردين:**\n"
        for acc_name, balance in balances['accounts_by_type']['for_them']:
            summary += f"   • {acc_name}: {format_balance_status(balance)}\n"
        summary += "\n"
    
    # الإيرادات
    if balances['accounts_by_type']['revenue']:
        summary += "💵 **الإيرادات:**\n"
        for acc_name, balance in balances['accounts_by_type']['revenue']:
            summary += f"   • {acc_name}: {balance:.2f}\n"
        summary += f"   **المجموع:** {balances['revenues']:.2f}\n\n"
    
    # المصاريف
    if balances['accounts_by_type']['expense']:
        summary += "💸 **المصاريف:**\n"
        for acc_name, balance in balances['accounts_by_type']['expense']:
            summary += f"   • {acc_name}: {balance:.2f}\n"
        summary += f"   **المجموع:** {balances['expenses']:.2f}\n\n"
    
    # الحسابات العامة
    if balances['accounts_by_type']['general']:
        summary += "📊 **حسابات عامة:**\n"
        for acc_name, balance in balances['accounts_by_type']['general']:
            summary += f"   • {acc_name}: {format_balance_status(balance)}\n"
        summary += f"   **المجموع:** {balances['general']:.2f}\n\n"
    
    # الملخص النهائي
    summary += "🎯 **الملخص النهائي:**\n"
    summary += "-" * 25 + "\n"
    summary += f"💰 إجمالي النقد: {balances['total_cash']:.2f}\n"
    summary += f"📈 إجمالي لنا: {balances['for_us']:.2f}\n"
    summary += f"📉 إجمالي لهم: {balances['for_them']:.2f}\n"
    summary += f"💵 إجمالي الإيرادات: {balances['revenues']:.2f}\n"
    summary += f"💸 إجمالي المصاريف: {balances['expenses']:.2f}\n"
    summary += f"📊 **الرصيد الإجمالي:** {balances['total']:.2f}\n"
    
    # تحليل الوضع المالي
    net_worth = balances['assets'] + balances['for_us'] - balances['for_them']
    summary += f"💎 **صافي الثروة:** {net_worth:.2f}\n"
    
    if net_worth > 0:
        summary += "✅ الوضع المالي: إيجابي 💚"
    elif net_worth < 0:
        summary += "⚠️ الوضع المالي: سلبي 🔴"
    else:
        summary += "⚖️ الوضع المالي: متوازن 🟡"
    
    return summary

def get_report(user_id):
    """إنشاء تقرير مبسط للمستخدم"""
    return get_financial_summary(user_id)

def get_accounts_list(user_id):
    """الحصول على قائمة الحسابات مع أرصدتها وأنواعها"""
    accounts = get_user_accounts(user_id)
    
    if not accounts:
        return "📋 لا توجد حسابات مسجلة بعد.\nاستخدم @حساب [اسم الحساب] لإضافة حساب جديد."
    
    response = "📋 **قائمة الحسابات:**\n"
    response += "=" * 25 + "\n"
    
    type_emoji = {
        'asset': '💰',
        'for_us': '📈',
        'for_them': '📉',
        'expense': '💸',
        'revenue': '💵',
        'general': '📊'
    }
    
    for i, (acc_name, balance, acc_type) in enumerate(accounts, 1):
        emoji = type_emoji.get(acc_type, '📊')
        balance_status = format_balance_status(balance)
        response += f"{i}. {acc_name} {emoji}: {balance_status}\n"
    
    response += f"\n📊 المجموع: {len(accounts)}/5 حسابات"
    
    return response

def get_transactions_history(user_id, limit=10):
    """الحصول على سجل المعاملات المحسن"""
    transactions = get_user_transactions(user_id, limit)
    
    if not transactions:
        return "📝 لا توجد معاملات مسجلة بعد.\nاستخدم @معاملة [من] [إلى] [المبلغ] لإضافة معاملة."
    
    response = f"📝 **آخر {len(transactions)} معاملات:**\n"
    response += "=" * 35 + "\n"
    
    for trans_id, trans_type, from_acc, to_acc, amount, description, created_at in transactions:
        formatted_date = format_datetime(created_at)
        response += f"🔹 **المعاملة #{trans_id}**\n"
        response += f"📅 {formatted_date}\n"
        
        if trans_type == 'cash_in':
            response += f"💰 دخول نقدي إلى {to_acc}: {amount:.2f}\n"
        elif trans_type == 'cash_out':
            response += f"💸 خروج نقدي من {from_acc}: {amount:.2f}\n"
        else:  # transfer
            response += f"🔄 تحويل من {from_acc} إلى {to_acc}: {amount:.2f}\n"
        
        if description:
            response += f"📝 {description}\n"
        response += "-" * 30 + "\n"
    
    return response

def get_monthly_report(user_id):
    """تقرير شهري للمعاملات"""
    # الحصول على معاملات الشهر الحالي
    current_date = datetime.now()
    first_day = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    cursor.execute("""
        SELECT transaction_type, from_account, to_account, amount, created_at
        FROM transactions 
        WHERE user_id = ? AND created_at >= ?
        ORDER BY created_at DESC
    """, (user_id, first_day.isoformat()))
    
    monthly_transactions = cursor.fetchall()
    
    if not monthly_transactions:
        return f"📅 **تقرير شهر {current_date.strftime('%m/%Y')}**\n\nلا توجد معاملات هذا الشهر."
    
    total_amount = sum(trans[3] for trans in monthly_transactions)
    cash_in_total = sum(trans[3] for trans in monthly_transactions if trans[0] == 'cash_in')
    cash_out_total = sum(trans[3] for trans in monthly_transactions if trans[0] == 'cash_out')
    transfer_total = sum(trans[3] for trans in monthly_transactions if trans[0] == 'transfer')
    
    response = f"📅 **تقرير شهر {current_date.strftime('%m/%Y')}**\n"
    response += "=" * 30 + "\n"
    response += f"📊 عدد المعاملات: {len(monthly_transactions)}\n"
    response += f"💰 إجمالي الدخول النقدي: {cash_in_total:.2f}\n"
    response += f"💸 إجمالي الخروج النقدي: {cash_out_total:.2f}\n"
    response += f"🔄 إجمالي التحويلات: {transfer_total:.2f}\n"
    response += f"📈 متوسط المعاملة: {total_amount/len(monthly_transactions):.2f}\n\n"
    
    response += "📝 **المعاملات:**\n"
    for trans_type, from_acc, to_acc, amount, created_at in monthly_transactions[:5]:  # أول 5 معاملات
        formatted_date = format_datetime(created_at)
        if trans_type == 'cash_in':
            response += f"• {formatted_date}: دخول إلى {to_acc} ({amount:.2f})\n"
        elif trans_type == 'cash_out':
            response += f"• {formatted_date}: خروج من {from_acc} ({amount:.2f})\n"
        else:
            response += f"• {formatted_date}: {from_acc} → {to_acc} ({amount:.2f})\n"
    
    if len(monthly_transactions) > 5:
        response += f"... و {len(monthly_transactions) - 5} معاملات أخرى"
    
    return response

