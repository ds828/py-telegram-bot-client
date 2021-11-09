"""
run: python -m example.command
"""
import logging

from telegrambotclient import bot_client
from telegrambotclient.base import BotCommand, ParseMode

BOT_TOKEN = "<BOT_TOKEN>"

logger = logging.getLogger("telegram-bot-client")
logger.setLevel(logging.DEBUG)

router = bot_client.router()


@router.command_handler(("/start", ))
def on_start(bot, message, *cmd_args):
    logger.debug(cmd_args)
    bot.reply_message(message, text=message.text)
    return bot.stop_call


@router.command_handler(("/cmd", ))
def on_cmd1(bot, message):
    text = "[{0}]({1}) {2}".format(
        message.text, bot.get_deep_link(payload="good", startgroup=False),
        "let's start")
    bot.reply_message(message, text=text, parse_mode=ParseMode.MARKDOWN)
    return bot.stop_call


logger.debug(router)
bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
bot.delete_webhook(drop_pending_updates=True)
cmd = BotCommand(command="/cmd", description="cmd")
bot.set_my_commands(commands=(cmd, ))
bot.run_polling(timeout=10)
