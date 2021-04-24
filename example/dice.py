"""
run in terminal: python -m example.dice
"""
from telegrambotclient import TelegramBot, bot_client
from telegrambotclient.base import Emoji, Message

from example.settings import BOT_TOKEN

router = bot_client.router()
example_bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


@router.message_handler()
def on_example(bot: TelegramBot, message: Message):
    bot.send_dice(message.chat.id, Emoji.DICE)
    bot.send_dice(message.chat.id, Emoji.BULLSEYE)
    bot.reply_dice(message.chat.id, Emoji.BASKETBALL)


example_bot.run_polling(timeout=10)
