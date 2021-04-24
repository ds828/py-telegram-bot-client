"""
first, add your bot into a channel
run in terminal: python -m example.channel_post
"""
import logging

from telegrambotclient import TelegramBot, bot_client
from telegrambotclient.base import Message, MessageField, ParseMode

from example.settings import BOT_TOKEN

logger = logging.getLogger("telegram-bot-client")
logger.setLevel(logging.DEBUG)

router = bot_client.router()
example_bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


@router.channel_post_handler(fields=MessageField.TEXT)
def on_channel_post(bot: TelegramBot, message: Message):
    bot.reply_message(
        message,
        text="I receive a channel post: <strong>{0}</strong>".format(
            message.text),
        parse_mode=ParseMode.HTML,
    )


@router.edited_channel_post_handler(fields=MessageField.TEXT)
def on_edited_channel_post(bot: TelegramBot, message: Message):
    bot.reply_message(
        message,
        text="I receive a edited channel post: <strong>{0}</strong>".format(
            message.text),
        parse_mode=ParseMode.HTML,
    )


example_bot.run_polling(timeout=10)
