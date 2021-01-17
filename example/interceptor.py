"""
run in terminal: python -m example.interceptor.py
"""
from simplebot.utils import pretty_print
from simplebot.handler import InterceptorType
from simplebot import bot_proxy, SimpleBot
from simplebot.base import Message, SimpleObject, UpdateType
from example.settings import BOT_TOKEN

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)

# intercept all types of update
@router.interceptor(inter_type=InterceptorType.BEFORE)
def on_before(bot: SimpleBot, data: SimpleObject):
    pretty_print(data)
    bot.send_message(chat_id=data.from_user.id, text="on_before")


# intercept when a message's incoming
@router.interceptor(update_type=UpdateType.MESSAGE, inter_type=InterceptorType.BEFORE)
def on_message_before(bot: SimpleBot, message: Message):
    bot.send_message(chat_id=message.from_user.id, text="on_message_before: " + str(message))


@router.interceptor(inter_type=InterceptorType.AFTER)
def on_after(bot: SimpleBot, data: SimpleObject):
    bot.send_message(chat_id=data.from_user.id, text="on_after")


@router.message_handler()
def on_message(bot: SimpleBot, message: Message):
    bot.reply_message(message, text="message is received")
    # after interceptor will not be called
    # raise Exception("something wrong")


example_bot.run_polling(timeout=10)
