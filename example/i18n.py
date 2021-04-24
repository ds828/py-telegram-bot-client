"""
run in cli: python -m example.i18n
"""
from typing import Callable

from telegrambotclient import TelegramBot, bot_client
from telegrambotclient.base import Message
from telegrambotclient.utils import i18n

from example.settings import BOT_TOKEN

trans_data = {
    "en": {
        "start": "start to play",
        "help": "help text"
    },
    "zh-hant": {
        "start": "開始",
        "help": "幫助"
    },
}

# import gettext
# translations = {}
# locale_dir = "./locales"
# for lang in ("en", "zh-hant"):
# translate = gettext.translation("simplebot", locale_dir, languages=[lang])
# translate.install()
# translations[lang] = translate

router = bot_client.router()
example_bot = bot_client.create_bot(token=BOT_TOKEN,
                                    router=router,
                                    i18n_source=trans_data)
example_bot.delete_webhook(drop_pending_updates=True)


@router.message_handler()
@i18n()
def on_i18n_text(bot: TelegramBot, message: Message, _: Callable):
    bot.reply_message(message, text=_(message.text))


example_bot.run_polling(timeout=10)
