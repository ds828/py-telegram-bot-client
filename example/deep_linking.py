"""
run in terminal: python -m example.deep_linking
deep linking: https://t.me/<YOUR-BOT-USERNAME>?start=test
"""
from telegrambotclient import bot_client

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


@router.message_handler()
def on_text(bot, message):
    bot.send_message(chat_id=message.chat.id,
                     text=bot.get_deep_link(payload="PAYLOAD"))


@router.command_handler(("/start", ))
def on_start(bot, message, *payload):
    print(payload)
    bot.reply_message(message, text=message.text)


async def on_update(bot, update):
    await router.dispatch(bot, update)


bot = bot_client.create_bot(token=BOT_TOKEN)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(on_update, timeout=10)
