"""
run: python -m example.callback_query
"""
import logging

from telegrambotclient import bot_client
from telegrambotclient.base import InlineKeyboardButton, MessageField
from telegrambotclient.ui import InlineKeyboard
from telegrambotclient.utils import build_callback_data

BOT_TOKEN = "<BOT_TOKEN>"

# create a default router
router = bot_client.router()


@router.message_handler(MessageField.TEXT)
def on_show_items(bot, message):
    btn_0 = InlineKeyboardButton(text="match with callback_data",
                                 callback_data="some data")
    btn_1 = InlineKeyboardButton(text="match with callback_data_name",
                                 callback_data=build_callback_data(
                                     "my-callback-data-name", "one value", 100,
                                     True, {"a": 1}))
    keyboard = InlineKeyboard((btn_0, btn_1), )
    bot.send_message(chat_id=message.chat.id,
                     text="select one",
                     reply_markup=keyboard.markup())


@router.callback_query_handler(callback_data="some data")
def on_match_callback_data_1(bot, callback_query):
    bot.answer_callback_query(callback_query_id=callback_query.id)
    #replace btn_0 with new_btn
    new_btn = InlineKeyboardButton(text="new data", callback_data="new data")
    keyboard = InlineKeyboard(
        *callback_query.message.reply_markup.inline_keyboard)
    if keyboard.replace(callback_query.data, new_btn):
        print("replaced")
    bot.send_message(chat_id=callback_query.from_user.id,
                     text="your select is matched by {}".format(
                         callback_query.data),
                     reply_markup=keyboard.markup())
    return bot.stop_call


@router.callback_query_handler(callback_data="new data")
def on_match_callback_data_2(bot, callback_query):
    bot.answer_callback_query(callback_query_id=callback_query.id)
    keyboard = InlineKeyboard(
        *callback_query.message.reply_markup.inline_keyboard)
    # locate the button
    row_idx, col_idx = keyboard.where(callback_query.data)
    print(keyboard[row_idx][col_idx])
    bot.send_message(chat_id=callback_query.from_user.id,
                     text="your select is matched by {}".format(
                         callback_query.data))
    return bot.stop_call


@router.callback_query_handler(callback_data="my-callback-data-name")
def on_match_callback_data_name(bot, callback_query, *values):
    bot.answer_callback_query(callback_query_id=callback_query.id)
    # remove btn_1
    keyboard = InlineKeyboard(
        *callback_query.message.reply_markup.inline_keyboard)
    if keyboard.remove(callback_query.data):
        print("removed")

    bot.send_message(
        chat_id=callback_query.from_user.id,
        text="your select is matched by my-callback-data-name: {0}".format(
            values),
        reply_markup=keyboard.markup())
    return bot.stop_call


async def on_update(bot, update):
    await router.dispatch(bot, update)


logger = logging.getLogger("telegram-bot-client")
logger.setLevel(logging.DEBUG)
logger.debug(router)
bot = bot_client.create_bot(token=BOT_TOKEN)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(on_update, timeout=10)
