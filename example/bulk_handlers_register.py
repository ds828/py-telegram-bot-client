"""
run in terminal: python -m example.bluk_handlers_register.py
"""
from simplebot import SimpleBot, bot_proxy
from simplebot.base import BotCommand, Message, MessageField
from simplebot.handler import CommandHandler, MessageHandler

from example.settings import BOT_TOKEN


def on_mycmd(bot: SimpleBot, message: Message):
    bot.reply_message(message, text=message.text)


def on_message(bot: SimpleBot, message: Message):
    bot.reply_message(message, text=message.text)


handlers = (
    CommandHandler(callback=on_mycmd, cmds=("/mycmd1", "/mycmd2")),
    MessageHandler(callback=on_message, fields=(MessageField.TEXT, )),
)
# define a named router
# router = bot_proxy.router(name="my_router", handlers=handlers)
# example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)

# quick to work, define a router is not necessary
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, handlers=handlers)
example_bot.delete_webhook(drop_pending_updates=True)
cmd1 = BotCommand(command="/mycmd1", description="cmd1")
cmd2 = BotCommand(command="/mycmd2", description="cmd2")
example_bot.set_my_commands(commands=(cmd1, cmd2))
example_bot.run_polling(timeout=10)
