"""
first, add your bot into a group
if your group is privacy mode, your bot will not receive any messages from the group
so make your bot be a group admin after running
run in terminal: python -m example.group_chat
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


@router.message_handler(fields=MessageField.GROUP_CHAT_CREATED)
def on_group_chat_creted(bot: TelegramBot, message: Message):
    bot.reply_message(
        message,
        text="Thanks, I am in this group",
        parse_mode=ParseMode.HTML,
    )


@router.message_handler(fields=MessageField.TEXT)
def on_text_group_message(bot: TelegramBot, message: Message):
    bot.reply_message(
        message,
        text="I receive a text message: <strong>{0}</strong>".format(
            message.text),
        parse_mode=ParseMode.HTML,
    )


example_bot.run_polling(timeout=10)
