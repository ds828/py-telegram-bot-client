"""
run in cli: python -m example.select_group.py
"""
import logging
from simplebot import bot_proxy, SimpleBot
from simplebot.base import (
    CallbackQuery,
    InlineKeyboardButton,
    Message,
    MessageField,
)
from simplebot.ui import InlineKeyboard
from example.settings import BOT_TOKEN

logger = logging.getLogger("simple-bot")
logger.setLevel(logging.DEBUG)

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


def select_callback(bot: SimpleBot, callback_query: CallbackQuery, option):
    bot.send_message(
        chat_id=callback_query.from_user.id, text="you select: {0}".format(option)
    )


def unselect_callback(bot: SimpleBot, callback_query: CallbackQuery, option):
    bot.send_message(
        chat_id=callback_query.from_user.id, text="you unselect: {0}".format(option)
    )


InlineKeyboard.set_select_callback(
    router,
    name="select-group",
    selected_callback=select_callback,
    unselected_callback=unselect_callback,
)


@router.message_handler(fields=(MessageField.TEXT,))
def on_show_keyboard(bot: SimpleBot, message: Message):
    keyboard = InlineKeyboard()
    keyboard.add_select_group(
        "select-group",
        ("select1", "select-value1", True),  # selected
        ("select2", "select-value2"),
        ("select3", "select-value3"),
    )
    keyboard.add_buttons(InlineKeyboardButton(text="submit", callback_data="submit"))
    bot.send_message(
        chat_id=message.chat.id,
        text="Your selections:",
        reply_markup=keyboard.markup(),
    )


@router.callback_query_handler(static_match="submit")
def on_submit(bot, callback_query):
    keyboard = InlineKeyboard(callback_query.message.reply_markup.inline_keyboard)
    bot.send_message(
        chat_id=callback_query.from_user.id,
        text="you select: {0}".format(
            keyboard.get_select_value("select-group"),
        ),
    )


example_bot.run_polling(timeout=10)
