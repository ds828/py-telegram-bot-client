"""
depends on fastapi and uvicorn
run: uvicorn example.webhook:app
"""
from fastapi import FastAPI, Request, status
from telegrambotclient import bot_client
from telegrambotclient.base import MessageField, ParseMode

BOT_TOKEN = "<BOT_TOKEN>"

# ngrok provides a real-time HTTP traffic tunnel.
# get a tunnel on port 8000 in Austrlia
# run in terminal: ngrok http 8000 --region=au
# replace below with the your https url
WEBHOOK_URL = "https://5f9d0f13b9fb.au.ngrok.io/{0}"

router = bot_client.router()
bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
bot.set_webhook(url=WEBHOOK_URL.format(BOT_TOKEN))


@router.message_handler(fields=MessageField.TEXT)
def on_echo_text(bot, message):
    bot.reply_message(
        message,
        text="I receive: <strong>{0}</strong>".format(message.text),
        parse_mode=ParseMode.HTML,
    )


app = FastAPI()


@app.post("/{bot_token}", status_code=status.HTTP_200_OK)
async def process_telegram_update(bot_token: str, request: Request):
    await bot_client.dispatch(bot_token, await request.json())
    return "OK"
