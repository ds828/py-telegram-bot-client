"""
run: python -m example.animation
A animation file is GIF or H.264/MPEG-4 AVC video without sound
"""
import logging

from telegrambotclient import bot_client
from telegrambotclient.base import MessageField

BOT_TOKEN = "<BOT_TOKEN>"

logger = logging.getLogger("telegram-bot-client")
logger.setLevel(logging.DEBUG)

router = bot_client.router()


@router.message_handler(fields=MessageField.ANIMATION & MessageField.DOCUMENT)
def on_animation(bot, message):
    logger.debug(bot.get_file(file_id=message.animation.file_id))
    bot.reply_message(
        message,
        text="a nice animation from {0}".format(message.chat.first_name),
    )


bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(timeout=10)
