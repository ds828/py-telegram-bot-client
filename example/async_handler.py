"""
run in terminal: python -m example.async_handler
"""
import asyncio

from telegrambotclient import TelegramBot, bot_client
from telegrambotclient.base import Message, MessageField, ParseMode

from example.settings import BOT_TOKEN

router = bot_client.router()
example_bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


@router.message_handler(fields=MessageField.TEXT)
async def on_echo_text(bot: TelegramBot, message: Message):
    bot.reply_message(message, text="I will reply in 3s.")
    await asyncio.sleep(3)
    bot.reply_message(
        message,
        text="I receive: <strong>{0}</strong>".format(message.text),
        parse_mode=ParseMode.HTML,
    )


example_bot.run_polling(timeout=10)
