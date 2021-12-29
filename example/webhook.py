"""
depends on fastapi and uvicorn
run: uvicorn example.webhook:app
"""
from fastapi import FastAPI, Request, status
from telegrambotclient import bot_client
from telegrambotclient.base import MessageField, TelegramObject
from telegrambotclient.utils import pretty_print

BOT_TOKEN_0 = "<BOT_TOKEN_0>"
BOT_TOKEN_1 = "<BOT_TOKEN_1>"

# ngrok provides a real-time HTTP traffic tunnel.
# get a tunnel on port 8000 in Austrlia
# run in terminal: ngrok http 8000 --region=au
# replace below with the your https url
WEBHOOK_URL = "https://5f9d0f13b9fb.au.ngrok.io/{0}"

router0 = bot_client.router(BOT_TOKEN_0)
router1 = bot_client.router(BOT_TOKEN_1)


def on_message(bot, message):
    pretty_print(message)
    bot.send_message(chat_id=message.chat.id,
                     text="bot {0} receives a message: {1}".format(
                         bot.user.id, message.text))


router0.register_message_handler(on_message, MessageField.TEXT)
router1.register_message_handler(on_message)  # not only text message

app = FastAPI()


@app.post("/{bot_token}", status_code=status.HTTP_200_OK)
async def serve_update(bot_token: str, request: Request):
    bot = bot_client.bots.get(bot_token, None)
    if bot:
        router = bot_client.routers.get(bot_token, None)
        if router:
            await router.dispatch(bot, TelegramObject(**await request.json()))
    return "OK"


bot_client.create_bot(token=BOT_TOKEN_0).set_webhook(
    url=WEBHOOK_URL.format(BOT_TOKEN_0))
bot_client.create_bot(token=BOT_TOKEN_1).set_webhook(
    url=WEBHOOK_URL.format(BOT_TOKEN_1))
