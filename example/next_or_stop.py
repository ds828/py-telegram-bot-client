"""
run in terminal: python -m example.next_or_stop.py
"""
import logging

from simplebot import SimpleBot, bot_proxy
from simplebot.base import Message, MessageField

from example.settings import BOT_TOKEN

logger = logging.getLogger("simple-bot")
logger.setLevel(logging.DEBUG)

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


@router.command_handler(("/cmd", ))
def on_cmd(bot: SimpleBot, message: Message):
    bot.send_message(chat_id=message.chat.id,
                     text="on_cmd: {0}".format(message.text))
    return bot.next_call


@router.message_handler(fields=MessageField.TEXT)
def on_text(bot: SimpleBot, message: Message):
    bot.send_message(chat_id=message.chat.id,
                     text="on_text: {0}".format(message.text))
    return bot.stop_call  # do not needt or if you like


example_bot.run_polling(timeout=10)
