"""
run: python -m example.callback_query
"""
import logging

from telegrambotclient import bot_client
from telegrambotclient.base import InlineKeyboardButton, InlineKeyboardMarkup
from telegrambotclient.ui import InlineKeyboard
from telegrambotclient.utils import build_callback_data

BOT_TOKEN = "<BOT_TOKEN>"

# create a default router
router = bot_client.router()


@router.message_handler()
def on_show_items(bot, message):
    btn_0 = InlineKeyboardButton(text="match all callback data",
                                 callback_data="full match")
    btn_1 = InlineKeyboardButton(text="match the callback data name",
                                 callback_data=build_callback_data(
                                     "callback-data-name", "one value", 100,
                                     True, {"a": 1}))
    keyboard = InlineKeyboard((btn_0, btn_1), )
    bot.send_message(chat_id=message.chat.id,
                     text="select one",
                     reply_markup=keyboard.markup())


@router.callback_query_handler(callback_data="full match")
def on_match_all(bot, callback_query):
    bot.answer_callback_query(callback_query_id=callback_query.id)
    bot.send_message(chat_id=callback_query.from_user.id,
                     text="your select matches all text of a callback_data",
                     reply_markup=InlineKeyboardMarkup(
                         inline_keyboard=callback_query.message.reply_markup.
                         inline_keyboard))


@router.callback_query_handler(callback_data="callback-data-name")
def on_match_name(bot, callback_query, *values):
    bot.answer_callback_query(callback_query_id=callback_query.id)
    bot.send_message(chat_id=callback_query.from_user.id,
                     text="callback-data-name: {0}".format(values),
                     reply_markup=InlineKeyboardMarkup(
                         inline_keyboard=callback_query.message.reply_markup.
                         inline_keyboard))


logger = logging.getLogger("telegram-bot-client")
logger.setLevel(logging.DEBUG)
logger.debug(router)
bot = bot_client.create_bot(token=BOT_TOKEN)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(timeout=10)
