"""
run in cli: python -m example.error.py
"""
from simplebot import bot_proxy, SimpleBot
from simplebot.base import SimpleBotException, SimpleObject, Message

from example.settings import BOT_TOKEN

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


@router.message_handler()
def on_echo_text(bot: SimpleBot, message: Message):
    bot.send_message(chat_id=message.chat.id, text="I will raise a exception")
    raise SimpleBotException("simplebot exception")
    # Only catch by on_exception
    # raise Exception("something wrong")


@router.error_handler(error_type=SimpleBotException)
def on_simplebotexception(bot: SimpleBot, data: SimpleObject, error):
    bot.send_message(chat_id=data.from_user.id, text="on_simplebotexception: " + str(error))


@router.error_handler()
def on_exception(bot: SimpleBot, data: SimpleObject, error):
    bot.send_message(chat_id=data.from_user.id, text="on_exception: " + str(error))


example_bot.run_polling(timeout=10)
