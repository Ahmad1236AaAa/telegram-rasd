import re
from telebot import types
from database_enhanced import (
    create_user, add_account, add_cash_in_transaction, add_cash_out_transaction,
    add_transfer_transaction, get_report, get_accounts_list, get_transactions_history,
    get_financial_summary, get_monthly_report, get_current_cash_balance, get_user_accounts,
    delete_account, delete_transaction, update_transaction, get_transaction_by_id
)

def extract_accounts_from_text(text):
    """استخراج أسماء الحسابات من النص (المسبوقة بـ @)"""
    # البحث عن الكلمات المسبوقة بـ @
    accounts = re.findall(r'@(\w+(?:_\w+)*)', text)
    return accounts

def parse_transaction_text(text):
    """تحليل نص المعاملة لفهم نوعها واتجاهها"""
    text_lower = text.lower()
    
    # استخراج الحسابات
    accounts = extract_accounts_from_text(text)
    
    # استخراج المبلغ
    amount_match = re.search(r'\b(\d+(?:\.\d+)?)\b', text)
    amount = amount_match.group(1) if amount_match else None
    
    # كلمات الدخول
    cash_in_keywords = ['دخول', 'إيداع', 'وصل', 'تحصيل', 'قبض']
    # كلمات الخروج
    cash_out_keywords = ['خروج', 'سحب', 'دفع', 'صرف', 'سداد']
    # كلمات التحويل
    transfer_keywords = ['تحويل', 'نقل', 'من', 'إلى', 'ل']
    
    # تحديد نوع المعاملة
    transaction_type = 'transfer'  # افتراضي
    
    # فحص كلمات الدخول
    for keyword in cash_in_keywords:
        if keyword in text_lower:
            transaction_type = 'cash_in'
            break
    
    # فحص كلمات الخروج
    for keyword in cash_out_keywords:
        if keyword in text_lower:
            transaction_type = 'cash_out'
            break
    
    # تحليل الاتجاه بناءً على الكلمات
    from_account = None
    to_account = None
    
    if transaction_type == 'cash_in':
        # البحث عن الحساب المستقبل
        if 'إلى' in text_lower or 'ل' in text_lower:
            # البحث عن الحساب بعد "إلى" أو "ل"
            for i, word in enumerate(text.split()):
                if word.lower() in ['إلى', 'ل'] and i + 1 < len(text.split()):
                    next_word = text.split()[i + 1]
                    if next_word.startswith('@'):
                        to_account = next_word[1:]
                        break
        
        # إذا لم نجد، نأخذ أول حساب
        if not to_account and accounts:
            to_account = accounts[0]
    
    elif transaction_type == 'cash_out':
        # البحث عن الحساب المرسل
        if 'من' in text_lower:
            # البحث عن الحساب بعد "من"
            for i, word in enumerate(text.split()):
                if word.lower() == 'من' and i + 1 < len(text.split()):
                    next_word = text.split()[i + 1]
                    if next_word.startswith('@'):
                        from_account = next_word[1:]
                        break
        
        # إذا لم نجد، نأخذ أول حساب
        if not from_account and accounts:
            from_account = accounts[0]
    
    else:  # transfer
        # البحث عن الحساب المرسل والمستقبل
        if len(accounts) >= 2:
            from_account = accounts[0]
            to_account = accounts[1]
        elif len(accounts) == 1:
            # محاولة تحديد الاتجاه من السياق
            if 'من' in text_lower:
                from_account = accounts[0]
            elif 'إلى' in text_lower or 'ل' in text_lower:
                to_account = accounts[0]
    
    return {
        'type': transaction_type,
        'from_account': from_account,
        'to_account': to_account,
        'amount': amount,
        'accounts': accounts
    }

