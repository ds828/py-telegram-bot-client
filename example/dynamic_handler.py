"""
run: python -m example.dynamic_handler
"""
from telegrambotclient import bot_client
from telegrambotclient.base import InlineKeyboardButton, MessageField
from telegrambotclient.ui import InlineKeyboard

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


def on_callback_query_handler(bot, callback_query):
    bot.send_message(chat_id=callback_query.from_user.id,
                     text="callback query handler")
    return bot.stop_call


def on_location_message(bot, message):
    bot.send_message(chat_id=message.chat.id, text="I received a location")
    return bot.stop_call


@router.message_handler(fields=MessageField.TEXT)
def on_add_handler(bot, message):
    router.register_callback_query_handler(on_callback_query_handler,
                                           callback_data="callback")
    router.register_message_handler(on_location_message,
                                    fields=MessageField.LOCATION)

    keyboard = InlineKeyboard(
        InlineKeyboardButton(text="callback query", callback_data="callback"))
    bot.send_message(
        chat_id=message.chat.id,
        text=
        "Dynamicly register a callback query handler and a location message handler",
        reply_markup=keyboard.markup())
    return bot.stop_call


bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(timeout=10)
