"""
run: python -m example.photo
"""
import os

from telegrambotclient import bot_client
from telegrambotclient.base import MessageField, ParseMode
from telegrambotclient.utils import get_file_bytes

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


def download_file(src_url: str, save_to_file: str):
    file_path = os.path.dirname(save_to_file)
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    file_bytes = get_file_bytes(src_url)
    with open(save_to_file, "wb") as new_file:
        new_file.write(file_bytes)


@router.message_handler(fields=MessageField.PHOTO)
def on_photo_received(bot, message):
    # get the largest photo
    file_id = message.photo[-1].file_id
    # get the File object
    file_obj = bot.get_file(file_id=file_id)
    # where to save
    save_to_file = os.path.abspath(
        os.path.join("./sample", str(bot.id), file_obj.file_path))
    # download it
    download_file(bot.get_file_url(file_path=file_obj.file_path), save_to_file)
    # reply it
    bot.send_photo(
        chat_id=message.chat.id,
        photo=file_id,
        caption="<b>{0}</b>".format(message.caption)
        if message.caption else None,
        parse_mode=ParseMode.HTML,
        disable_notification=True,
        reply_to_message_id=message.message_id,
    )


bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(timeout=10)