def create_commands_inline_keyboard():
    """إنشاء لوحة مفاتيح inline للأوامر الرئيسية"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # الأوامر الأساسية
    commands = [
        ("💰 حساب", "cmd_حساب"),
        ("💸 معاملة", "cmd_معاملة"),
        ("📊 كشف", "cmd_كشف"),
        ("📋 الحسابات", "cmd_الحسابات"),
        ("📝 معاملاتي", "cmd_معاملاتي"),
        ("💵 الرصيد الآن", "cmd_الرصيد_الآن"),
        ("📈 ملخص مالي", "cmd_ملخص_مالي"),
        ("📅 تقرير شهري", "cmd_تقرير_شهري"),
        ("ℹ️ أنواع الحسابات", "cmd_انواع_الحسابات"),
        ("🔧 تعديل", "cmd_تعديل"),
        ("🗑️ حذف", "cmd_حذف"),
        ("❌ إخفاء", "cmd_hide")
    ]
    
    buttons = []
    for text, callback_data in commands:
        buttons.append(types.InlineKeyboardButton(text, callback_data=callback_data))
    
    # ترتيب الأزرار في صفوف
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            markup.row(buttons[i], buttons[i + 1])
        else:
            markup.row(buttons[i])
    
    return markup

def create_accounts_inline_keyboard(user_id):
    """إنشاء لوحة مفاتيح inline للحسابات"""
    accounts = get_user_accounts(user_id)
    
    if not accounts:
        return None
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # إضافة أزرار الحسابات
    buttons = []
    for acc_name, balance, acc_type in accounts:
        # تحديد الرمز حسب نوع الحساب
        type_emoji = {
            'asset': '💰',
            'for_us': '📈',
            'for_them': '📉',
            'expense': '💸',
            'revenue': '💵',
            'general': '📊'
        }
        emoji = type_emoji.get(acc_type, '📊')
        
        button_text = f"{emoji} {acc_name}"
        callback_data = f"acc_{acc_name}"
        buttons.append(types.InlineKeyboardButton(button_text, callback_data=callback_data))
    
    # ترتيب الأزرار في صفوف
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            markup.row(buttons[i], buttons[i + 1])
        else:
            markup.row(buttons[i])
    
    # إضافة زر الإخفاء
    markup.row(types.InlineKeyboardButton("❌ إخفاء", callback_data="acc_hide"))
    
    return markup

def create_transactions_inline_keyboard(user_id, limit=10):
    """إنشاء لوحة مفاتيح inline للمعاملات"""
    from database_updated import get_user_transactions
    transactions = get_user_transactions(user_id, limit)
    
    if not transactions:
        return None
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for trans_id, trans_type, from_acc, to_acc, amount, description, created_at in transactions:
        # تحديد نص المعاملة
        if trans_type == 'cash_in':
            trans_text = f"💰 دخول إلى {to_acc}: {amount:.2f}"
        elif trans_type == 'cash_out':
            trans_text = f"💸 خروج من {from_acc}: {amount:.2f}"
        else:  # transfer
            trans_text = f"🔄 {from_acc} → {to_acc}: {amount:.2f}"
        
        # قطع النص إذا كان طويلاً
        if len(trans_text) > 35:
            trans_text = trans_text[:32] + "..."
        
        button_text = f"#{trans_id} {trans_text}"
        callback_data = f"trans_{trans_id}"
        markup.row(types.InlineKeyboardButton(button_text, callback_data=callback_data))
    
    # إضافة زر الإخفاء
    markup.row(types.InlineKeyboardButton("❌ إخفاء", callback_data="trans_hide"))
    
    return markup

def handle_start(bot, message):
    """التعامل مع أمر البداية"""
    user_id = message.from_user.id
    username = message.from_user.first_name or "المستخدم"
    
    create_user(user_id)
    
    welcome_msg = f"""
🤖 **مرحباً {username}!**

أهلاً بك في **المساعد المحاسبي الذكي المحسن** 📊

