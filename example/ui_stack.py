"""
run: python -m example.ui_stack
"""
from telegrambotclient import bot_client
from telegrambotclient.base import InlineKeyboardButton, MessageField
from telegrambotclient.ui import InlineKeyboard

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


@router.message_handler(fields=MessageField.TEXT)
def on_show_ui_01(bot, message):
    keyboard = InlineKeyboard()
    btn = InlineKeyboardButton(text="next", callback_data="next")
    keyboard.add_buttons(btn)
    bot.send_message(chat_id=message.chat.id,
                     text="go to next",
                     reply_markup=keyboard.markup())


@router.callback_query_handler(callback_data="next")
def on_show_ui_02(bot, callback_query):
    bot.push_ui(callback_query.from_user.id, callback_query.message)
    keyboard = InlineKeyboard()
    btn = InlineKeyboardButton(text="back", callback_data="back")
    keyboard.add_buttons(btn)
    bot.edit_message_text(chat_id=callback_query.from_user.id,
                          message_id=callback_query.message.message_id,
                          text="back",
                          reply_markup=keyboard.markup())


@router.callback_query_handler(callback_data="back")
def on_back_ui_01(bot, callback_query):
    message = bot.pop_ui(callback_query.from_user.id)
    bot.edit_message_text(chat_id=callback_query.from_user.id,
                          message_id=callback_query.message.message_id,
                          text=message["text"],
                          reply_markup=message["reply_markup"])


bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(timeout=10)
