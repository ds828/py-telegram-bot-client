"""
run: python -m example.live_location
"""

from telegrambotclient import bot_client
from telegrambotclient.base import MessageField

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


# when a live location start to be shared
# the telegram bot server will send a location message which has a 'live_period' field firstly
@router.message_handler(fields=MessageField.LOCATION)
def on_share_location(bot, message):
    if "live_period" in message.location:
        # begin to share a live location
        print("start to share live locations")
    return bot.stop_call


# next, the bot will receive edited messages as live location updates.
# if a sharing live location is stopped, the bot will receive a location edited message without a 'live_period' field.
@router.edited_message_handler(fields=MessageField.LOCATION)
def on_live_location(bot, edited_message):
    if "live_period" in edited_message.location:
        print(edited_message.location, edited_message.edit_date)
    else:
        print("stop to share live locations")

    return bot.stop_call


async def on_update(bot, update):
    await router.dispatch(bot, update)


bot = bot_client.create_bot(token=BOT_TOKEN)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(on_update, timeout=10)