**✨ الميزات الجديدة:**
• قوائم تفاعلية ذكية
• وظائف تعديل وحذف
• واجهة محسنة

**🎯 للبدء السريع:**
• اكتب `@` فقط لعرض قائمة الأوامر التفاعلية
• اختر الأمر المطلوب بنقرة واحدة
• استمتع بالتجربة المحسنة!

**📋 الأوامر الأساسية:**
• `@حساب [اسم]` - إضافة حساب جديد
• `@معاملة [تفاصيل]` - تسجيل معاملة
• `@كشف` - عرض الملخص المالي
• `@تعديل` - تعديل حساب أو معاملة
• `@حذف` - حذف حساب أو معاملة

💡 **نصيحة:** اكتب `@` واختر من القائمة التفاعلية!
    """
    
    bot.reply_to(message, welcome_msg.strip())

def handle_at_symbol(bot, message):
    """التعامل مع كتابة @ فقط لعرض قائمة الأوامر"""
    markup = create_commands_inline_keyboard()
    
    response = """
📋 **قائمة الأوامر التفاعلية**

اختر الأمر المطلوب من القائمة أدناه:

💡 **نصيحة:** بعد اختيار الأمر، يمكنك إكمال التفاصيل مباشرة
    """
    
    bot.reply_to(message, response.strip(), reply_markup=markup)

def handle_callback_query(bot, call):
    """التعامل مع الضغط على الأزرار التفاعلية"""
    user_id = call.from_user.id
    data = call.data
    
    try:
        # التعامل مع أوامر القائمة الرئيسية
        if data.startswith("cmd_"):
            command = data[4:]  # إزالة "cmd_"
            
            if command == "hide":
                bot.edit_message_text("✅ تم إخفاء القائمة", call.message.chat.id, call.message.message_id)
                return
            
            # إرسال الأمر مع إرشادات الإكمال
            command_instructions = {
                "حساب": "✏️ **@حساب** تم اختياره\n\nأكمل الآن: `@حساب [اسم الحساب]`\n\n**مثال:** `@حساب صندوق المحل`",
                "معاملة": "✏️ **@معاملة** تم اختياره\n\nأكمل الآن بأحد الأنماط:\n• `@معاملة دخول إلى @حساب مبلغ`\n• `@معاملة خروج من @حساب مبلغ`\n• `@معاملة من @حساب1 إلى @حساب2 مبلغ`\n\n💡 اكتب `@` لعرض قائمة الحسابات",
                "كشف": "📊 جاري إعداد كشف الحساب...",
                "الحسابات": "📋 جاري عرض قائمة الحسابات...",
                "معاملاتي": "📝 جاري عرض المعاملات...",
                "الرصيد_الآن": "💵 جاري حساب الرصيد النقدي...",
                "ملخص_مالي": "📈 جاري إعداد الملخص المالي...",
                "تقرير_شهري": "📅 جاري إعداد التقرير الشهري...",
                "انواع_الحسابات": "ℹ️ جاري عرض أنواع الحسابات...",
                "تعديل": "🔧 **@تعديل** تم اختياره\n\nاختر ما تريد تعديله:",
                "حذف": "🗑️ **@حذف** تم اختياره\n\nاختر ما تريد حذفه:"
            }
            
            instruction = command_instructions.get(command, f"تم اختيار الأمر: @{command}")
            
            # تنفيذ الأوامر المباشرة
            if command == "كشف":
                bot.edit_message_text("📊 جاري إعداد كشف الحساب...", call.message.chat.id, call.message.message_id)
                report = get_report(user_id)
                bot.send_message(call.message.chat.id, report)
            elif command == "الحسابات":
                bot.edit_message_text("📋 جاري عرض قائمة الحسابات...", call.message.chat.id, call.message.message_id)
                accounts_list = get_accounts_list(user_id)
                bot.send_message(call.message.chat.id, accounts_list)
            elif command == "معاملاتي":
                bot.edit_message_text("📝 جاري عرض المعاملات...", call.message.chat.id, call.message.message_id)
                transactions = get_transactions_history(user_id, 10)
                bot.send_message(call.message.chat.id, transactions)
            elif command == "الرصيد_الآن":
                bot.edit_message_text("💵 جاري حساب الرصيد النقدي...", call.message.chat.id, call.message.message_id)
                cash_balance = get_current_cash_balance(user_id)
                response = f"💰 **الرصيد النقدي الحالي:** {cash_balance:.2f}"
                bot.send_message(call.message.chat.id, response)
            elif command == "ملخص_مالي":
                bot.edit_message_text("📈 جاري إعداد الملخص المالي...", call.message.chat.id, call.message.message_id)
                summary = get_financial_summary(user_id)
                bot.send_message(call.message.chat.id, summary)
            elif command == "تقرير_شهري":
                bot.edit_message_text("📅 جاري إعداد التقرير الشهري...", call.message.chat.id, call.message.message_id)
                monthly_report = get_monthly_report(user_id)
                bot.send_message(call.message.chat.id, monthly_report)
            elif command == "انواع_الحسابات":
                bot.edit_message_text("ℹ️ جاري عرض أنواع الحسابات...", call.message.chat.id, call.message.message_id)
                types_info = get_account_types_info()
                bot.send_message(call.message.chat.id, types_info)
            elif command == "تعديل":
                bot.edit_message_text("🔧 اختر ما تريد تعديله:", call.message.chat.id, call.message.message_id)
                markup = create_edit_options_keyboard()
                bot.send_message(call.message.chat.id, "🔧 **خيارات التعديل:**", reply_markup=markup)
            elif command == "حذف":
                bot.edit_message_text("🗑️ اختر ما تريد حذفه:", call.message.chat.id, call.message.message_id)
                markup = create_delete_options_keyboard()
                bot.send_message(call.message.chat.id, "🗑️ **خيارات الحذف:**", reply_markup=markup)
            else:
                bot.edit_message_text(instruction, call.message.chat.id, call.message.message_id)
        
        # التعامل مع اختيار الحسابات
        elif data.startswith("acc_"):
            account = data[4:]  # إزالة "acc_"
            
            if account == "hide":
                bot.edit_message_text("✅ تم إخفاء قائمة الحسابات", call.message.chat.id, call.message.message_id)
                return
            
            instruction = f"✅ **تم اختيار الحساب:** @{account}\n\nيمكنك الآن استخدامه في المعاملات:\n\n**أمثلة:**\n• `@معاملة دخول إلى @{account} 1000`\n• `@معاملة خروج من @{account} 500`"
            bot.edit_message_text(instruction, call.message.chat.id, call.message.message_id)
        
        # التعامل مع اختيار المعاملات
        elif data.startswith("trans_"):
            trans_id = data[6:]  # إزالة "trans_"
            
            if trans_id == "hide":
                bot.edit_message_text("✅ تم إخفاء قائمة المعاملات", call.message.chat.id, call.message.message_id)
                return
            
            # عرض تفاصيل المعاملة مع خيارات التعديل والحذف
            transaction = get_transaction_by_id(user_id, int(trans_id))
            if transaction:
                trans_details = format_transaction_details(transaction)
                markup = create_transaction_actions_keyboard(trans_id)
                bot.edit_message_text(trans_details, call.message.chat.id, call.message.message_id, reply_markup=markup)
            else:
                bot.edit_message_text("❌ المعاملة غير موجودة", call.message.chat.id, call.message.message_id)
        
        # التعامل مع خيارات التعديل والحذف
        elif data.startswith("edit_") or data.startswith("delete_"):
            handle_edit_delete_actions(bot, call, data)
        
        # الإجابة على الاستعلام
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"خطأ: {str(e)}")

def create_edit_options_keyboard():
    """إنشاء لوحة مفاتيح لخيارات التعديل"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    buttons = [
        types.InlineKeyboardButton("📝 تعديل معاملة", callback_data="edit_transaction"),
        types.InlineKeyboardButton("🏦 تعديل حساب", callback_data="edit_account"),
        types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_hide")
    ]
    
    markup.row(buttons[0], buttons[1])
    markup.row(buttons[2])
    
    return markup

