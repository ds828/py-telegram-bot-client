"""
run in terminal: python -m example.deep_linking.py
deep linking: https://t.me/<YOUR-BOT-USERNAME>?start=test
"""
import logging
from example.settings import BOT_TOKEN
from simplebot import bot_proxy, SimpleBot
from simplebot.base import BotCommand, Message

logger = logging.getLogger("simple-bot")
logger.setLevel(logging.DEBUG)

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)
cmd_start = BotCommand(command="/start", description="start to talk")
cmd_help = BotCommand(command="/help", description="help")
example_bot.set_my_commands(commands=(cmd_start, cmd_help))


@router.command_handler(("/start",))
def on_start(bot: SimpleBot, message: Message, *payload):
    print(payload)
    bot.reply_message(message, text=message.text)


@router.command_handler(("/help",))
def on_help(bot: SimpleBot, message: Message):
    bot.send_message(chat_id=message.chat.id, text="help me how to use")


example_bot.run_polling(timeout=10)
