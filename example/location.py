"""
run: python -m example.location
"""

from telegrambotclient import bot_client
from telegrambotclient.base import MessageField

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


@router.message_handler(MessageField.LOCATION)
def on_location(bot, message):
    bot.send_location(chat_id=message.chat.id,
                      latitude=message.location.latitude,
                      longitude=message.location.longitude)

    return bot.stop_call


async def on_update(bot, update):
    await router.dispatch(bot, update)


bot = bot_client.create_bot(token=BOT_TOKEN)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(on_update, timeout=10)
