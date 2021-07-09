"""
run in terminal: python -m example.command
"""
import logging

from telegrambotclient import bot_client
from telegrambotclient.base import BotCommand, BotCommandScopeChat

from example.settings import BOT_TOKEN

logger = logging.getLogger("telegram-bot-client")
logger.setLevel(logging.DEBUG)

router = bot_client.router()
my_bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
my_bot.delete_webhook(drop_pending_updates=True)
cmd1 = BotCommand(command="/mycmd1", description="cmd1")
my_bot.set_my_commands(commands=(cmd1, ))


@router.command_handler(("/cmd1", ))
def on_mycmd1(bot, message):
    bot.reply_message(message, text=message.text)


@router.command_handler(("/cmd2", ))
def on_mycmd2(bot, message, *cmd_args):
    logger.debug(cmd_args)
    cmd2 = BotCommand(command="/mycmd2", description="cmd2 value1 value2")
    bot.set_my_commands(
        commands=(cmd2, ),
        scope=BotCommandScopeChat(chat_id=message.from_user.id))
    bot.reply_message(message, text=message.text)


my_bot.run_polling(timeout=10)
