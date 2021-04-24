"""
run in terminal: python -m example.live_location
"""

from telegrambotclient import TelegramBot, bot_client
from telegrambotclient.base import Message, MessageField

from example.settings import BOT_TOKEN

router = bot_client.router()
example_bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


# when a live location start to be shared
# the telegram bot server will send a location message which has a 'live_period' field firstly
@router.message_handler(fields=MessageField.LOCATION)
def on_share_location(bot: TelegramBot, message: Message):
    if "live_period" in message.location:
        # begin to share a live location
        print("start to share live locations")


# next, the bot will receive edited messages as live location updates.
# if a sharing live location is stopped, the bot will receive a location edited message without a 'live_period' field.
@router.edited_message_handler(fields=MessageField.LOCATION)
def on_live_location(bot: TelegramBot, edited_message: Message):
    if "live_period" in edited_message.location:
        print(edited_message.location, edited_message.edit_date)
    else:
        print("stop to share live locations")


example_bot.run_polling(timeout=10)
