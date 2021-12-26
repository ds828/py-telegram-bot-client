"""
NOT fully tested
run: python -m example.local_server
"""
from telegrambotclient import bot_client
from telegrambotclient.api import TelegramBotAPI
from telegrambotclient.base import MessageField, ParseMode

BOT_TOKEN = "BOT_TOKEN"

router = bot_client.router()


@router.message_handler(MessageField.TEXT)
def on_echo_text(bot, message):
    bot.reply_message(
        message,
        text="I receive: <strong>{0}</strong>".format(message.text),
        parse_mode=ParseMode.HTML,
    )


async def on_update(bot, update):
    await router.dispatch(bot, update)


# the bot with the offical api
bot = bot_client.create_bot(token=BOT_TOKEN)
bot.delete_webhook(drop_pending_updates=True)
if bot.log_out():
    bot = bot_client.create_bot(
        token=BOT_TOKEN,
        bot_api=TelegramBotAPI(
            api_host="http://your_local_api_host"))  # self-define api provider
    bot.run_polling(on_update, timeout=10)
