"""
first, add your bot into a channel
run in terminal: python -m example.channel_post.py
"""
import logging
from example.settings import BOT_TOKEN
from simplebot import bot_proxy, SimpleBot
from simplebot.base import MessageField, Message, ParseMode


logger = logging.getLogger("simple-bot")
logger.setLevel(logging.DEBUG)

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


@router.channel_post_handler(fields=(MessageField.TEXT,))
def on_channel_post(bot: SimpleBot, message: Message):
    bot.reply_message(
        message,
        text="I receive a channel post: <strong>{0}</strong>".format(message.text),
        parse_mode=ParseMode.HTML,
    )


@router.edited_channel_post_handler(fields=(MessageField.TEXT,))
def on_edited_channel_post(bot: SimpleBot, message: Message):
    bot.reply_message(
        message,
        text="I receive a edited channel post: <strong>{0}</strong>".format(message.text),
        parse_mode=ParseMode.HTML,
    )


example_bot.run_polling(timeout=10)
