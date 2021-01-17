"""
run in cli: python -m example.keyboard.py
"""
import logging
from simplebot import bot_proxy, SimpleBot
from simplebot.base import (
    Message,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    MessageType,
)
from simplebot.ui import KeyboardLayout
from example.settings import BOT_TOKEN

logger = logging.getLogger("simple-bot")
logger.setLevel(logging.DEBUG)

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


@router.message_handler(message_type=MessageType.TEXT)
def on_build_keyboard(bot: SimpleBot, message: Message):
    btn_text = KeyboardButton("click me")
    btn_contact = KeyboardButton("share your contact", request_contact=True)
    btn_location = KeyboardButton("share your location", request_location=True)
    layout = KeyboardLayout()
    layout.add_buttons(btn_text, btn_contact, btn_location)
    layout.add_line(btn_text, btn_contact, btn_location)
    bot.send_message(
        chat_id=message.chat.id,
        text=message.text,
        reply_markup=ReplyKeyboardMarkup(keyboard=layout.keyboard(), selective=True),
    )
    bot.join_force_reply(user_id=message.from_user.id, callback=on_btn_click)


@router.force_reply_handler()
def on_btn_click(bot: SimpleBot, message: Message):
    bot.force_reply_done(message.from_user.id)
    if message.text:
        bot.send_message(
            chat_id=message.chat.id,
            text="you click: {0}".format(message.text),
            reply_markup=ReplyKeyboardRemove(),
        )
        return
    if message.location:
        bot.send_message(
            chat_id=message.chat.id,
            text="a location is received",
            reply_markup=ReplyKeyboardRemove(),
        )
        return
    if message.contact:
        bot.send_message(
            chat_id=message.chat.id,
            text="a contact is received",
            reply_markup=ReplyKeyboardRemove(),
        )
        return


example_bot.run_polling(timeout=10)
