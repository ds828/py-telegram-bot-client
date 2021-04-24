"""
run in cli: python -m example.radio_group
"""
import logging

from telegrambotclient import bot_client
from telegrambotclient.base import (CallbackQuery, InlineKeyboardButton,
                                    Message, MessageField)
from telegrambotclient.ui import InlineKeyboard

from example.settings import BOT_TOKEN

logger = logging.getLogger("telegram-bot-client")
logger.setLevel(logging.DEBUG)

router = bot_client.router()
example_bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


def radio_callback(bot, callback_query: CallbackQuery, text, option):
    text = "You click: text={0} option={1}".format(text, option)
    bot.send_message(chat_id=callback_query.from_user.id, text=text)
    return text


InlineKeyboard.auto_radio(router,
                          name="radio-group",
                          changed_callback=radio_callback)


@router.message_handler(fields=MessageField.TEXT)
def on_show_keyboard(bot, message: Message):
    keyboard = InlineKeyboard()
    keyboard.add_radio_group("radio-group", ("key1", "value1", True),
                             ("key2", "value2"), ("key3", "value3"))
    keyboard.add_buttons(
        InlineKeyboardButton(text="submit", callback_data="submit"))
    bot.send_message(chat_id=message.chat.id,
                     text="Your selections:",
                     reply_markup=keyboard.markup())


@router.callback_query_handler(callback_data="submit")
def on_submit(bot, callback_query):
    keyboard = InlineKeyboard(
        callback_query.message.reply_markup.inline_keyboard)
    bot.send_message(
        chat_id=callback_query.from_user.id,
        text="you select item: text={0}, option={1}".format(
            *keyboard.get_radio_value("radio-group"), ),
    )


example_bot.run_polling(timeout=10)
