"""
run: python -m example.next_or_stop
"""
from telegrambotclient import bot_client
from telegrambotclient.base import MessageField

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


@router.command_handler(("/cmd", ))
def on_cmd(bot, message):
    bot.send_message(chat_id=message.chat.id,
                     text="on_cmd: {0}".format(message.text))
    return bot.next_call  # next_call will call on_text which is the next matched handler


@router.message_handler(MessageField.TEXT)
def on_text(bot, message):
    bot.send_message(chat_id=message.chat.id,
                     text="on_text: {0}".format(message.text))
    return bot.stop_call


async def on_update(bot, update):
    await router.dispatch(bot, update)


bot = bot_client.create_bot(token=BOT_TOKEN)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(on_update, timeout=10)
