"""
first, add your bot into a group
If your group is privacy mode, your bot will NOT receive any messages from the group, make your bot be a group admin after running
run: python -m example.group_chat
"""
import logging

from telegrambotclient import bot_client
from telegrambotclient.base import MessageField, ParseMode

BOT_TOKEN = "<BOT_TOKEN>"

logger = logging.getLogger("telegram-bot-client")
logger.setLevel(logging.DEBUG)

router = bot_client.router()


@router.message_handler(MessageField.GROUP_CHAT_CREATED)
def on_group_chat_created(bot, message):
    bot.reply_message(message, text="Thanks, I am in this group")
    return bot.stop_call


@router.message_handler(MessageField.TEXT)
def on_text_group_message(bot, message):
    bot.reply_message(
        message,
        text="I receive a text message: <strong>{0}</strong>".format(
            message.text),
        parse_mode=ParseMode.HTML)
    return bot.stop_call


async def on_update(bot, update):
    await router.dispatch(bot, update)


bot = bot_client.create_bot(token=BOT_TOKEN)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(on_update, timeout=10)
