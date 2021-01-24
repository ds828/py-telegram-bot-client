"""
run in terminal: python -m example.command.py
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
cmd1 = BotCommand(command="/mycmd1", description="cmd1")
cmd2 = BotCommand(command="/mycmd2", description="cmd2 value1 value2")
example_bot.set_my_commands(commands=(cmd1, cmd2))


@router.command_handler(("/mycmd1",))
def on_mycmd1(bot: SimpleBot, message: Message):
    bot.reply_message(message, text=message.text)


@router.command_handler(("/mycmd2",))
def on_mycmd2(bot: SimpleBot, message: Message, *cmd_args):
    print(cmd_args)
    bot.reply_message(message, text=message.text)


example_bot.run_polling(timeout=10)
