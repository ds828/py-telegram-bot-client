"""
run: python -m example.session
"""
from telegrambotclient import bot_client
from telegrambotclient.storage import SQLiteStorage

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


@router.message_handler()
def on_session_example(bot, message):
    session = bot.get_session(message.from_user.id,
                              expires=60)  # renew a new expires
    session.set("key1", 123)  # field, value
    bot.send_message(
        chat_id=message.from_user.id,
        text=str(session),
    )

    session["key2"] = {"foo": "abc"}
    key2_data = session["key2"]
    key2_data["foo2"] = 345
    session["key2"] = key2_data
    session.save()  # save persistently
    bot.send_message(
        chat_id=message.from_user.id,
        text=str(session),
    )
    print(session.data)
    # access session with context manager
    with bot.session(message.chat.id) as session:
        # delete mulit keys
        session.delete("key1", "key2")
        # delete one key
        del session["key3"]
        if "key3" not in session:
            session.set("key3", 789)
            bot.send_message(
                chat_id=message.from_user.id,
                text=str(session),
            )
        session.clear()
        bot.send_message(
            chat_id=message.from_user.id,
            text=str(session),
        )
        print(session.data)


# using redis
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
# storage = None # uncomment for memory session
storage = SQLiteStorage("/tmp/session.db")
bot = bot_client.create_bot(token=BOT_TOKEN, router=router, storage=storage)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(timeout=10)
