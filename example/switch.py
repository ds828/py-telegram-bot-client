"""
run: python -m example.switch
"""
from telegrambotclient import bot_client
from telegrambotclient.base import InlineKeyboardButton, MessageField
from telegrambotclient.ui import InlineKeyboard
from telegrambotclient.utils import build_callback_data, parse_callback_data

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()
emoji = ("✔️", "❌")


@router.message_handler(fields=MessageField.TEXT)
def on_show_keyboard(bot, message):
    keyboard = InlineKeyboard()
    keyboard.add_buttons(
        InlineKeyboardButton(text="{0}status".format(emoji[0]),
                             callback_data=build_callback_data(
                                 "switch", 123, True)))
    keyboard.add_buttons(
        InlineKeyboardButton(text="submit", callback_data="submit"))
    bot.send_message(chat_id=message.chat.id,
                     text="switch status: {0}".format(True),
                     reply_markup=keyboard.markup())
    return bot.stop_call


@router.callback_query_handler(callback_data="switch")
def on_change(bot, callback_query, value, selected):
    keyboard = InlineKeyboard(
        *callback_query.message.reply_markup.inline_keyboard)
    new_button = InlineKeyboardButton(
        text="{0}status".format(emoji[1] if selected else emoji[0]),
        callback_data=build_callback_data("switch", value, not selected))
    if keyboard.replace(build_callback_data("switch", value, selected),
                        new_button):

        bot.edit_message_text(chat_id=callback_query.from_user.id,
                              message_id=callback_query.message.message_id,
                              text="switch status: {0}".format(not selected),
                              reply_markup=keyboard.markup())
    return bot.stop_call


@router.callback_query_handler(callback_data="submit")
def on_submit(bot, callback_query):
    keyboard = InlineKeyboard(
        *callback_query.message.reply_markup.inline_keyboard)
    for button in keyboard.get_buttons("switch"):
        callback_data_name, value, selected = parse_callback_data(
            button.callback_data)
        message_text = "callback_data_name={0} value={1} selected={2}".format(
            callback_data_name, value, selected)
        bot.send_message(
            chat_id=callback_query.from_user.id,
            text=message_text,
        )
    return bot.stop_call


bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(timeout=10)
