"""
depends on fastapi and uvicorn
run in terminal: uvicorn example.webhook:app
"""
from fastapi import FastAPI, Request, status
from telegrambotclient import TelegramBot, bot_client
from telegrambotclient.base import Message, MessageField, ParseMode

from example.settings import BOT_TOKEN

# ngrok provides a real-time HTTP traffic tunnel.
# get a tunnel on port 8000 in Austrlia
# run in terminal: ngrok http 8000 --region=au
# replace below with the https url
WEBHOOK_URL = "https://5f9d0f13b9fb.au.ngrok.io/bot/{0}"

router = bot_client.router()
example_bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
example_bot.setup_webhook(WEBHOOK_URL.format(BOT_TOKEN))


@router.message_handler(fields=MessageField.TEXT)
def on_echo_text(bot: TelegramBot, message: Message):
    bot.reply_message(
        message,
        text="I receive: <strong>{0}</strong>".format(message.text),
        parse_mode=ParseMode.HTML,
    )


app = FastAPI()


@app.post("/bot/{bot_token}", status_code=status.HTTP_200_OK)
async def process_telegram_update(bot_token: str, request: Request):
    await bot_client.dispatch(bot_token, await request.json())
    return ""
