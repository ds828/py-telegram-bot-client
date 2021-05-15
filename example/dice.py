"""
run in terminal: python -m example.dice
"""
from telegrambotclient import bot_client
from telegrambotclient.base import Emoji

from example.settings import BOT_TOKEN

router = bot_client.router()
example_bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


@router.message_handler()
def on_example(bot, message):
    for _ in list(Emoji):
        bot.send_dice(message.chat.id, _)


example_bot.run_polling(timeout=10)
