"""
run: python -m example.keyboard
"""
from telegrambotclient import bot_client
from telegrambotclient.base import (KeyboardButton, MessageField,
                                    ReplyKeyboardRemove)
from telegrambotclient.ui import ReplyKeyboard

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


@router.message_handler(fields=MessageField.TEXT)
def on_show_keyboard(bot, message):
    keyboard = ReplyKeyboard()
    btn_text = KeyboardButton(text="click")
    btn_contact = KeyboardButton(text="contact", request_contact=True)
    btn_location = KeyboardButton(text="location", request_location=True)
    keyboard.add_buttons(btn_text, btn_contact, col=2)
    keyboard.append((btn_location, ))  # add a line
    # compose keyboards
    keyboard += ReplyKeyboard(layout=((btn_text, btn_contact),
                                      (btn_location, )))

    bot.send_message(
        chat_id=message.chat.id,
        text=message.text,
        reply_markup=keyboard.markup(selective=True),
    )
    bot.join_force_reply(user_id=message.from_user.id,
                         callback=on_reply_button_click)
    return bot.stop_call


@router.force_reply_handler()
def on_reply_button_click(bot, message):
    bot.force_reply_done(message.from_user.id)
    if message.text:
        bot.send_message(
            chat_id=message.chat.id,
            text="you click: {0}".format(message.text),
            reply_markup=ReplyKeyboardRemove(),
        )
        return bot.stop_call
    if message.location:
        bot.send_message(
            chat_id=message.chat.id,
            text="a location is received",
            reply_markup=ReplyKeyboardRemove(),
        )
        return bot.stop_call
    if message.contact:
        bot.send_message(
            chat_id=message.chat.id,
            text="a contact is received",
            reply_markup=ReplyKeyboardRemove(),
        )
        return bot.stop_call


bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(timeout=10)
