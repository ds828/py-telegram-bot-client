"""
run: python example.document
"""
import os.path

from telegrambotclient import bot_client
from telegrambotclient.base import InputFile, MessageField

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


@router.message_handler()
def on_send_document(bot, message):
    # read more: https://core.telegram.org/bots/api#inputfile
    # InputFile can accept a file path string
    thumb_img = InputFile("thumb.png", os.path.abspath("./sample/sample.png"))
    document = None
    # # send as a URL
    # document = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    file = os.path.abspath("./sample/sample.txt")
    # # send as a InputFile
    document = InputFile("sample.txt", file)
    # # send as bytes
    # with open(file, "rb") as file_obj:
    #     # InputFile can accept a bytes stream as well
    #     document = InputFile("sample.txt", file_obj.read())
    bot.send_document(chat_id=message.chat.id,
                      document=document,
                      thumb=thumb_img)
    return bot.stop_call


@router.message_handler(fields=MessageField.DOCUMENT)
def on_receive_document(bot, message):
    file_obj = bot.get_file(file_id=message.document.file_id)
    file_url = bot.get_file_url(file_path=file_obj.file_path)
    file_data = bot.get_file_bytes(file_obj.file_path)
    print(file_data)
    bot.reply_message(message, text="download url: {0}".format(file_url))
    return bot.stop_call


async def on_update(bot, update):
    await router.dispatch(bot, update)


bot = bot_client.create_bot(token=BOT_TOKEN)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(on_update, timeout=10)