def create_delete_options_keyboard():
    """إنشاء لوحة مفاتيح لخيارات الحذف"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    buttons = [
        types.InlineKeyboardButton("🗑️ حذف معاملة", callback_data="delete_transaction"),
        types.InlineKeyboardButton("🏦 حذف حساب", callback_data="delete_account"),
        types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_hide")
    ]
    
    markup.row(buttons[0], buttons[1])
    markup.row(buttons[2])
    
    return markup

def create_transaction_actions_keyboard(trans_id):
    """إنشاء لوحة مفاتيح لإجراءات المعاملة"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    buttons = [
        types.InlineKeyboardButton("✏️ تعديل", callback_data=f"edit_trans_{trans_id}"),
        types.InlineKeyboardButton("🗑️ حذف", callback_data=f"delete_trans_{trans_id}"),
        types.InlineKeyboardButton("❌ إغلاق", callback_data="cmd_hide")
    ]
    
    markup.row(buttons[0], buttons[1])
    markup.row(buttons[2])
    
    return markup

def handle_edit_delete_actions(bot, call, data):
    """التعامل مع إجراءات التعديل والحذف"""
    user_id = call.from_user.id
    
    if data == "edit_transaction":
        # عرض قائمة المعاملات للتعديل
        markup = create_transactions_inline_keyboard(user_id)
        if markup:
            bot.edit_message_text("📝 **اختر المعاملة المراد تعديلها:**", call.message.chat.id, call.message.message_id, reply_markup=markup)
        else:
            bot.edit_message_text("❌ لا توجد معاملات للتعديل", call.message.chat.id, call.message.message_id)
    
    elif data == "edit_account":
        # عرض قائمة الحسابات للتعديل
        markup = create_accounts_inline_keyboard(user_id)
        if markup:
            bot.edit_message_text("🏦 **اختر الحساب المراد تعديله:**", call.message.chat.id, call.message.message_id, reply_markup=markup)
        else:
            bot.edit_message_text("❌ لا توجد حسابات للتعديل", call.message.chat.id, call.message.message_id)
    
    elif data == "delete_transaction":
        # عرض قائمة المعاملات للحذف
        markup = create_transactions_inline_keyboard(user_id)
        if markup:
            bot.edit_message_text("🗑️ **اختر المعاملة المراد حذفها:**\n\n⚠️ **تحذير:** هذا الإجراء لا يمكن التراجع عنه", call.message.chat.id, call.message.message_id, reply_markup=markup)
        else:
            bot.edit_message_text("❌ لا توجد معاملات للحذف", call.message.chat.id, call.message.message_id)
    
    elif data == "delete_account":
        # عرض قائمة الحسابات للحذف
        markup = create_accounts_inline_keyboard(user_id)
        if markup:
            bot.edit_message_text("🗑️ **اختر الحساب المراد حذفه:**\n\n⚠️ **تحذير:** سيتم حذف جميع المعاملات المرتبطة بهذا الحساب", call.message.chat.id, call.message.message_id, reply_markup=markup)
        else:
            bot.edit_message_text("❌ لا توجد حسابات للحذف", call.message.chat.id, call.message.message_id)
    
    elif data.startswith("edit_trans_"):
        trans_id = data[11:]  # إزالة "edit_trans_"
        bot.edit_message_text(f"✏️ **تعديل المعاملة #{trans_id}**\n\nأرسل البيانات الجديدة بالتنسيق:\n`@معاملة [تفاصيل جديدة]`", call.message.chat.id, call.message.message_id)
        # هنا يمكن إضافة منطق حفظ ID المعاملة للتعديل
    
    elif data.startswith("delete_trans_"):
        trans_id = data[12:]  # إزالة "delete_trans_"
        # تأكيد الحذف
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("✅ تأكيد الحذف", callback_data=f"confirm_delete_trans_{trans_id}"),
            types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_hide")
        )
        bot.edit_message_text(f"⚠️ **تأكيد حذف المعاملة #{trans_id}**\n\nهل أنت متأكد من حذف هذه المعاملة؟\nهذا الإجراء لا يمكن التراجع عنه.", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif data.startswith("confirm_delete_trans_"):
        trans_id = data[21:]  # إزالة "confirm_delete_trans_"
        result = delete_transaction(user_id, int(trans_id))
        bot.edit_message_text(result, call.message.chat.id, call.message.message_id)

def format_transaction_details(transaction):
    """تنسيق تفاصيل المعاملة للعرض"""
    trans_id, trans_type, from_acc, to_acc, amount, description, created_at = transaction
    
    details = f"📋 **تفاصيل المعاملة #{trans_id}**\n\n"
    
    if trans_type == 'cash_in':
        details += f"💰 **نوع المعاملة:** دخول نقدي\n"
        details += f"📥 **إلى الحساب:** {to_acc}\n"
    elif trans_type == 'cash_out':
        details += f"💸 **نوع المعاملة:** خروج نقدي\n"
        details += f"📤 **من الحساب:** {from_acc}\n"
    else:  # transfer
        details += f"🔄 **نوع المعاملة:** تحويل\n"
        details += f"📤 **من الحساب:** {from_acc}\n"
        details += f"📥 **إلى الحساب:** {to_acc}\n"
    
    details += f"💰 **المبلغ:** {amount:.2f}\n"
    details += f"📅 **التاريخ:** {created_at}\n"
    
    if description:
        details += f"📝 **الوصف:** {description}\n"
    
    return details

def get_account_types_info():
    """معلومات أنواع الحسابات"""
    return """
ℹ️ **أنواع الحسابات المدعومة**

**💰 الأصول النقدية:**
• صندوق، بنك، نقد، محفظة، خزنة
• تمثل الأموال المتاحة لديك

**📈 لنا (العملاء والمدينون):**
• عميل، زبون، مشتري
• الأشخاص الذين يدينون لك بأموال

**📉 لهم (الموردون والدائنون):**
• مورد، بائع، مقاول
• الأشخاص الذين تدين لهم بأموال

**💸 المصاريف:**
• مصروف، إيجار، راتب، كهرباء، ماء
• النفقات والتكاليف

**💵 الإيرادات:**
• مبيعات، دخل، ربح
• مصادر الدخل

**📊 حسابات عامة:**
• أي حساب لا يندرج تحت الفئات السابقة

💡 **النظام يتعرف تلقائياً على نوع الحساب من اسمه!**
    """

# باقي الوظائف من handlers_updated.py
def handle_add_account(bot, message):
    """التعامل مع إضافة حساب جديد"""
    user_id = message.from_user.id
    parts = message.text.strip().split()
    
    if len(parts) < 2:
        # عرض قائمة تفاعلية للمساعدة
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("💡 أمثلة الحسابات", callback_data="cmd_انواع_الحسابات"))
        
        error_msg = """
❌ **خطأ في الاستخدام**

الاستخدام الصحيح: `@حساب [اسم الحساب]`

**أمثلة سريعة:**
💰 `@حساب صندوق المحل`
🏦 `@حساب بنك الأهلي`
👤 `@حساب عميل أحمد`
        """
        bot.reply_to(message, error_msg.strip(), reply_markup=markup)
        return
    
    # دمج الكلمات لتكوين اسم الحساب
    account_name = " ".join(parts[1:])
    
    result = add_account(user_id, account_name)
    bot.reply_to(message, result)

