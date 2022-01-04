"""
run: python -m example.live_location2
"""
import random

from telegrambotclient import bot_client
from telegrambotclient.base import MessageField

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


# for this testing, a user shares a current location to make the bot share live loctions as well
@router.message_handler(MessageField.LOCATION)
def on_share_user_location(bot, message):
    if "live_period" in message.location:
        # we do not need live location messages
        return bot.stop_call
    # the bot sends a shareing live locations message with a random location
    sent_message = bot.send_location(
        chat_id=message.chat.id,
        latitude=message.location.latitude + 0.01,
        longitude=message.location.longitude + 0.01,
        live_period=900,
    )
    session = bot.get_session(message.chat.id)
    # save the sent message id
    session["message_id"] = sent_message.message_id
    session.save()
    return bot.stop_call


# next, your telegram app will show a sharing locations between you and the bot.
# if a live location you shared, using a random location to simulate the bot's movement
@router.edited_message_handler(MessageField.LOCATION)
def on_live_location(bot, edited_message):
    session = bot.get_session(edited_message.chat.id)
    message_id = session["message_id"]
    if "live_period" in edited_message.location:
        print(edited_message.location, edited_message.edit_date)
        location = edited_message.location
        offset = random.randrange(1, 9) / 100
        # use your location to make a dummy location and heading
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
    return bot.stop_call


async def on_update(bot, update):
    await router.dispatch(bot, update)


bot = bot_client.create_bot(token=BOT_TOKEN)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(on_update, timeout=10)
