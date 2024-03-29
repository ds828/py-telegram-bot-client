"""
run: python -m example.message_entity
"""
from telegrambotclient import bot_client
from telegrambotclient.base import (BoldEntity, BotCommandEntity,
                                    CashTagEntity, CodeEntity, EmailEntity,
                                    HashTagEntity, ItalicEntity, MentionEntity,
                                    MessageField, PhoneNumberEntity, PreEntity,
                                    SpoilerEntity, StrikeThroughEntity,
                                    TextLinkEntity, TextMentionEntity,
                                    UnderLineEntity, URLEntity, SpoilerEntity)
from telegrambotclient.utils import compose_message_entities

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


@router.message_handler(MessageField.TEXT)
def on_message(bot, message):
    text_entities = ("plain text", ("strong text", BoldEntity()),
                     ("do-not-reply@telegram.org",
                      EmailEntity()), ("@username",
                                       MentionEntity()), ("#hashtag",
                                                          HashTagEntity()),
                     ("$USD", CashTagEntity()), ("/start@jobs_bot",
                                                 BotCommandEntity()),
                     ("https://telegram.org",
                      URLEntity()), ("+1-212-555-0123", PhoneNumberEntity()),
                     ("italic", ItalicEntity()), ("underline",
                                                  UnderLineEntity()),
                     ("strikethrough", StrikeThroughEntity()), ("code",
                                                                CodeEntity()),
                     ("print('hello {}'.format('telegram bot'))",
                      PreEntity(language="python")),
                     ("text_link", TextLinkEntity(url="https://telegram.org")),
                     ("about this bot", TextMentionEntity(user=bot.user)),
                     (("this is a", ("inner bold text",
                                     BoldEntity()), "and something behind"),
                      ItalicEntity()), ("some spoiler", SpoilerEntity()))
    text, entities = compose_message_entities(text_entities, sep="\n")
    bot.send_message(chat_id=message.chat.id, text=text, entities=entities)
    return bot.stop_call


async def on_update(bot, update):
    await router.dispatch(bot, update)


bot = bot_client.create_bot(token=BOT_TOKEN)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(on_update, timeout=10)