def handle_transaction(bot, message):
    """التعامل مع تسجيل معاملة مالية"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    # إزالة @معاملة من بداية النص
    if text.startswith("@معاملة"):
        text = text[8:].strip()
    
    if not text:
        # عرض قائمة تفاعلية للمساعدة
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("📋 عرض الحسابات", callback_data="cmd_الحسابات"),
            types.InlineKeyboardButton("💡 أمثلة", callback_data="cmd_انواع_الحسابات")
        )
        
        error_msg = """
❌ **خطأ في الاستخدام**

**أنواع المعاملات المدعومة:**

💰 **دخول نقدي:**
• `@معاملة دخول إلى @صندوق 1000`

💸 **خروج نقدي:**
• `@معاملة خروج من @صندوق 500`

🔄 **تحويل:**
• `@معاملة من @صندوق إلى @بنك 1000`

💡 **نصيحة:** اكتب `@` لعرض قائمة الحسابات
        """
        bot.reply_to(message, error_msg.strip(), reply_markup=markup)
        return
    
    # تحليل النص
    parsed = parse_transaction_text(text)
    
    # استخراج الوصف
    description_parts = []
    for word in text.split():
        if not word.startswith('@') and not re.match(r'\d+(?:\.\d+)?', word) and word.lower() not in ['من', 'إلى', 'ل', 'دخول', 'خروج', 'تحويل', 'إيداع', 'سحب', 'دفع', 'صرف']:
            description_parts.append(word)
    description = " ".join(description_parts)
    
    if not parsed['amount']:
        bot.reply_to(message, "❌ لم يتم العثور على مبلغ صحيح في النص")
        return
    
    # تنفيذ المعاملة حسب النوع
    if parsed['type'] == 'cash_in':
        if not parsed['to_account']:
            bot.reply_to(message, "❌ لم يتم تحديد الحساب المستقبل للدخول النقدي")
            return
        result = add_cash_in_transaction(user_id, parsed['to_account'], parsed['amount'], description)
    
    elif parsed['type'] == 'cash_out':
        if not parsed['from_account']:
            bot.reply_to(message, "❌ لم يتم تحديد الحساب المرسل للخروج النقدي")
            return
        result = add_cash_out_transaction(user_id, parsed['from_account'], parsed['amount'], description)
    
    else:  # transfer
        if not parsed['from_account'] or not parsed['to_account']:
            bot.reply_to(message, "❌ لم يتم تحديد الحساب المرسل والمستقبل للتحويل")
            return
        result = add_transfer_transaction(user_id, parsed['from_account'], parsed['to_account'], parsed['amount'], description)
    
    bot.reply_to(message, result)

def handle_accounts_request(bot, message):
    """التعامل مع طلب عرض الحسابات مع قائمة تفاعلية"""
    user_id = message.from_user.id
    
    # عرض قائمة الحسابات النصية
    accounts_list = get_accounts_list(user_id)
    
    # إضافة قائمة تفاعلية
    markup = create_accounts_inline_keyboard(user_id)
    
    if markup:
        response = accounts_list + "\n\n💡 **اختر حساباً من القائمة أدناه للاستخدام السريع:**"
        bot.reply_to(message, response, reply_markup=markup)
    else:
        bot.reply_to(message, accounts_list)

def handle_unknown_command(bot, message):
    """التعامل مع الأوامر غير المعروفة"""
    # إذا كانت الرسالة تحتوي على @ فقط، عرض القائمة التفاعلية
    if message.text.strip() == "@":
        handle_at_symbol(bot, message)
        return
    
    # إذا كانت الرسالة تحتوي على @ متبوعة بنص، عرض قائمة الحسابات
    if message.text.strip().endswith("@") and len(message.text.strip()) > 1:
        markup = create_accounts_inline_keyboard(message.from_user.id)
        if markup:
            bot.reply_to(message, "📋 **اختر الحساب المطلوب:**", reply_markup=markup)
        else:
            bot.reply_to(message, "❌ لا توجد حسابات مسجلة. استخدم @حساب لإضافة حساب جديد.")
        return
    
    # رسالة الأوامر غير المعروفة
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("📋 عرض الأوامر", callback_data="cmd_help"))
    
    unknown_msg = """
