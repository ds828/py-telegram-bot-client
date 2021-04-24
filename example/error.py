"""
run in cli: python -m example.error
"""
from telegrambotclient import TelegramBot, bot_client
from telegrambotclient.base import (Message, TelegramBotException,
                                    TelegramObject)

from example.settings import BOT_TOKEN

router = bot_client.router()
example_bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


@router.message_handler()
def on_echo_text(bot: TelegramObject, message: Message):
    bot.send_message(chat_id=message.chat.id, text="I will raise a exception")
    raise TelegramBotException("simplebot exception")
    # Only catch by on_exception
    # raise Exception("something wrong")


@router.error_handler(errors=(TelegramBotException, ))
def on_simplebotexception(bot: TelegramBot, data: TelegramObject, error):
    bot.send_message(chat_id=data.from_user.id,
                     text="on_simplebotexception: " + str(error))


@router.error_handler()
def on_exception(bot: TelegramBot, data: TelegramObject, error):
    bot.send_message(chat_id=data.from_user.id,
                     text="on_exception: " + str(error))


print(router.route_map)
example_bot.run_polling(timeout=10)
