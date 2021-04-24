"""
run in terminal: python -m example.command
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
cmd1 = BotCommand(command="/mycmd1", description="cmd1")
cmd2 = BotCommand(command="/mycmd2", description="cmd2 value1 value2")
example_bot.set_my_commands(commands=(cmd1, cmd2))


@router.command_handler(("/mycmd1", ))
def on_mycmd1(bot: TelegramBot, message: Message):
    bot.reply_message(message, text=message.text)


@router.command_handler(("/mycmd2", ))
def on_mycmd2(bot: TelegramBot, message: Message, *cmd_args):
    print(cmd_args)
    bot.reply_message(message, text=message.text)


example_bot.run_polling(timeout=10)
