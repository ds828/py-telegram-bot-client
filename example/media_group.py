"""
run: python -m example.media_group
"""
import os.path

from telegrambotclient import bot_client
from telegrambotclient.base import (InputFile, InputMediaAudio,
                                    InputMediaDocument, InputMediaPhoto,
                                    InputMediaVideo)

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


@router.message_handler()
def on_send_media_group(bot, message):
    thumb = InputFile("sample.jpg", os.path.abspath("./sample/sample.jpg"))
    video = InputMediaVideo(
        media=InputFile("sample.mp4", os.path.abspath("./sample/sample.mp4")),
        thumb=thumb,
    )
    photo = InputMediaPhoto(
        media=InputFile("sample.png", os.path.abspath("./sample/sample.png")))
    document = InputMediaDocument(
        media=InputFile("sample.txt", os.path.abspath("./sample/sample.txt")),
        thumb=thumb,
    )
    audio = InputMediaAudio(
        media=InputFile("sample.mp3", os.path.abspath("./sample/sample.mp3")),
        thumb=thumb,
    )
    bot.send_media_group(chat_id=message.chat.id, media=(video, photo))
    bot.send_media_group(chat_id=message.chat.id, media=(document, document))
    bot.send_media_group(chat_id=message.chat.id, media=(audio, audio))
    # Documents and audio files can be only grouped in an album with messages of the same type.
    # uncomment below, it will raise Bad Request: document can't be mixed with other media types
    # bot.send_media_group(chat_id=message.chat.id, media=(audio, document))
    return bot.stop_call


async def on_update(bot, update):
    await router.dispatch(bot, update)


bot = bot_client.create_bot(token=BOT_TOKEN)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(on_update, timeout=10)
