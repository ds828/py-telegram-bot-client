"""
run: python -m example.toggler
"""
from telegrambotclient import bot_client
from telegrambotclient.base import InlineKeyboardButton, MessageField
from telegrambotclient.ui import InlineKeyboard, Switch

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


def on_switch_callback(bot, callback_query, status: bool):
    return "switch status: {0}".format(status)


switch_name = "my-switch"
Switch.setup(router, switch_name, on_switch_callback)


@router.message_handler(fields=MessageField.TEXT)
def on_show_keyboard(bot, message):
    button = Switch.create(switch_name, "my switch", True)
    keyboard = InlineKeyboard()
    keyboard.add_buttons(
        button, InlineKeyboardButton(text="submit", callback_data="submit"))
    bot.send_message(chat_id=message.chat.id,
                     text="switch status: {0}".format(True),
                     reply_markup=keyboard.markup())
    return bot.stop_call


@router.callback_query_handler(callback_data="submit")
def on_submit(bot, callback_query):
    status = Switch.lookup(callback_query.message.reply_markup.inline_keyboard,
                           switch_name)
    bot.send_message(
        chat_id=callback_query.from_user.id,
        text="switch status: {0}".format(status),
    )
    return bot.stop_call


bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(timeout=10)
