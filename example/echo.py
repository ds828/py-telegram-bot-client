"""
run in terminal: python -m example.echo.py
"""
import logging

from simplebot import SimpleBot, bot_proxy
from simplebot.base import Message, MessageField, ParseMode

from example.settings import BOT_TOKEN

logger = logging.getLogger("simple-bot")
logger.setLevel(logging.DEBUG)

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


@router.message_handler(fields=MessageField.TEXT)
def on_echo_text(bot: SimpleBot, message: Message):
    sent_message = bot.reply_message(
        message,
        text="I receive: <strong>{0}</strong>".format(message.text),
        parse_mode=ParseMode.HTML,
    )
    bot.pin_chat_message(chat_id=message.chat.id,
                         message_id=sent_message.message_id)


@router.message_handler(fields=MessageField.PINNED_MESSAGE)
def on_pinned_message(bot: SimpleBot, message: Message):
    bot.send_message(
        chat_id=message.chat.id,
        text="{0} pinned a message".format(message.chat.first_name),
    )


# any fields of a message
# it will be called if others callbacks before it return bool(something) is True
@router.message_handler()
def on_unacceptable(bot: SimpleBot, message: Message):
    bot.send_message(chat_id=message.chat.id, text="Opoos...")


print(router)
example_bot.run_polling(timeout=10)
