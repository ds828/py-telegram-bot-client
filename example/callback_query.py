"""
run in terminal: python -m example.callback_query.py
"""
import logging

from simplebot import bot_proxy, SimpleBot
from simplebot.base import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    MessageType,
)
from simplebot.ui import Keyboard
from simplebot.utils import build_callback_data, parse_callback_data

from example.settings import BOT_TOKEN

logger = logging.getLogger("simple-bot")
logger.setLevel(logging.DEBUG)

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


@router.message_handler(message_type=MessageType.TEXT)
def on_select(bot: SimpleBot, message: Message):
    keyboard = Keyboard()
    btn_0 = InlineKeyboardButton(text="static", callback_data="static")
    btn_1 = InlineKeyboardButton(text="regex", callback_data="regex-abc123")
    btn_2 = InlineKeyboardButton(
        text="callable", callback_data=build_callback_data("callable", "match")
    )
    keyboard.add_buttons(btn_0, btn_1, btn_2)
    bot.send_message(
        chat_id=message.chat.id,
        text="select one",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard.layout),
    )


@router.callback_query_handler(static_match="static")
def on_static_match(bot: SimpleBot, callback_query: CallbackQuery):
    bot.answer_callback_query(callback_query_id=callback_query.id)
    bot.send_message(chat_id=callback_query.from_user.id, text="your select matches 'static'")


@router.callback_query_handler(regex_match={r"^regex-.*"})
def on_regex_match(bot: SimpleBot, callback_query: CallbackQuery, result):
    bot.answer_callback_query(callback_query_id=callback_query.id)
    bot.send_message(
        chat_id=callback_query.from_user.id, text="your matche result is {0}".format(result)
    )


@router.callback_query_handler(callable_match=parse_callback_data, name="callable")
def on_callable_match(bot: SimpleBot, callback_query: CallbackQuery, callback_data_args):
    bot.answer_callback_query(callback_query_id=callback_query.id)
    bot.send_message(
        chat_id=callback_query.from_user.id,
        text="your select matches {0}".format(callback_data_args),
    )


example_bot.run_polling(timeout=10)
