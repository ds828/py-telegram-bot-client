"""
run: python -m example.error
"""
from telegrambotclient import bot_client
from telegrambotclient.base import TelegramBotException

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


@router.message_handler()
def on_echo_text(bot, message):
    bot.send_message(chat_id=message.chat.id, text="I will raise a exception")
    # raise TelegramBotException("telegrambot exception")
    # only catch by on_exception
    raise Exception("something wrong")


@router.error_handler(TelegramBotException)
def on_telegrambot_exception(bot, data, error):
    bot.send_message(chat_id=data.from_user.id,
                     text="on_telegrambot_exception: " + str(error))


@router.error_handler(ValueError, IndexError)
def on_many_exceptions(bot, data, error):
    bot.send_message(chat_id=data.from_user.id,
                     text="on_many_exceptions: " + str(error))


# for all excetions
@router.error_handler()
def on_exception(bot, data, error):
    bot.send_message(chat_id=data.chat.id, text="on_exception: " + str(error))


async def on_update(bot, update):
    await router.dispatch(bot, update)


bot = bot_client.create_bot(token=BOT_TOKEN)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(on_update, timeout=10)
