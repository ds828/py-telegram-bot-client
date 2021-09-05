"""
run: python -m example.venue
for testing, you can share a venue with this bot though @foursquare bot
"""
from telegrambotclient import bot_client
from telegrambotclient.base import MessageField
from telegrambotclient.utils import pretty_print

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


# when a venue field is set, a location field is set as well
@router.message_handler(fields=MessageField.VENUE & MessageField.LOCATION)
def on_venue(bot, message):
    pretty_print(message)
    bot.send_venue(chat_id=message.chat.id, )
    return bot.stop_call


bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(timeout=10)
