"""
run in terminal: python -m example.callback_query.py
"""
from simplebot import SimpleBot, bot_proxy
from simplebot.base import (CallbackQuery, InlineKeyboardButton, Message,
                            MessageField)
from simplebot.ui import InlineKeyboard
from simplebot.utils import (build_callback_data, parse_callback_data,
                             pretty_print)

from example.settings import BOT_TOKEN

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


@router.message_handler(fields=(MessageField.TEXT, ))
def on_select(bot: SimpleBot, message: Message):
    keyboard = InlineKeyboard()
    btn_0 = InlineKeyboardButton(text="all match", callback_data="static")
    btn_1 = InlineKeyboardButton(
        text="start match",
        callback_data=build_callback_data("start-with-me", "value", 100),
    )

    btn_2 = InlineKeyboardButton(text="regex", callback_data="regex-abc123")
    btn_3 = InlineKeyboardButton(text="callable",
                                 callback_data=build_callback_data(
                                     "callable", "callable_arg"))
    keyboard.add_buttons(btn_0, btn_1, btn_2, btn_3)
    bot.send_message(chat_id=message.chat.id,
                     text="select one",
                     reply_markup=keyboard.markup())


@router.callback_query_handler(all_match="static")
def on_static_match(bot: SimpleBot, callback_query: CallbackQuery):
    bot.answer_callback_query(callback_query_id=callback_query.id)
    bot.send_message(chat_id=callback_query.from_user.id,
                     text="your select matches 'static'")


@router.callback_query_handler(start_match="start-with-me")
def on_start_match(bot: SimpleBot, callback_query: CallbackQuery,
                   value_str: str, value_int: int):
    bot.answer_callback_query(callback_query_id=callback_query.id)
    bot.send_message(
        chat_id=callback_query.from_user.id,
        text="your match result are: {0} {1}".format(value_str, value_int),
    )


@router.callback_query_handler(regex_match={r"^regex-.*"})
def on_regex_match(bot: SimpleBot, callback_query: CallbackQuery, result):
    bot.answer_callback_query(callback_query_id=callback_query.id)
    bot.send_message(
        chat_id=callback_query.from_user.id,
        text="your match result is {0}".format(result),
    )


@router.callback_query_handler(callable_match=parse_callback_data,
                               name="callable")
def on_callable_match(bot: SimpleBot, callback_query: CallbackQuery,
                      *callback_data_args):
    bot.answer_callback_query(callback_query_id=callback_query.id)
    bot.send_message(
        chat_id=callback_query.from_user.id,
        text="your select matches {0}".format(callback_data_args),
    )


pretty_print(router)
example_bot.run_polling(timeout=10)
