"""
run: python -m example.force_reply
"""
from telegrambotclient import bot_client
from telegrambotclient.base import ForceReply, MessageField

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


@router.message_handler(fields=MessageField.TEXT)
def on_force_reply(bot, message):
    bot.send_message(chat_id=message.chat.id,
                     text="reply something",
                     reply_markup=ForceReply())
    bot.join_force_reply(message.chat.id, on_callback_reply, 123, "value")
    return bot.stop_call


@router.force_reply_handler()
def on_callback_reply(bot, message, value_1, value_2):
    bot.reply_message(
        message,
        text="you reply: '{0}' and args: {1}, {2}".format(
            message.text, value_1, value_2),
    )
    # remove this force reply callback
    bot.force_reply_done(message.chat.id)
    return bot.stop_call


bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(timeout=10)
