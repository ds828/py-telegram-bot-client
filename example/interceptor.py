"""
run in terminal: python -m example.interceptor
"""
from telegrambotclient import TelegramBot, bot_client
from telegrambotclient.base import Message, TelegramObject, UpdateType
from telegrambotclient.handler import InterceptorType
from telegrambotclient.utils import pretty_print

from example.settings import BOT_TOKEN

router = bot_client.router()
example_bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


# intercept any update types
@router.interceptor(inter_type=InterceptorType.BEFORE)
def on_before(bot: TelegramBot, data: TelegramObject):
    pretty_print(data)
    bot.send_message(chat_id=data.from_user.id, text="on_before")


# intercept when a message's incoming
@router.interceptor(update_types=(UpdateType.MESSAGE, ),
                    inter_type=InterceptorType.BEFORE)
def on_message_before(bot: TelegramBot, message: Message):
    bot.send_message(chat_id=message.from_user.id,
                     text="on_message_before: " + str(message))


@router.interceptor(inter_type=InterceptorType.AFTER)
def on_after(bot: TelegramBot, data: TelegramObject):
    bot.send_message(chat_id=data.from_user.id, text="on_after")


@router.message_handler()
def on_message(bot: TelegramBot, message: Message):
    bot.reply_message(message, text="message is received")
    # after interceptor will not be called
    # raise Exception("something wrong")


example_bot.run_polling(timeout=10)
