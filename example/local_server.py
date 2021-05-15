"""
run in terminal: python -m example.local_server
"""
import logging

from telegrambotclient import bot_client
from telegrambotclient.api import TelegramBotAPI
from telegrambotclient.base import MessageField, ParseMode

from example.settings import BOT_TOKEN

logger = logging.getLogger("telegram-bot-client")
logger.setLevel(logging.DEBUG)

router = bot_client.router()


@router.message_handler(fields=MessageField.TEXT)
def on_echo_text(bot, message):
    bot.reply_message(
        message,
        text="I receive: <strong>{0}</strong>".format(message.text),
        parse_mode=ParseMode.HTML,
    )


bot_api = TelegramBotAPI()
bot_api.delete_webhook(drop_pending_updates=True)
if bot_api.log_out():
    local_bot = bot_client.create_bot(
        token=BOT_TOKEN,
        router=router,
        bot_api=TelegramBotAPI(api_host="YOUR-LOCAL-API-HOST"))
    local_bot.run_polling(timeout=10)
