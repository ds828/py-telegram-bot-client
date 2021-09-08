"""
run: python -m example.switch
"""
from telegrambotclient import bot_client
from telegrambotclient.base import InlineKeyboardButton, MessageField
from telegrambotclient.ui import InlineKeyboard, UIHelper

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


def on_switch_callback(bot, callback_query, value, status: bool):
    return "switch status: {0}, {1}".format(status, value)


switch_name = "my-switch"
UIHelper.setup_switch(router, switch_name, on_switch_callback)


@router.message_handler(fields=MessageField.TEXT)
def on_show_keyboard(bot, message):
    keyboard = InlineKeyboard(
        UIHelper.build_switch_button(switch_name,
                                     "my switch", ("abc", 123),
                                     status=True))
    keyboard.add_buttons(
        InlineKeyboardButton(text="submit", callback_data="submit"))
    bot.send_message(chat_id=message.chat.id,
                     text="switch status: {0}".format(True),
                     reply_markup=keyboard.markup())
    return bot.stop_call


@router.callback_query_handler(callback_data="submit")
def on_submit(bot, callback_query):
    status, value = UIHelper.lookup_switch(
        callback_query.message.reply_markup.inline_keyboard, switch_name)
    bot.send_message(
        chat_id=callback_query.from_user.id,
        text="switch status: {0}, {1}".format(status, value),
    )
    return bot.stop_call


bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(timeout=10)
