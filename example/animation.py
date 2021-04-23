"""
run in terminal: python -m example.animation.py
"""
import logging

from simplebot import SimpleBot, bot_proxy
from simplebot.base import Message, MessageField

from example.settings import BOT_TOKEN

logger = logging.getLogger("simple-bot")
logger.setLevel(logging.DEBUG)

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


@router.message_handler(fields=MessageField.ANIMATION & MessageField.DOCUMENT)
def on_animation(bot: SimpleBot, message: Message):
    bot.send_message(
        chat_id=message.chat.id,
        text="receive a animation from {0}".format(message.chat.first_name),
    )


print(router)
example_bot.run_polling(timeout=10)
