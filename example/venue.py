"""
run in terminal: python -m example.venue.py
for testing this, you can share a venue to this bot though @foursquare
"""
import logging

from simplebot import SimpleBot, bot_proxy
from simplebot.base import Message, MessageField
from simplebot.utils import pretty_print

from example.settings import BOT_TOKEN

logger = logging.getLogger("simple-bot")
logger.setLevel(logging.DEBUG)

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


# when venue field is set, the location field will also be set
# For this reason, use a set as fields, items in set have a AND relationship
# all are same
# @router.message_handler(fields={"venue", "location"})
# @router.message_handler(fields={MessageField.VENUE, MessageField.LOCATION})
@router.message_handler(fields=MessageField.VENUE & MessageField.LOCATION)
def on_venue(bot: SimpleBot, message: Message):
    pretty_print(message)


example_bot.run_polling(timeout=10)
