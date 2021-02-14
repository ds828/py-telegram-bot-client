"""
run in cli: python -m example.toggler.py
"""
import logging
from simplebot.utils import pretty_print
from simplebot import bot_proxy, SimpleBot
from simplebot.base import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    MessageField,
)
from simplebot.ui import Toggler
from example.settings import BOT_TOKEN

logger = logging.getLogger("simple-bot")
logger.setLevel(logging.DEBUG)

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


def select_toggle_callback(
    bot: SimpleBot, callback_query: CallbackQuery, *option, switch_status
):
    print(option, switch_status)


Toggler.set_auto_toggle(router, name="toggler", toggle_callback=select_toggle_callback)


@router.message_handler(fields=(MessageField.TEXT,))
def on_show_keyboard(bot: SimpleBot, message: Message):
    toggler = Toggler(name="toggler", option_value=("I am a toggler", "str-value", 123))
    toggler.add_buttons(InlineKeyboardButton(text="submit", callback_data="submit"))
    bot.send_message(
        chat_id=message.chat.id,
        text="Your selections:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=toggler.layout),
    )


@router.callback_query_handler(static_match="submit")
def on_submit(bot, callback_query):
    toggler = Toggler(
        name="toggler", layout=callback_query.message.reply_markup.inline_keyboard
    )
    bot.send_message(
        chat_id=callback_query.from_user.id,
        text="you select: {0}".format(
            toggler.get_selected(),
        ),
    )


example_bot.run_polling(timeout=10)
