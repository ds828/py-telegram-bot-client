"""
run in terminal: python -m example.live_location.py
"""
import datetime
import sqlite3

from simplebot import bot_proxy, SimpleBot
from simplebot.base import MessageType, Message, ParseMode

from example.settings import BOT_TOKEN

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)

conn = sqlite3.connect(
    "file:memory?cache=shared&mode=memory",
    detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
)
conn.execute(
    """
    CREATE TABLE IF NOT EXISTS "t_live_location" (
                    `id`    INTEGER NOT NULL PRIMARY KEY UNIQUE,
                    `lng`   REAL    NOT NULL,
                    `lat`   REAL    NOT NULL,
                    `time`  INTEGER NOT NULL
                );
"""
)
conn.commit()


@router.edited_message_handler(message_type=MessageType.LOCATION)
def on_live_location(bot: SimpleBot, edited_message: Message):
    print(edited_message.location, edited_message.edit_date)
    with conn:
        conn.execute(
            """
            INSERT INTO t_live_location (
                lng,
                lat,
                time
            ) VALUES (?, ?, ?)
        """,
            (
                edited_message.location.longitude,
                edited_message.location.latitude,
                edited_message.edit_date,
            ),
        )


example_bot.run_polling(timeout=10)
