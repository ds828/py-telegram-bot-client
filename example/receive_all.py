"""
run: python -m example.receive_all
"""
from telegrambotclient import bot_client
from telegrambotclient.handler import HandlerMapping
from telegrambotclient.utils import pretty_print

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


def on_all_updates(bot, data):
    bot.send_message(
        chat_id=data.from_user.id if data.from_user else data.chat.id,
        text="I received a update")
    return bot.stop_call


for handler in HandlerMapping.values():
    router.register_handler(handler(on_all_updates))

pretty_print(router)
bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(timeout=10)
