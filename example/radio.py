"""
run: python -m example.radio_group
"""
from telegrambotclient import bot_client
from telegrambotclient.base import InlineKeyboardButton, MessageField
from telegrambotclient.ui import InlineKeyboard, Radio

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


def radio_callback(bot, callback_query, text, option):
    text = "You click: text={0} option={1}".format(text, option)
    bot.send_message(chat_id=callback_query.from_user.id, text=text)
    return text


radio_name = "my-radio"
Radio.setup(router, radio_name, radio_callback)


@router.message_handler(fields=MessageField.TEXT)
def on_show_keyboard(bot, message):
    buttons = Radio.create(radio_name, ("key1", "value1", True),
                           ("key2", "value2"), ("key3", "value3"))
    keyboard = InlineKeyboard(*buttons)
    keyboard.add_buttons(
        InlineKeyboardButton(text="submit", callback_data="submit"))
    bot.send_message(chat_id=message.chat.id,
                     text="Your selections:",
                     reply_markup=keyboard.markup())
    return bot.stop_call


@router.callback_query_handler(callback_data="submit")
def on_submit(bot, callback_query):
    text, value = Radio.lookup(
        callback_query.message.reply_markup.inline_keyboard, radio_name)
    bot.send_message(chat_id=callback_query.from_user.id,
                     text="you select item: text={0}, option={1}".format(
                         text, value))
    return bot.stop_call


bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(timeout=10)
