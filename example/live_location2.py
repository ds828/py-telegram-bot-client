"""
run in terminal: python -m example.live_location2.py
"""
import random
from simplebot import bot_proxy, SimpleBot
from simplebot.base import MessageField, Message

from example.settings import BOT_TOKEN

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


# for testing, a user share his location to touch off the bot to share live loctions
@router.message_handler(fields=(MessageField.LOCATION,))
def on_share_user_location(bot: SimpleBot, message: Message):
    if "live_period" in message.location:
        # filter off live location messages
        return
    # the bot sends a shareing live locations message with a faked location
    sent_message = bot.send_location(
        chat_id=message.chat.id,
        latitude=message.location.latitude + 0.01,
        longitude=message.location.longitude + 0.01,
        live_period=900,
    )
    session = bot.get_session(message.chat.id)
    # save this message id into session
    session["message_id"] = sent_message.message_id


# next, the user's telegram app will show a sharing locations between him and the bot.
# if the user shares his live locations, here is to simulate the bot's movement
@router.edited_message_handler(fields=(MessageField.LOCATION,))
def on_live_location(bot: SimpleBot, edited_message: Message):
    session = bot.get_session(edited_message.chat.id)
    message_id = session["message_id"]
    # use the user's location to make some faked locations
    if "live_period" in edited_message.location:
        print(edited_message.location, edited_message.edit_date)
        location = edited_message.location
        offset = random.randrange(1, 9) / 100
        bot.edit_message_live_location(
            chat_id=edited_message.chat.id,
            message_id=message_id,
            latitude=location.latitude + offset,
            longitude=location.longitude + offset,
            heading=location.heading + 45,
            horizontal_accuracy=location.horizontal_accuracy,
        )
    else:
        print("stop to share live locations")
        bot.stop_message_live_location(
            chat_id=edited_message.chat.id,
            message_id=message_id,
        )


example_bot.run_polling(timeout=10)
