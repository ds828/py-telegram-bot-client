"""
run: python -m example.animation
A animation file is GIF or H.264/MPEG-4 AVC video without sound
"""
from telegrambotclient import bot_client
from telegrambotclient.base import MessageField
from telegrambotclient.utils import pretty_print

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


# Message is an animation, information about the animation.
# For backward compatibility, when this field is set, the document field will also be set
@router.message_handler(MessageField.ANIMATION, MessageField.DOCUMENT)
def on_animation(bot, message):
    pretty_print(bot.get_file(file_id=message.animation.file_id))
    bot.reply_message(
        message,
        text="a nice animation from {0}".format(message.chat.first_name),
    )
    return bot.stop_call


async def on_update(bot, update):
    await router.dispatch(bot, update)


bot = bot_client.create_bot(token=BOT_TOKEN)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(on_update, timeout=10)
