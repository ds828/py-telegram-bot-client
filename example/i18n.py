"""
run in cli: python -m example.i18n.py
"""
from simplebot import bot_proxy, SimpleBot
from simplebot.base import Message
from simplebot.utils import i18n
from example.settings import BOT_TOKEN

trans_data = {
    "en": {"start": "start to play", "help": "help text"},
    "zh-hant": {"start": "開始", "help": "幫助"},
}

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


@router.message_handler()
@i18n(trans_data)
def on_i18n_text(bot: SimpleBot, message: Message, _: callable):
    bot.reply_message(message, _(message.text))


example_bot.run_polling(timeout=10)
