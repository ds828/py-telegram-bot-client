"""
run: python -m example.userprofilephotos
"""
from telegrambotclient import bot_client

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


@router.message_handler()
def on_example(bot, message):
    user_profile_photos = bot.get_user_profile_photos(user_id=message.chat.id)
    if user_profile_photos.total_count > 0:
        for photos in user_profile_photos.photos:
            for photo in photos:
                bot.send_photo(
                    chat_id=message.chat.id,
                    photo=photo.file_id,
                    caption="{0}x{1}".format(photo.height, photo.width),
                )


bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(timeout=10)
