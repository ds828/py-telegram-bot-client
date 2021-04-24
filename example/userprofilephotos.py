"""
run in terminal: python -m example.userprofilephotos
"""
from telegrambotclient import TelegramBot, bot_client
from telegrambotclient.base import Message

from example.settings import BOT_TOKEN

router = bot_client.router()
example_bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


@router.message_handler()
def on_example(bot: TelegramBot, message: Message):
    user_profile_photos = bot.get_user_profile_photos(
        user_id=message.from_user.id)
    if user_profile_photos.total_count > 0:
        for photos in user_profile_photos.photos:
            for photo in photos:
                bot.send_photo(
                    chat_id=message.chat.id,
                    photo=photo.file_id,
                    caption="{0}x{1}".format(photo.height, photo.width),
                )


example_bot.run_polling(timeout=10)
