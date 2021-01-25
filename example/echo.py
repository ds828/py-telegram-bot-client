"""
run in terminal: python -m example.echo.py
"""
import logging
from example.settings import BOT_TOKEN
from simplebot import bot_proxy, SimpleBot
from simplebot.base import Message, MessageField, ParseMode


logger = logging.getLogger("simple-bot")
logger.setLevel(logging.DEBUG)

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


@router.message_handler(
    fields={
        MessageField.TEXT,
    }
)
def on_echo_text(bot: SimpleBot, message: Message):
    sent_message = bot.reply_message(
        message,
        text="I receive: <strong>{0}</strong>".format(message.text),
        parse_mode=ParseMode.HTML,
    )
    bot.pin_chat_message(chat_id=message.chat.id, message_id=sent_message.message_id)


print(router.route_map)
example_bot.run_polling(timeout=10)
