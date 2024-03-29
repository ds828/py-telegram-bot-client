"""
run: python -m example.command
"""
import logging

from telegrambotclient import bot_client
from telegrambotclient.base import BotCommand, BotCommandScopeChat, ParseMode

BOT_TOKEN = "<BOT_TOKEN>"

logger = logging.getLogger("telegram-bot-client")
logger.setLevel(logging.DEBUG)

router = bot_client.router()


@router.command_handler("/start")
def on_start(bot, message, *args):
    logger.debug(args)
    bot.reply_message(message, text=message.text)
    scope = BotCommandScopeChat(chat_id=message.chat.id)
    logger.debug(bot.get_my_commands(scope=scope))
    logger.debug(bot.delete_my_commands(scope=scope))
    logger.debug(bot.get_my_commands(scope=scope))
    cmd1 = BotCommand(command="/cmd1", description="cmd1")
    cmd2 = BotCommand(command="/cmd2", description="cmd2")
    logger.debug(bot.set_my_commands(commands=(cmd1, cmd2), scope=scope))
    return bot.stop_call


@router.command_handler("/cmd1", "/cmd2")  # support mulit-commands
def on_cmd1(bot, message, *args):
    text = "[{0}]({1}) {2}".format(
        message.text, bot.get_deep_link(payload="good", startgroup=False),
        "let's start")
    bot.reply_message(message, text=text, parse_mode=ParseMode.MARKDOWN)
    return bot.stop_call


async def on_update(bot, update):
    await router.dispatch(bot, update)


logger.debug(router)
bot = bot_client.create_bot(token=BOT_TOKEN)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(on_update, timeout=10)
