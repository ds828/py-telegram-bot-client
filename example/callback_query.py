"""
run: python -m example.callback_query
"""
import logging

from telegrambotclient import bot_client
from telegrambotclient.base import InlineKeyboardButton, MessageField
from telegrambotclient.ui import InlineKeyboard
from telegrambotclient.utils import build_callback_data

BOT_TOKEN = "<BOT_TOKEN>"
router = bot_client.router()


@router.message_handler(MessageField.TEXT)
def on_show_items(bot, message):
    btn_0 = InlineKeyboardButton(text="some data", callback_data="some data")
    btn_1 = InlineKeyboardButton(text="my btn 1",
                                 callback_data=build_callback_data(
                                     "my-btn", "one", 1, True, {"a": 1}))
    btn_2 = InlineKeyboardButton(text="my btn 2",
                                 callback_data=build_callback_data(
                                     "my-btn", "two", 2, False, {"b": 2}))

    keyboard = InlineKeyboard([[btn_0], [btn_1, btn_2]])
    bot.send_message(chat_id=message.chat.id,
                     text="select one",
                     reply_markup=keyboard.markup())
    return bot.stop_call


@router.callback_query_handler(callback_data="some data")
def on_callback_data_0(bot, callback_query):
    bot.answer_callback_query(callback_query_id=callback_query.id)
    #replace btn_0 with new_btn
    keyboard = InlineKeyboard(
        callback_query.message.reply_markup.inline_keyboard)
    new_btn = InlineKeyboardButton(text="new data", callback_data="new data")
    if keyboard.replace(callback_query.data, new_btn):
        print("replaced")
    bot.send_message(chat_id=callback_query.from_user.id,
                     text="your select is matched by {}".format(
                         callback_query.data),
                     reply_markup=keyboard.markup())
    return bot.stop_call


@router.callback_query_handler(callback_data="new data")
def on_callback_data_1(bot, callback_query):
    bot.answer_callback_query(callback_query_id=callback_query.id)
    keyboard = InlineKeyboard(
        callback_query.message.reply_markup.inline_keyboard)
    # locate the button
    row_idx, col_idx = keyboard.where(callback_query.data)
    print(keyboard[row_idx][col_idx])
    new_btn = InlineKeyboardButton(text="some data", callback_data="some data")
    # replace it
    keyboard[row_idx][col_idx] = new_btn
    bot.send_message(chat_id=callback_query.from_user.id,
                     text="your select is matched by {}".format(
                         callback_query.data),
                     reply_markup=keyboard.markup())
    return bot.stop_call


@router.callback_query_handler(callback_data="my-btn")
def on_callback_data_name(bot, callback_query, *values):
    bot.answer_callback_query(callback_query_id=callback_query.id)
    keyboard = InlineKeyboard(
        callback_query.message.reply_markup.inline_keyboard)
    # find buttons
    buttons = keyboard.group("my-btn")
    print(buttons)
    # remove this button you click
    if keyboard.remove(callback_query.data):
        print("removed")

    bot.send_message(chat_id=callback_query.from_user.id,
                     text="your select and remove: my-btn: {0}".format(values),
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