❓ **أمر غير معروف**

💡 **للمساعدة السريعة:**
• اكتب `@` فقط لعرض قائمة الأوامر
• اكتب `/help` للمساعدة الشاملة

**الأوامر الأساسية:**
• `@حساب` - إضافة حساب
• `@معاملة` - تسجيل معاملة
• `@كشف` - الملخص المالي
    """
    bot.reply_to(message, unknown_msg.strip(), reply_markup=markup)

# باقي الوظائف من الملف السابق...
def handle_report(bot, message):
    """التعامل مع طلب كشف الحساب"""
    user_id = message.from_user.id
    report = get_report(user_id)
    bot.reply_to(message, report)

def handle_current_balance(bot, message):
    """التعامل مع طلب الرصيد النقدي الحالي"""
    user_id = message.from_user.id
    cash_balance = get_current_cash_balance(user_id)
    
    response = f"""
💰 **الرصيد النقدي الحالي**

📊 إجمالي النقد المتاح: **{cash_balance:.2f}**

💡 هذا الرصيد يشمل جميع الحسابات النقدية (صندوق، بنك، محفظة)

للحصول على تفاصيل أكثر، استخدم:
• `@كشف` - للملخص الشامل
• `@الحسابات` - لقائمة الحسابات
    """
    
    bot.reply_to(message, response.strip())

def handle_financial_summary(bot, message):
    """التعامل مع طلب الملخص المالي المفصل"""
    user_id = message.from_user.id
    summary = get_financial_summary(user_id)
    bot.reply_to(message, summary)

def handle_monthly_report(bot, message):
    """التعامل مع طلب التقرير الشهري"""
    user_id = message.from_user.id
    monthly_report = get_monthly_report(user_id)
    bot.reply_to(message, monthly_report)

def handle_transactions_history(bot, message):
    """التعامل مع طلب سجل المعاملات مع قائمة تفاعلية"""
    user_id = message.from_user.id
    
    # عرض سجل المعاملات النصي
    transactions = get_transactions_history(user_id, 10)
    
    # إضافة قائمة تفاعلية للمعاملات
    markup = create_transactions_inline_keyboard(user_id)
    
    if markup:
        response = transactions + "\n\n💡 **اختر معاملة من القائمة أدناه لعرض التفاصيل:**"
        bot.reply_to(message, response, reply_markup=markup)
    else:
        bot.reply_to(message, transactions)

def handle_help(bot, message):
    """التعامل مع طلب المساعدة"""
    markup = create_commands_inline_keyboard()
    
    help_msg = """
🆘 **دليل الاستخدام الشامل**

**✨ الميزات الجديدة:**
• قوائم تفاعلية ذكية
• وظائف تعديل وحذف
• واجهة محسنة

**🎯 للاستخدام السريع:**
• اكتب `@` فقط لعرض قائمة الأوامر التفاعلية

**🏦 إدارة الحسابات:**
• `@حساب [اسم]` - إضافة حساب جديد
• `@الحسابات` - عرض جميع الحسابات

**💸 المعاملات المالية:**
• `@معاملة [تفاصيل]` - تسجيل معاملة
• `@معاملاتي` - عرض آخر المعاملات

**🔧 التعديل والحذف:**
• `@تعديل` - تعديل حساب أو معاملة
• `@حذف` - حذف حساب أو معاملة

💡 **جرب القائمة التفاعلية أدناه:**
    """
    bot.reply_to(message, help_msg.strip(), reply_markup=markup)

