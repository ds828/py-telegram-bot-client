# run: python -m example.confirm
from telegrambotclient import bot_client
from telegrambotclient.base import MessageField
from telegrambotclient.ui import Confirm, InlineKeyboard

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


@router.message_handler(fields=MessageField.TEXT)
def on_show_keyboard(bot, message):
    buttons = Confirm.create("my-confirm", "I confirm it")
    keyboard = InlineKeyboard()
    keyboard.add_buttons(*buttons)
    bot.send_message(chat_id=message.from_user.id,
                     text="Please confirm",
                     reply_markup=keyboard.markup())
    return bot.stop_call


@router.callback_query_handler(callback_data_name="my-confirm")
def on_click(bot, callback_query, confirm, value):
    bot.send_message(chat_id=callback_query.from_user.id,
                     text="click {0} with {1}".format(
                         "OK" if confirm else "Cancel", value))
    return bot.stop_call


bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(timeout=10)
