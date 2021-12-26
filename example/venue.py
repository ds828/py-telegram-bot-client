"""
run: python -m example.venue
for testing, you can share a venue with this bot though @foursquare bot
"""
from telegrambotclient import bot_client
from telegrambotclient.base import MessageField
from telegrambotclient.utils import pretty_print

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


# https://core.telegram.org/bots/api#message --> venue
# Message is a venue, information about the venue.
# For backward compatibility, when this field is set, the location field will also be set
@router.message_handler(MessageField.VENUE, MessageField.LOCATION)
def on_venue(bot, message):
    pretty_print(message)
    return bot.stop_call


async def on_update(bot, update):
    await router.dispatch(bot, update)


bot = bot_client.create_bot(token=BOT_TOKEN)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(on_update, timeout=10)
