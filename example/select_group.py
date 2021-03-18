"""
run in cli: python -m example.select_group.py
"""
import logging

from simplebot import SimpleBot, bot_proxy
from simplebot.base import (CallbackQuery, InlineKeyboardButton, Message,
                            MessageField)
from simplebot.ui import InlineKeyboard

from example.settings import BOT_TOKEN

logger = logging.getLogger("simple-bot")
logger.setLevel(logging.DEBUG)

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


def select_callback(bot: SimpleBot, callback_query: CallbackQuery, text,
                    option):
    text = "you select: text={0} option={1}".format(text, option)
    bot.send_message(chat_id=callback_query.from_user.id, text=text)
    return text


def unselect_callback(bot: SimpleBot, callback_query: CallbackQuery, text,
                      option):
    bot.send_message(chat_id=callback_query.from_user.id,
                     text="you unselect: text={0} option={1}".format(
                         text, option))


InlineKeyboard.auto_select(
    router,
    name="select-group",
    selected_callback=select_callback,
    unselected_callback=unselect_callback,
)


@router.message_handler(fields=MessageField.TEXT)
def on_show_keyboard(bot: SimpleBot, message: Message):
    keyboard = InlineKeyboard()
    keyboard.add_select_group(
        "select-group",
        ("select1", "select-value1", True),  # selected
        ("select2", "select-value2"),
        ("select3", "select-value3"),
    )
    keyboard.add_buttons(
        InlineKeyboardButton(text="submit", callback_data="submit"))
    bot.send_message(
        chat_id=message.chat.id,
        text="Your selections:",
        reply_markup=keyboard.markup(),
    )


@router.callback_query_handler(callback_data="submit")
def on_submit(bot, callback_query):
    keyboard = InlineKeyboard(
        callback_query.message.reply_markup.inline_keyboard)
    message_text = "\n".join([
        "you select item: text={0}, option={1}".format(text, option)
        for text, option in keyboard.get_select_value("select-group")
    ])
    bot.send_message(
        chat_id=callback_query.from_user.id,
        text=message_text or "nothing selected",
    )


example_bot.run_polling(timeout=10)
