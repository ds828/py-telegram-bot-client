import asyncio
import logging
import sys
from contextlib import contextmanager
from typing import Callable, Dict

from telegrambotclient.api import TelegramBotAPI
from telegrambotclient.base import File, Message, TelegramObject
from telegrambotclient.storage import TelegramSession, TelegramStorage

logger = logging.getLogger("telegram-bot-client")
formatter = logging.Formatter(
    '%(levelname)s %(asctime)s (%(filename)s:%(lineno)d): "%(message)s"')
console_output_handler = logging.StreamHandler(sys.stderr)
console_output_handler.setFormatter(formatter)
logger.addHandler(console_output_handler)
logger.setLevel(logging.INFO)


class TelegramBot:
    SESSION_ID_FORMAT = "{0}:{1}"
    next_call = True
    stop_call = False

    __slots__ = ("token", "bot_api", "storage", "i18n_source",
                 "session_expires", "user")

    def __init__(self,
                 token: str,
                 bot_api: TelegramBotAPI = None,
                 storage: TelegramStorage = None,
                 i18n_source: Dict = None,
                 session_expires: int = 1800):

        self.token = token
        self.bot_api = bot_api or TelegramBotAPI()
        if storage is None:
            logger.warning(
                "You are using a memory session which should be for testing only."
            )
            storage = TelegramStorage()
        self.storage = storage
        self.i18n_source = i18n_source
        self.session_expires = session_expires
        self.user = self.get_me()

    def get_session(self, user_id: int, expires: int = 0):
        return TelegramSession(
            self.SESSION_ID_FORMAT.format(self.user.id, user_id), self.storage,
            expires or self.session_expires)

    def clear_session(self, user_id: int):
        session = self.get_session(user_id)
        session.clear()

    @contextmanager
    def session(self, user_id: int, expires: int = 0):
        session = self.get_session(user_id, expires or self.session_expires)
        try:
            yield session
        finally:
            session.save()

    def join_force_reply(self,
                         user_id: int,
                         reply_to_message: Message,
                         callback: Callable,
                         *force_reply_args,
                         expires: int = 0):
        force_reply_callback_name = "{0}.{1}".format(callback.__module__,
                                                     callback.__name__)
        session = self.get_session(user_id, expires or self.session_expires)
        if force_reply_args:
            session["_reply_to_message"] = {
                "message_id": reply_to_message.message_id,
                "callback": force_reply_callback_name,
                "args": force_reply_args
            }
        else:
            session["_reply_to_message"] = {
                "message_id": reply_to_message.message_id,
                "callback": force_reply_callback_name
            }
        session.save()

    def update_force_reply(self, user_id, reply_to_message, expires: int = 0):
        session = self.get_session(user_id, expires or self.session_expires)
        if "_reply_to_message" in session:
            session["_reply_to_message"].update(
                {"message_id": reply_to_message.message_id})
            session.save()

    def remove_force_reply(self, user_id, expires: int = 0):
        session = self.get_session(user_id, expires or self.session_expires)
        del session["_reply_to_message"]

    def get_force_reply(self, user_id, expires: int = 0):
        session = self.get_session(user_id, expires or self.session_expires)
        return session.get("_reply_to_message", {})

    def get_text(self, lang_code: str, text: str):
        if self.i18n_source:
            lang_source = self.i18n_source.get(lang_code, None)
            if lang_source:
                if isinstance(lang_source, dict):
                    return lang_source.get(text, text)
                return lang_source.gettext(text)
        return text

    def reply_message(self, message: Message, **kwargs):
        kwargs["reply_to_message_id"] = message.message_id
        return self.send_message(chat_id=message.chat.id, **kwargs)

    def get_file_url(self, file_path: str):
        return "{0}{1}".format(
            self.bot_api.host,
            self.bot_api.FILE_URL.format(self.token, file_path))

    def get_file_bytes(self, file_obj: File):
        return self.bot_api.api_caller.get_bytes(
            self.bot_api.FILE_URL.format(self.token, file_obj.file_path),
            chunk_size=file_obj.file_size or 1024,
        )

    def get_deep_link(self,
                      payload: str,
                      host: str = "https://t.me",
                      startgroup: bool = False):
        return "{0}/{1}?{2}={3}".format(
            host, self.user.username, "startgroup" if startgroup else "start",
            payload)

    def run_polling(self,
                    on_update_callback: Callable,
                    offset: int = 0,
                    limit: int = 100,
                    timeout: int = 10,
                    allowed_updates=None):
        if timeout == 0:
            logger.warning(
                "You are using 0 as timeout in long polling which should be used for testing only."
            )
        while True:
            for raw_update in self.get_updates(
                    offset=offset,
                    limit=limit,
                    timeout=timeout,
                    allowed_updates=allowed_updates):
                update = TelegramObject(**raw_update)
                offset = update.update_id + 1
                asyncio.run(on_update_callback(self, update))

    def __getattr__(self, api_name):
        def api_method(**kwargs):
            return getattr(self.bot_api, api_name)(self.token, **kwargs)

        return api_method
