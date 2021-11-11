"""
run: python -m example.session
"""

from telegrambotclient import bot_client
from telegrambotclient.storage import (MongoDBStorage, RedisStorage,
                                       SQLiteStorage)
from telegrambotclient.utils import pretty_print

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


@router.message_handler()
def on_message(bot, message):
    session = bot.get_session(message.chat.id,
                              expires=60)  # set this session a new expires
    session["key1"] = 123  # field, value
    bot.send_message(
        chat_id=message.chat.id,
        text=str(session.data),
    )

    session["key2"] = {"foo": "abc"}
    key2_data = session["key2"]
    key2_data["foo2"] = 345
    session["key2"] = key2_data
    session.save()  # save and write
    bot.send_message(
        chat_id=message.chat.id,
        text=str(session.data),
    )
    pretty_print(session)
    # a dict include all data in the session
    pretty_print(session._data)
    # access a session with a context manager, automaticlly save
    with bot.session(message.chat.id) as session:
        # delete mulit keys
        session.delete("key1", "key2")
        # delete one key
        del session["key3"]
        if "key3" not in session:
            session["key3"] = 789
            bot.send_message(
                chat_id=message.chat.id,
                text=str(session.data),
            )
        session.clear()  # same with bot.clear_session(message.chat.id)
        bot.send_message(
            chat_id=message.chat.id,
            text=str(session.data),
        )
        pretty_print(session)


storage = None  # using memory session

# using sqlite
# import os
import sqlite3

# db_file = "/tmp/session.db"
# db_path = os.path.dirname(db_file)
# if not os.path.exists(db_path):
#     os.mkdir(db_path)
# db_conn = sqlite3.connect(db_file)
# using memory db file
db_conn = sqlite3.connect("file:memory?cache=shared&mode=memory", uri=True)
storage = SQLiteStorage(db_conn)

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

# using mongodb
# from pymongo import MongoClient
# storage = MongoDBStorage(
#     MongoClient("mongodb://localhost:27017")["session_db"]["session"])

bot = bot_client.create_bot(
    token=BOT_TOKEN, router=router, storage=storage,
    session_expires=30)  # set 30s as a default session timeout
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(timeout=10)
