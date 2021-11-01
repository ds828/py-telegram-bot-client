"""
run: python -m example.message_entity
"""
from telegrambotclient import bot_client
from telegrambotclient.base import (
    BoldEntity, BotCommandEntity, CashTagEntity, CodeEntity, EmailEntity,
    HashTagEntity, ItalicEntity, MentionEntity, PhoneNumberEntity, PreEntity,
    StrikeThroughEntity, TextLinkEntity, TextMentionEntity, UnderLineEntity,
    URLEntity)
from telegrambotclient.utils import compose_message_entities, pretty_print

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


@router.message_handler()
def on_message(bot, message):
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
        ("print('hello {}'.format('telegram bot'))",
         PreEntity(language="python")),
        ("text_link", TextLinkEntity(url="https://telegram.org")),
        ("about this bot", TextMentionEntity(user=bot.user)),
        (("this is a", ("inner bold text", BoldEntity()),
          "and something behind"), ItalicEntity()),
    )
    text, entities = compose_message_entities(text_entities1, sep="\n")
    print(text)
    pretty_print(entities)
    bot.send_message(chat_id=message.chat.id, text=text, entities=entities)


bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(timeout=10)
