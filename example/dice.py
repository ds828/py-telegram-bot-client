"""
run in terminal: python -m example.dice.py
"""
from simplebot import bot_proxy, SimpleBot
from simplebot.base import Message, Emoji
from example.settings import BOT_TOKEN

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


@router.message_handler()
def on_example(bot: SimpleBot, message: Message):
    bot.send_dice(message.chat.id, Emoji.DICE)
    bot.send_dice(message.chat.id, Emoji.BULLSEYE)
    bot.reply_dice(message.chat.id, Emoji.BASKETBALL)


example_bot.run_polling(timeout=10)
