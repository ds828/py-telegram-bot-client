"""
run in terminal: python -m example.animation.py
"""
import logging
from simplebot.utils import pretty_print
from simplebot import bot_proxy, SimpleBot
from simplebot.base import Message, MessageField

from example.settings import BOT_TOKEN

logger = logging.getLogger("simple-bot")
logger.setLevel(logging.DEBUG)

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)

# Message is an animation, information about the animation.
# For backward compatibility, when this field is set, the document field will also be set
# For this reason, use a set as fields, items in set have a AND relationship
@router.message_handler(fields={MessageField.ANIMATION, MessageField.DOCUMENT})
def on_animation(bot: SimpleBot, message: Message):
    pretty_print(message)


example_bot.run_polling(timeout=10)
