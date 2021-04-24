"""
run in terminal: python -m example.venue
for testing this, you can share a venue to this bot though @foursquare
"""
import logging

from telegrambotclient import TelegramBot, bot_client
from telegrambotclient.base import Message, MessageField
from telegrambotclient.utils import pretty_print

from example.settings import BOT_TOKEN

logger = logging.getLogger("telegrambotclient")
logger.setLevel(logging.DEBUG)

router = bot_client.router()
example_bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


# when venue field is set, the location field will also be set
@router.message_handler(fields=MessageField.VENUE & MessageField.LOCATION)
def on_venue(bot: TelegramBot, message: Message):
    pretty_print(message)


example_bot.run_polling(timeout=10)
