import telebot
from telebot import types
from handlers import handle_start, handle_add_account, handle_transaction, handle_total_report, handle_debtors_report, handle_creditors_report, handle_account_statement, handle_latest_transactions, handle_main_balance, handle_edit_transaction, handle_delete_transaction
from database import get_user_accounts, get_latest_transactions
from config import TOKEN

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    handle_start(bot, message)

@bot.message_handler(func=lambda msg: msg.text.startswith("@حساب"))
def add_account(message):
    handle_add_account(bot, message)

@bot.message_handler(func=lambda msg: msg.text.startswith("@معاملة"))
def transaction(message):
    handle_transaction(bot, message)

@bot.message_handler(func=lambda msg: msg.text.startswith("@كشف"))
def report(message):
    handle_total_report(bot, message)
print("🤖 Bot is running...")
bot.polling()

@bot.inline_query_handler(func=lambda query: True)
def inline_query(query):
    commands = [
        types.InlineQueryResultArticle(
            id='1',
            title='معاملة',
            description='يضيف معاملة (دخول كاش / خروج كاش / تحويل بين حسابات)',
            input_message_content=types.InputTextMessageContent('معاملة ')
        ),
        types.InlineQueryResultArticle(
            id='2',
            title='كشف_الكلي',
            description='يعرض جميع الحسابات مع أرصدتها + المجموع النهائي (الخزنة)',
            input_message_content=types.InputTextMessageContent('كشف_الكلي')
        ),
        types.InlineQueryResultArticle(
            id='3',
            title='كشف_لنا',
            description='يعرض الحسابات المدينة لنا + مجموعها',
            input_message_content=types.InputTextMessageContent('كشف_لنا')
        ),
        types.InlineQueryResultArticle(
            id='4',
            title='كشف_لهم',
            description='يعرض الحسابات الدائنة لنا + مجموعها',
            input_message_content=types.InputTextMessageContent('كشف_لهم')
        ),
        types.InlineQueryResultArticle(
            id='5',
            title='كشف_حساب',
            description='يعرض حركة حساب معين + رصيده النهائي',
            input_message_content=types.InputTextMessageContent('كشف_حساب ')
        ),
        types.InlineQueryResultArticle(
            id='6',
            title='معاملاتي',
            description='يعرض آخر 10 معاملات',
            input_message_content=types.InputTextMessageContent('معاملاتي')
        ),
        types.InlineQueryResultArticle(
            id='7',
            title='الرصيد',
            description='يعرض رصيد الخزنة الرئيسية',
            input_message_content=types.InputTextMessageContent('الرصيد')
        ),
        types.InlineQueryResultArticle(
            id='8',
            title='تعديل',
            description='يسمح بتعديل معاملة موجودة',
            input_message_content=types.InputTextMessageContent('تعديل ')
        ),
        types.InlineQueryResultArticle(
            id='9',
            title='حذف',
            description='يحذف معاملة',
            input_message_content=types.InputTextMessageContent('حذف ')
        )
    ]

    if query.query.startswith("معاملة ") or query.query.startswith("كشف_حساب "):
        user_accounts = get_user_accounts(query.from_user.id)
        results = []
        for i, account in enumerate(user_accounts):
            results.append(
                types.InlineQueryResultArticle(
                    id=str(i),
                    title=account,
                    input_message_content=types.InputTextMessageContent(query.query + account)
                )
            )
        bot.answer_inline_query(query.id, results, cache_time=1)
    elif query.query.startswith("تعديل ") or query.query.startswith("حذف "):
        latest_transactions = get_latest_transactions(query.from_user.id)
        results = []
        for i, transaction_id in enumerate(latest_transactions):
            results.append(
                types.InlineQueryResultArticle(
                    id=str(i),
                    title=f"#{transaction_id}",
                    input_message_content=types.InputTextMessageContent(query.query + f"#{transaction_id}")
                )
            )
        bot.answer_inline_query(query.id, results, cache_time=1)
    elif not query.query:
        bot.answer_inline_query(query.id, commands, cache_time=1)
    else:
        filtered_commands = [cmd for cmd in commands if query.query.lower() in cmd.title.lower()]
        bot.answer_inline_query(query.id, filtered_commands, cache_time=1)



@bot.message_handler(func=lambda msg: msg.text == "كشف_لنا")
def debtors_report(message):
    handle_debtors_report(bot, message)

@bot.message_handler(func=lambda msg: msg.text == "كشف_لهم")
def creditors_report(message):
    handle_creditors_report(bot, message)

@bot.message_handler(func=lambda msg: msg.text.startswith("كشف_حساب"))
def account_statement(message):
    handle_account_statement(bot, message)

@bot.message_handler(func=lambda msg: msg.text == "معاملاتي")
def latest_transactions(message):
    handle_latest_transactions(bot, message)

@bot.message_handler(func=lambda msg: msg.text == "الرصيد")
def main_balance(message):
    handle_main_balance(bot, message)

@bot.message_handler(func=lambda msg: msg.text.startswith("تعديل"))
def edit_transaction(message):
    handle_edit_transaction(bot, message)

@bot.message_handler(func=lambda msg: msg.text.startswith("حذف"))
def delete_transaction(message):
    handle_delete_transaction(bot, message)




@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data.startswith("edit_") or call.data.startswith("cancel_edit_"):
        callback_inline_edit(call)
    elif call.data.startswith("confirm_delete_") or call.data.startswith("cancel_delete_"):
        callback_inline_delete(call)


