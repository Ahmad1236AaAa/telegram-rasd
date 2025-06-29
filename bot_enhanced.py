import telebot
from handlers_enhanced import (
    handle_start, handle_at_symbol, handle_add_account, handle_transaction,
    handle_report, handle_accounts_request, handle_current_balance,
    handle_financial_summary, handle_monthly_report, handle_transactions_history,
    handle_help, handle_unknown_command, handle_callback_query
)
from config import TOKEN as BOT_TOKEN

# إنشاء البوت
bot = telebot.TeleBot(BOT_TOKEN)

# معالج أمر البداية
@bot.message_handler(commands=['start'])
def start_command(message):
    handle_start(bot, message)

# معالج أمر المساعدة
@bot.message_handler(commands=['help'])
def help_command(message):
    handle_help(bot, message)

# معالج الضغط على الأزرار التفاعلية
@bot.callback_query_handler(func=lambda call: True)
def callback_query_handler(call):
    handle_callback_query(bot, call)

# معالج الرسائل النصية
@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    text = message.text.strip()
    
    # التعامل مع @ فقط
    if text == "@":
        handle_at_symbol(bot, message)
        return
    
    # التعامل مع الأوامر المختلفة
    if text.startswith("@حساب"):
        handle_add_account(bot, message)
    elif text.startswith("@معاملة"):
        handle_transaction(bot, message)
    elif text == "@كشف":
        handle_report(bot, message)
    elif text == "@الحسابات":
        handle_accounts_request(bot, message)
    elif text == "@معاملاتي":
        handle_transactions_history(bot, message)
    elif text == "@الرصيد_الآن":
        handle_current_balance(bot, message)
    elif text == "@ملخص_مالي":
        handle_financial_summary(bot, message)
    elif text == "@تقرير_شهري":
        handle_monthly_report(bot, message)
    elif text == "@انواع_الحسابات":
        from handlers_enhanced import get_account_types_info
        bot.reply_to(message, get_account_types_info())
    elif text.startswith("@تعديل"):
        # عرض خيارات التعديل
        from handlers_enhanced import create_edit_options_keyboard
        markup = create_edit_options_keyboard()
        bot.reply_to(message, "🔧 **اختر ما تريد تعديله:**", reply_markup=markup)
    elif text.startswith("@حذف"):
        # عرض خيارات الحذف
        from handlers_enhanced import create_delete_options_keyboard
        markup = create_delete_options_keyboard()
        bot.reply_to(message, "🗑️ **اختر ما تريد حذفه:**\n\n⚠️ **تحذير:** هذا الإجراء لا يمكن التراجع عنه", reply_markup=markup)
    elif text.endswith("@") and len(text) > 1:
        # عرض قائمة الحسابات عند كتابة @ في نهاية أمر
        from handlers_enhanced import create_accounts_inline_keyboard
        markup = create_accounts_inline_keyboard(message.from_user.id)
        if markup:
            bot.reply_to(message, "📋 **اختر الحساب المطلوب:**", reply_markup=markup)
        else:
            bot.reply_to(message, "❌ لا توجد حسابات مسجلة. استخدم @حساب لإضافة حساب جديد.")
    else:
        handle_unknown_command(bot, message)

if __name__ == "__main__":
    print("🤖 بدء تشغيل المساعد المحاسبي الذكي المحسن...")
    print("✨ الميزات الجديدة:")
    print("   • قوائم تفاعلية ذكية")
    print("   • وظائف تعديل وحذف")
    print("   • واجهة محسنة")
    print("🚀 البوت جاهز للاستخدام!")
    
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"❌ خطأ في تشغيل البوت: {e}")
        print("💡 تأكد من صحة التوكن في ملف config.py")

