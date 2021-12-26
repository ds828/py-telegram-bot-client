"""
run: python -m example.i18n
"""
from telegrambotclient import bot_client
from telegrambotclient.base import MessageField
from telegrambotclient.utils import i18n

BOT_TOKEN = "<BOT_TOKEN>"

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

# or using gettext
# import gettext
# trans_data = {}
# locale_dir = "./locales"
# for lang in ("en", "zh-hant"):
#     translate = gettext.translation("example", locale_dir, languages=[lang])
#     translate.install()
#     trans_data[lang] = translate

router = bot_client.router()


@router.message_handler(MessageField.TEXT)
@i18n()
def on_i18n_reply(bot, message, _):
    bot.reply_message(message, text=_(message.text))


async def on_update(bot, update):
    await router.dispatch(bot, update)


bot = bot_client.create_bot(token=BOT_TOKEN, i18n_source=trans_data)

bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(on_update, timeout=10)
