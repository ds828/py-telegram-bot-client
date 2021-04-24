"""
run in terminal: python -m example.next_or_stop
"""
import logging

from telegrambotclient import TelegramBot, bot_client
from telegrambotclient.base import Message, MessageField

from example.settings import BOT_TOKEN

logger = logging.getLogger("telegram-bot-client")
logger.setLevel(logging.DEBUG)

router = bot_client.router()
example_bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


@router.command_handler(("/cmd", ))
def on_cmd(bot: TelegramBot, message: Message):
    bot.send_message(chat_id=message.chat.id,
                     text="on_cmd: {0}".format(message.text))
    return bot.next_call  # will call on_text which is the next matched handler


@router.message_handler(fields=MessageField.TEXT)
def on_text(bot: TelegramBot, message: Message):
    bot.send_message(chat_id=message.chat.id,
                     text="on_text: {0}".format(message.text))
    return bot.stop_call  # normally, do not need it


example_bot.run_polling(timeout=10)
