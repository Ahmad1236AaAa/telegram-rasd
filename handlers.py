from database import create_user, add_account, add_transaction, get_total_report

def handle_start(bot, message):
    user_id = message.from_user.id
    create_user(user_id)
    bot.reply_to(message, """
أهلاً بك في *رصد* مساعدك المحاسبي الذكي 👋

*الأوامر الأساسية:*

*@معاملة* "يضيف معاملة (دخول كاش / خروج كاش / تحويل بين حسابات)" 
*@كشف_الكلي* "يعرض جميع الحسابات مع أرصدتها + المجموع النهائي (الخزنة)"
*@كشف_لنا* "يعرض الحسابات المدينة لنا + مجموعها" 
*@كشف_لهم* "يعرض الحسابات الدائنة لنا + مجموعها"
*@كشف_حساب* "يعرض حركة حساب معين + رصيده النهائي"
*@معاملاتي* "يعرض آخر 10 معاملات"
*@الرصيد* "يعرض رصيد الخزنة الرئيسية"
*@تعديل* "يسمح بتعديل معاملة موجودة"
*@حذف* "يحذف معاملة"
""", parse_mode="Markdown")

def handle_add_account(bot, message):
    user_id = message.from_user.id
    parts = message.text.strip().split()
    if len(parts) < 2:
        bot.reply_to(message, "يرجى كتابة اسم الحساب بعد @حساب")
        return
    name = " ".join(parts[1:])
    result = add_account(user_id, name)
    bot.reply_to(message, result)
def handle_transaction(bot, message):
    user_id = message.from_user.id
    parts = message.text.strip().split()
    if len(parts) < 4:
        bot.reply_to(message, "الاستخدام: @معاملة من إلى المبلغ")
        return
    from_acc, to_acc = parts[1], parts[2]
    try:
        amount = float(parts[3])
    except ValueError:
        bot.reply_to(message, "❌ المبلغ يجب أن يكون رقمًا.")
        return
    note = " ".join(parts[4:]) if len(parts) > 4 else ""
    result = add_transaction(user_id, from_acc, to_acc, amount, note)
    bot.reply_to(message, result)
def handle_total_report(bot, message):
    user_id = message.from_user.id
    report = get_total_report(user_id)
    bot.reply_to(message, report)

def handle_debtors_report(bot, message):
    user_id = message.from_user.id
    report = get_debtors_report(user_id)
    bot.reply_to(message, report)

def handle_creditors_report(bot, message):
    user_id = message.from_user.id
    report = get_creditors_report(user_id)
    bot.reply_to(message, report)

def handle_account_statement(bot, message):
    user_id = message.from_user.id
    parts = message.text.strip().split()
    if len(parts) < 2:
        bot.reply_to(message, "الاستخدام: @كشف_حساب اسم_الحساب")
        return
    account_name = " ".join(parts[1:])
    report = get_account_statement(user_id, account_name)
    bot.reply_to(message, report)

def handle_latest_transactions(bot, message):
    user_id = message.from_user.id
    report = get_latest_transactions_details(user_id)
    bot.reply_to(message, report)

def handle_main_balance(bot, message):
    user_id = message.from_user.id
    balance = get_main_balance(user_id)
    bot.reply_to(message, balance)




def handle_edit_transaction(bot, message):
    user_id = message.from_user.id
    parts = message.text.strip().split()
    if len(parts) < 2:
        bot.reply_to(message, "الاستخدام: تعديل #رقم_المعاملة")
        return
    try:
        transaction_id = int(parts[1].replace("#", ""))
    except ValueError:
        bot.reply_to(message, "❌ رقم المعاملة غير صحيح.")
        return

    transaction = get_transaction_by_id(user_id, transaction_id)
    if not transaction:
        bot.reply_to(message, "❌ المعاملة غير موجودة أو لا تملك صلاحية تعديلها.")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    itembtn1 = types.InlineKeyboardButton("الحساب", callback_data=f"edit_account_{transaction_id}")
    itembtn2 = types.InlineKeyboardButton("المبلغ", callback_data=f"edit_amount_{transaction_id}")
    itembtn3 = types.InlineKeyboardButton("الملاحظة", callback_data=f"edit_note_{transaction_id}")
    itembtn4 = types.InlineKeyboardButton("إلغاء", callback_data=f"cancel_edit_{transaction_id}")
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4)

    bot.reply_to(message, f"ماذا تريد تعديل في #{transaction_id}؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_") or call.data.startswith("cancel_edit_"))
def callback_inline_edit(call):
    user_id = call.from_user.id
    data = call.data.split("_")
    action = data[0]
    field = data[1]
    transaction_id = int(data[2])

    if action == "cancel":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="تم إلغاء التعديل.")
        return

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"أدخل {field} الجديد لـ #{transaction_id}:")
    bot.register_next_step_handler(call.message, lambda m: process_edit_step(m, user_id, transaction_id, field))

def process_edit_step(message, user_id, transaction_id, field):
    new_value = message.text
    if field == "amount":
        try:
            new_value = float(new_value)
        except ValueError:
            bot.reply_to(message, "❌ المبلغ يجب أن يكون رقمًا.")
            return
    
    if update_transaction(user_id, transaction_id, field, new_value):
        bot.reply_to(message, f"✅ تم تحديث {field} للمعاملة #{transaction_id} بنجاح.")
    else:
        bot.reply_to(message, "❌ حدث خطأ أثناء التحديث.")

def handle_delete_transaction(bot, message):
    user_id = message.from_user.id
    parts = message.text.strip().split()
    if len(parts) < 2:
        bot.reply_to(message, "الاستخدام: حذف #رقم_المعاملة")
        return
    try:
        transaction_id = int(parts[1].replace("#", ""))
    except ValueError:
        bot.reply_to(message, "❌ رقم المعاملة غير صحيح.")
        return

    transaction = get_transaction_by_id(user_id, transaction_id)
    if not transaction:
        bot.reply_to(message, "❌ المعاملة غير موجودة أو لا تملك صلاحية حذفها.")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    itembtn1 = types.InlineKeyboardButton("نعم", callback_data=f"confirm_delete_{transaction_id}")
    itembtn2 = types.InlineKeyboardButton("لا", callback_data=f"cancel_delete_{transaction_id}")
    markup.add(itembtn1, itembtn2)

    bot.reply_to(message, f"هل متأكد من حذف المعاملة #{transaction_id}؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_delete_") or call.data.startswith("cancel_delete_"))
def callback_inline_delete(call):
    user_id = call.from_user.id
    data = call.data.split("_")
    action = data[0]
    transaction_id = int(data[2])

    if action == "confirm":
        if delete_transaction_db(user_id, transaction_id):
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"✅ تم حذف المعاملة #{transaction_id} بنجاح.")
        else:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="❌ حدث خطأ أثناء الحذف.")
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="تم إلغاء الحذف.")


