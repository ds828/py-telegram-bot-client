"""
first, add your bot into a channel
run in terminal: python -m example.channel_post
then send some text from the channel
"""
from telegrambotclient import bot_client
from telegrambotclient.base import MessageField, ParseMode

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


@router.channel_post_handler(MessageField.TEXT)
def on_channel_post(bot, message):
    bot.reply_message(
        message,
        text="I receive a channel post: <strong>{0}</strong>".format(
            message.text),
        parse_mode=ParseMode.HTML,
    )
    return bot.stop_call


@router.edited_channel_post_handler(MessageField.TEXT)
def on_edited_channel_post(bot, message):
    bot.reply_message(
        message,
        text="I receive a edited channel post: <strong>{0}</strong>".format(
            message.text),
        parse_mode=ParseMode.HTML,
    )
    return bot.stop_call


async def on_update(bot, update):
    await router.dispatch(bot, update)


bot = bot_client.create_bot(token=BOT_TOKEN)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(on_update, timeout=10)
