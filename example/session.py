"""
run in cli: python -m example.session
"""
from telegrambotclient import TelegramBot, bot_client
from telegrambotclient.base import Message
from telegrambotclient.storage import SQLiteStorage

from example.settings import BOT_TOKEN

# import redis
# from telegrambotclient.storage import RedisStorage
# redis_client = redis.StrictRedis(
#    host="127.0.0.1",
#    port=6379,
#    password="",
#    db=1,
#    max_connections=10,
#    decode_responses=True,
# )
# storage = RedisStorage(redis_client)
# storage = SQLiteStorage()
storage = None
router = bot_client.router()
example_bot = bot_client.create_bot(token=BOT_TOKEN,
                                    router=router,
                                    storage=storage)
example_bot.delete_webhook(drop_pending_updates=True)


@router.message_handler()
def on_session_example(bot: TelegramBot, message: Message):
    session = bot.get_session(message.from_user.id)
    session.set("key1", 123, 60)  # field, value, optional expires(seconds)
    bot.send_message(
        chat_id=message.from_user.id,
        text="session_id: {0} data: {1}".format(session.id, session),
    )

    session["key2"] = {"foo": "abc"}
    key2_data = session["key2"]
    key2_data["foo2"] = 345
    # if value is nested, must assign it again
    session["key2"] = key2_data
    bot.send_message(
        chat_id=message.from_user.id,
        text="session_id: {0} data: {1}".format(session.id, session),
    )
    session.delete("key1")
    del session["key2"]
    if "key3" in session:
        key3_data = session.get("key3", 789)
        bot.send_message(
            chat_id=message.from_user.id,
            text="key3: {1}".format(key3_data),
        )
    session.clear()
    bot.send_message(
        chat_id=message.from_user.id,
        text="session_id: {0} data: {1}".format(session.id, session),
    )


example_bot.run_polling(timeout=10)
