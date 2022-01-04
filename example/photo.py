"""
run: python -m example.photo
"""
import os

from telegrambotclient import bot_client
from telegrambotclient.base import ChatAction, InputFile, InputMediaPhoto, MessageField, ParseMode

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


@router.message_handler(MessageField.PHOTO)
def on_photo_message(bot, message):
    bot.send_chat_action(chat_id=message.chat.id,
                         action=ChatAction.UPLOAD_PHOTO)
    # get the largest photo
    file_id = message.photo[-1].file_id
    # get the File object
    file_obj = bot.get_file(file_id=file_id)
    # where to save
    save_to_file = os.path.abspath(os.path.join("/tmp", file_obj.file_path))
    file_path = os.path.dirname(save_to_file)
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    # download it
    file_bytes = bot.get_file_bytes(file_obj)
    # write
    with open(save_to_file, "wb") as new_file:
        new_file.write(file_bytes)
    # reply it
    sent_message = bot.send_photo(chat_id=message.chat.id,
                                  photo=file_id,
                                  caption="<b>{0}</b>".format(message.caption)
                                  if message.caption else None,
                                  parse_mode=ParseMode.HTML,
                                  disable_notification=True,
                                  reply_to_message_id=message.message_id)

    # and edit the photo
    bot.edit_message_media(
        chat_id=message.chat.id,
        message_id=sent_message.message_id,
        media=InputMediaPhoto(media=InputFile(
            "sample.png", os.path.abspath("./sample/sample.png"))))
    return bot.stop_call


async def on_update(bot, update):
    await router.dispatch(bot, update)


bot = bot_client.create_bot(token=BOT_TOKEN)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(on_update, timeout=10)
