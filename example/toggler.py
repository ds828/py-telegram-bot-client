"""
run in cli: python -m example.toggler
"""
import logging

from telegrambotclient import TelegramBot, bot_client
from telegrambotclient.base import (CallbackQuery, InlineKeyboardButton,
                                    Message, MessageField)
from telegrambotclient.ui import InlineKeyboard

from example.settings import BOT_TOKEN

logger = logging.getLogger("telegram-bot-client")
logger.setLevel(logging.DEBUG)

router = bot_client.router()
example_bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


def on_toggle_callback(bot: TelegramBot, callback_query: CallbackQuery, option,
                       toggle_status):
    bot.send_message(chat_id=callback_query.from_user.id,
                     text="toggler is {0}: {1}".format(
                         "on" if toggle_status else "off", option))


InlineKeyboard.auto_toggle(
    router,
    name="toggler",
    toggled_callback=on_toggle_callback,
)


@router.message_handler(fields=MessageField.TEXT)
def on_show_keyboard(bot: TelegramBot, message: Message):
    keyboard = InlineKeyboard()
    keyboard.add_toggler("toggler", "toggle_value", toggle_status=True)
    keyboard.add_buttons(
        InlineKeyboardButton(text="submit", callback_data="submit"))
    bot.send_message(chat_id=message.chat.id,
                     text="Your selections:",
                     reply_markup=keyboard.markup())


@router.callback_query_handler(callback_data="submit")
def on_submit(bot, callback_query):
    keyboard = InlineKeyboard(
        callback_query.message.reply_markup.inline_keyboard)

    toggle_status, toggle_option = keyboard.get_toggler_value("toggler")
    bot.send_message(
        chat_id=callback_query.from_user.id,
        text="toggled: {0}, {1}".format(toggle_status, toggle_option),
    )


example_bot.run_polling(timeout=10)
