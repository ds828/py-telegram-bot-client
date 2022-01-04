"""
run: python -m example.dice
"""
from telegrambotclient import bot_client
from telegrambotclient.base import Emoji

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


@router.message_handler()
def on_example(bot, message):
    for _ in Emoji.__members__.values():
        bot.send_dice(chat_id=message.chat.id, emoji=_)
    return bot.stop_call


async def on_update(bot, update):
    await router.dispatch(bot, update)


bot = bot_client.create_bot(token=BOT_TOKEN)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(on_update, timeout=10)
