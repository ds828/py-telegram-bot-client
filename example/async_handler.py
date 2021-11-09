"""
run: python -m example.async_handler
"""
import asyncio

from telegrambotclient import bot_client
from telegrambotclient.base import MessageField, ParseMode

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


@router.message_handler(fields=MessageField.TEXT)
async def on_echo_text(bot, message):
    bot.reply_message(message, text="I will reply in 3s.")
    await asyncio.sleep(3)
    bot.reply_message(
        message,
        text="I receive: *{0}*".format(message.text),
        parse_mode=ParseMode.MARKDOWN,
    )


bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(timeout=10)
