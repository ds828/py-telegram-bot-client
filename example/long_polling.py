"""
run in terminal: python -m example.long_polling.py
"""
from simplebot import SimpleBot, bot_proxy
from simplebot.base import Message, MessageField, ParseMode

from example.settings import BOT_TOKEN

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


@router.message_handler(fields=MessageField.TEXT)
def on_echo_text(bot: SimpleBot, message: Message):
    bot.reply_message(
        message,
        text="I receive: <strong>{0}</strong>".format(message.text),
        parse_mode=ParseMode.HTML,
    )


example_bot.run_polling(timeout=10)
