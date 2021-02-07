"""
run in terminal: python -m example.async_handler.py
"""
import asyncio

from simplebot import bot_proxy, SimpleBot
from simplebot.base import MessageField, Message, ParseMode
from example.settings import BOT_TOKEN

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


@router.message_handler(message_type=MessageType.TEXT)
async def on_echo_text(bot: SimpleBot, message: Message):
    bot.reply_message(message, text="I will reply in 3s.")
    await asyncio.sleep(3)
    bot.reply_message(
        message,
        text="I receive: <strong>{0}</strong>".format(message.text),
        parse_mode=ParseMode.HTML,
    )


example_bot.run_polling(timeout=10)
