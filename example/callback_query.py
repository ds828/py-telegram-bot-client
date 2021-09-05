"""
run: python -m example.callback_query
"""
import json

from telegrambotclient import bot_client
from telegrambotclient.base import InlineKeyboardButton, MessageField
from telegrambotclient.ui import InlineKeyboard
from telegrambotclient.utils import build_callback_data

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


@router.message_handler(fields=MessageField.TEXT)
def on_select(bot, message):
    btn_0 = InlineKeyboardButton(text="match all callback data",
                                 callback_data="match-all")
    btn_1 = InlineKeyboardButton(
        text="match the callback data name",
        callback_data=build_callback_data("a-callback-data-name", "one value",
                                          100),
    )

    btn_2 = InlineKeyboardButton(text="match callback datas with regex",
                                 callback_data="regex-abc123")
    btn_3 = InlineKeyboardButton(
        text="match callback datas with a parse function",
        callback_data=build_callback_data("callback-data-name", 123))
    keyboard = InlineKeyboard(btn_0, btn_1)
    keyboard.add_buttons(btn_2, btn_3)
    bot.send_message(chat_id=message.chat.id,
                     text="select one",
                     reply_markup=keyboard.markup())


@router.callback_query_handler(callback_data="match-all")
def on_static_match(bot, callback_query):
    bot.answer_callback_query(callback_query_id=callback_query.id)
    bot.send_message(chat_id=callback_query.from_user.id,
                     text="your select matches all text of a callback_data")


@router.callback_query_handler(callback_data_name="a-callback-data-name")
def on_start_match(bot, callback_query, value_str: str, value_int: int):
    bot.answer_callback_query(callback_query_id=callback_query.id)
    bot.send_message(
        chat_id=callback_query.from_user.id,
        text="you match a callback data name: {0} {1}".format(
            value_str, value_int),
    )


@router.callback_query_handler(callback_data_regex=(r"^regex-.*", ))
def on_regex_match(bot, callback_query, result):
    bot.answer_callback_query(callback_query_id=callback_query.id)
    bot.send_message(
        chat_id=callback_query.from_user.id,
        text="you match callback datas with regex: {0}".format(result),
    )


def parse_callback_data(callback_data: str, value: str):
    name_args = callback_data.split("|")
    if name_args[0] == value:
        return tuple(json.loads(name_args[1]))
    return None


@router.callback_query_handler(callback_data_parse=parse_callback_data,
                               value="callback-data-name")
def on_callable_match(bot, callback_query, arg: int):
    bot.answer_callback_query(callback_query_id=callback_query.id)
    bot.send_message(
        chat_id=callback_query.from_user.id,
        text="you matche a callback data with a parse: {0}".format(arg),
    )


print(router)
bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(timeout=10)
