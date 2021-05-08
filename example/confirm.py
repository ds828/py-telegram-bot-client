"""
run in cli: python -m example.confirm
"""
import logging

from telegrambotclient import TelegramBot, bot_client
from telegrambotclient.api import TelegramBotAPIException
from telegrambotclient.base import CallbackQuery, Message, MessageField
from telegrambotclient.ui import InlineKeyboard

from example.settings import BOT_TOKEN

logger = logging.getLogger("telegram-bot-client")
logger.setLevel(logging.DEBUG)

router = bot_client.router()
example_bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


def on_cancel_callback(bot: TelegramBot, callback_query: CallbackQuery,
                       confirm: bool, option):
    bot.send_message(chat_id=callback_query.from_user.id,
                     text="click cancel 1 with {0}".format(option))


InlineKeyboard.auto_cancel(
    router,
    name="confirm-dialog-1",
    cancel_callback=on_cancel_callback,
)


@router.message_handler(fields=MessageField.TEXT)
def on_show_keyboard(bot: TelegramBot, message: Message):
    keyboard = InlineKeyboard()
    keyboard.add_confirm_buttons(name="confirm-dialog-1",
                                 callback_data=123,
                                 ok_text="Confirm 1",
                                 cancel_text="Abort 1",
                                 auto_cancel=True)
    keyboard.add_confirm_buttons(name="confirm-dialog-2", callback_data=456)
    bot.send_message(chat_id=message.chat.id,
                     text="Please confirm",
                     reply_markup=keyboard.markup())


@router.callback_query_handler(callback_data_name="confirm-dialog-1")
def on_confirm1(bot, callback_query, confirm, option):
    if confirm:
        bot.send_message(chat_id=callback_query.from_user.id,
                         text="click confirm 1 with {0}".format(option))


@router.callback_query_handler(callback_data_name="confirm-dialog-2")
def on_confirm2(bot, callback_query, confirm, option):
    if confirm:
        bot.send_message(chat_id=callback_query.from_user.id,
                         text="click confirm 2 with {0}".format(option))
    else:
        # manually process click the cancel button
        try:
            bot.delete_message(chat_id=callback_query.from_user.id,
                               message_id=callback_query.message.message_id)
        except TelegramBotAPIException:
            pass


example_bot.run_polling(timeout=10)
