"""
run in cli: python -m example.toggler
"""
import logging

from telegrambotclient import TelegramBot, bot_client
from telegrambotclient.base import InlineKeyboardButton, Message, MessageField
from telegrambotclient.ui import InlineKeyboard

from example.settings import BOT_TOKEN

logger = logging.getLogger("telegram-bot-client")
logger.setLevel(logging.DEBUG)

router = bot_client.router()
my_bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
my_bot.delete_webhook(drop_pending_updates=True)


def on_toggle_callback(bot, callback_query, toggle_status: bool):
    return "Toggler status: {0}".format(toggle_status)


emoji_true = "✔️✔️"
emoji_fale = "❌"
InlineKeyboard.auto_toggle(router,
                           name="toggler",
                           toggled_callback=on_toggle_callback,
                           emoji=(emoji_true, emoji_fale))


@router.message_handler(fields=MessageField.TEXT)
def on_show_keyboard(bot: TelegramBot, message: Message):
    keyboard = InlineKeyboard()
    keyboard.add_toggler("toggler",
                         "This is a toggler",
                         toggle_status=True,
                         emoji=(emoji_true, emoji_fale))
    keyboard.add_buttons(
        InlineKeyboardButton(text="submit", callback_data="submit"))
    bot.send_message(chat_id=message.chat.id,
                     text="Toggler status: {0}".format(True),
                     reply_markup=keyboard.markup())


@router.callback_query_handler(callback_data="submit")
def on_submit(bot, callback_query):
    keyboard = InlineKeyboard(
        callback_query.message.reply_markup.inline_keyboard)

    toggle_status = keyboard.get_toggler_value("toggler")
    bot.send_message(
        chat_id=callback_query.from_user.id,
        text="Toggled: {0}".format(toggle_status),
    )


my_bot.run_polling(timeout=10)
