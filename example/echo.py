"""
run in terminal: python -m example.echo
"""
import logging

from telegrambotclient import bot_client
from telegrambotclient.base import MessageField, ParseMode

BOT_TOKEN = "<BOT_TOKEN>"
logger = logging.getLogger("telegram-bot-client")
logger.setLevel(logging.DEBUG)

router = bot_client.router()


@router.message_handler(fields=MessageField.TEXT)
def on_echo_text(bot, message):
    sent_message = bot.reply_message(
        message,
        text="I receive: <strong>{0}</strong>".format(message.text),
        parse_mode=ParseMode.HTML,
    )
    bot.pin_chat_message(chat_id=message.chat.id,
                         message_id=sent_message.message_id)


@router.message_handler(fields=MessageField.PINNED_MESSAGE)
def on_pinned_message(bot, message):
    bot.send_message(
        chat_id=message.chat.id,
        text="{0} pinned a message".format(message.chat.first_name),
    )


print(router)
my_bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
my_bot.delete_webhook(drop_pending_updates=True)
my_bot.run_polling(timeout=10)
