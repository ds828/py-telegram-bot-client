"""
run in terminal: python -m example.animation.py
"""
import logging
from simplebot import bot_proxy, SimpleBot
from simplebot.base import Message, MessageField

from example.settings import BOT_TOKEN

logger = logging.getLogger("simple-bot")
logger.setLevel(logging.DEBUG)

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)

# when animation field is set, the document field will also be set
# For this reason, pass all_in=True, so the handler will process the messages which have all fields
@router.message_handler(
    fields=set(
        (
            MessageField.ANIMATION,
            MessageField.DOCUMENT,
        )
    )
)
def on_animation(bot: SimpleBot, message: Message):
    bot.send_message(
        chat_id=message.chat.id,
        text="receive a animation from {0}".format(message.chat.first_name),
    )


example_bot.run_polling(timeout=10)
