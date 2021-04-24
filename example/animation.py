"""
run in terminal: python -m example.animation
"""
import logging

from telegrambotclient import TelegramBot, bot_client
from telegrambotclient.base import Message, MessageField

from example.settings import BOT_TOKEN

logger = logging.getLogger("telegram-bot-client-bot")
logger.setLevel(logging.DEBUG)

router = bot_client.router()
example_bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


@router.message_handler(fields=MessageField.ANIMATION & MessageField.DOCUMENT)
def on_animation(bot: TelegramBot, message: Message):
    bot.send_message(
        chat_id=message.chat.id,
        text="receive a animation from {0}".format(message.chat.first_name),
    )


print(router)
example_bot.run_polling(timeout=10)
