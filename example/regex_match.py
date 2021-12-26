"""
run in terminal: python -m example.regex_match
"""
import re
from telegrambotclient import bot_client
from telegrambotclient.base import MessageField
from telegrambotclient.utils import regex_match

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()

pattern_waze_url = re.compile(r"^.*(?P<url>https://waze.com/.+)$")
pattern_google_map_url = re.compile(r"^.*(?P<url>https://maps.app.goo.gl/.+)$")


@router.message_handler(MessageField.TEXT)
@regex_match(pattern_waze_url, pattern_google_map_url)
def on_message(bot, message, result):
    url = result.groupdict().get("url")
    bot.reply_message(message, text="I receive a url: {0}".format(url))
    return bot.stop_call


async def on_update(bot, update):
    await router.dispatch(bot, update)


bot = bot_client.create_bot(token=BOT_TOKEN)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(on_update, timeout=10)
