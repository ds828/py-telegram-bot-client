"""
run in terminal: python -m example.message_entity.py
"""
from simplebot import bot_proxy, SimpleBot
from simplebot.base import (
    BotCommandEntity,
    CodeEntity,
    EmailEntity,
    ItalicEntity,
    MentionEntity,
    MentionEntity,
    HashTagEntity,
    CashTagEntity,
    BoldEntity,
    EmailEntity,
    BotCommandEntity,
    PhoneNumberEntity,
    PreEntity,
    StrikeThroughEntity,
    TextLinkEntity,
    TextMentionEntity,
    URLEntity,
    UnderLineEntity,
    Message,
)
from simplebot.utils import compose_message_entities

from example.settings import BOT_TOKEN

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)

text_entities1 = (
    "plain text",
    ("strong text", BoldEntity()),
    ("do-not-reply@telegram.org", EmailEntity()),
    ("@username", MentionEntity()),
    ("#hashtag", HashTagEntity()),
    ("$USD", CashTagEntity()),
    ("/start@jobs_bot", BotCommandEntity()),
    ("https://telegram.org", URLEntity()),
    ("+1-212-555-0123", PhoneNumberEntity()),
    ("italic", ItalicEntity()),
    ("underline", UnderLineEntity()),
    ("strikethrough", StrikeThroughEntity()),
    ("code", CodeEntity()),
    ("print('hello {}'.format('telegram bot'))", PreEntity(language="python")),
    ("text_link", TextLinkEntity(url="https://telegram.org")),
    ("about this bot", TextMentionEntity(user=example_bot.me)),
    (("this is a", ("inner bold text", BoldEntity()), "and something behind"), ItalicEntity()),
)


@router.message_handler()
def on_reply(bot: SimpleBot, message: Message):
    text, entities = compose_message_entities(text_entities1, sep="\n")
    bot.send_message(chat_id=message.chat.id, text=text, entities=entities)


example_bot.run_polling(timeout=10)
