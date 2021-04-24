"""
run in terminal: python -m example.deep_linking
deep linking: https://t.me/<YOUR-BOT-USERNAME>?start=test
"""
import logging

from telegrambotclient import TelegramBot, bot_client
from telegrambotclient.base import BotCommand, Message

from example.settings import BOT_TOKEN

logger = logging.getLogger("telegram-bot-client")
logger.setLevel(logging.DEBUG)

router = bot_client.router()
example_bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)
cmd_start = BotCommand(command="/start", description="start to talk")
cmd_help = BotCommand(command="/help", description="help")
example_bot.set_my_commands(commands=(cmd_start, cmd_help))


@router.command_handler(("/start", ))
def on_start(bot: TelegramBot, message: Message, *payload):
    print(payload)
    bot.reply_message(message, text=message.text)


@router.command_handler(("/help", ))
def on_help(bot: TelegramBot, message: Message):
    bot.send_message(chat_id=message.chat.id, text="help me how to use")


example_bot.run_polling(timeout=10)
