"""
run in terminal: python -m example.photo.py
"""
import os

from simplebot import bot_proxy, SimpleBot
from simplebot.base import MessageType, ParseMode, Message, InputFile
from example.settings import BOT_TOKEN

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


@router.message_handler(message_type=MessageType.PHOTO)
def on_photo_received(bot: SimpleBot, message: Message):
    # get the largest photo
    file_id = message.photo[-1].file_id
    # get the File object
    file_obj = bot.get_file(file_id=file_id)
    # where to save
    save_path = "sample"
    save_to_file = os.path.join(save_path, str(bot.id), file_obj.file_path)
    # download it
    bot.download_file(src_file_path=file_obj.file_path, save_to_file=save_to_file)
    # reply
    photo = InputFile("sample.jpg", save_to_file)
    bot.send_photo(
        chat_id=message.chat.id,
        photo=photo,
        caption="<b>{0}</b>".format(message.caption) if message.caption else None,
        parse_mode=ParseMode.HTML,
        disable_notification=True,
        reply_to_message_id=message.message_id,
    )


example_bot.run_polling(timeout=10)
