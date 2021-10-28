import asyncio
import logging
import sys
from contextlib import contextmanager
from typing import Callable, Dict, Tuple

from telegrambotclient.api import TelegramBotAPI
from telegrambotclient.base import Message, TelegramBotException
from telegrambotclient.storage import (MemoryStorage, TelegramSession,
                                       TelegramStorage)
from telegrambotclient.utils import pretty_format

logger = logging.getLogger("telegram-bot-client")
formatter = logging.Formatter(
    '%(levelname)s %(asctime)s (%(filename)s:%(lineno)d): "%(message)s"')
console_output_handler = logging.StreamHandler(sys.stderr)
console_output_handler.setFormatter(formatter)
logger.addHandler(console_output_handler)
logger.setLevel(logging.INFO)


class TelegramBot:
    SESSION_ID_FORMAT = "{0}:{1}"
    FORCE_REPLY_ID_FORMAT = "force_reply:{0}:{1}"
    __slots__ = ("id", "token", "router", "api", "storage", "i18n_source",
                 "last_update_id", "_bot_user")

    def __init__(self,
                 token: str,
                 router,
                 bot_api: TelegramBotAPI = None,
                 storage: TelegramStorage = None,
                 i18n_source: Dict = None):
        try:
            self.id = int(token.split(":")[0])
        except IndexError as error:
            raise TelegramBotException(
                "⚠️wrong token format: {0}".format(token)) from error
        self.token = token
        self.router = router
        self.api = bot_api or TelegramBotAPI()
        if storage is None:
            logger.warning(
                "⚠️You are using a memory storage which can not be persisted.")
            storage = MemoryStorage()
        self.storage = storage
        self.i18n_source = i18n_source
        self.last_update_id = 0
        self._bot_user = None

    @property
    def user(self):
        if self._bot_user is None:
            self._bot_user = self.get_me()
        return self._bot_user

    @property
    def next_call(self):
        return self.router.NEXT_CALL

    @property
    def stop_call(self):
        return self.router.STOP_CALL

    def __get_session__(self, session_id: str, expires: int = 0):
        return TelegramSession(session_id, self.storage, expires)

    def get_session(self, user_id: int, expires: int = 0):
        return self.__get_session__(
            self.SESSION_ID_FORMAT.format(self.id, user_id), expires)

    @contextmanager
    def session(self, user_id: int, expires: int = 0):
        session = self.get_session(user_id, expires)
        try:
            yield session
        finally:
            session.save()

    def join_force_reply(self,
                         user_id: int,
                         callback: Callable,
                         *force_reply_args,
                         expires: int = 60):
        force_reply_callback_name = "{0}.{1}".format(callback.__module__,
                                                     callback.__name__)
        assert self.router.has_force_reply_callback(
            force_reply_callback_name), True
        session = self.__get_session__(
            self.FORCE_REPLY_ID_FORMAT.format(self.id, user_id), expires)
        if force_reply_args:
            session["force_reply"] = [force_reply_callback_name
                                      ] + list(force_reply_args)
        else:
            session["force_reply"] = [force_reply_callback_name]
        session.save()

    def force_reply_done(self, user_id):
        session = self.__get_session__(
            self.FORCE_REPLY_ID_FORMAT.format(self.id, user_id))
        session.clear()

    def get_force_reply(self, user_id):
        session = self.__get_session__(
            self.FORCE_REPLY_ID_FORMAT.format(self.id, user_id))
        force_reply_data = session.get("force_reply", None)
        if not force_reply_data:
            return None, None
        return force_reply_data[0], tuple(force_reply_data[1:])

    def get_text(self, language_code: str, text: str):
        if self.i18n_source:
            lang_source = self.i18n_source.get(language_code, None)
            if lang_source:
                if isinstance(lang_source, dict):
                    return lang_source.get(text, text)
                return lang_source.gettext(text)
        return text

    def reply_message(self, message: Message, **kwargs):
        kwargs["reply_to_message_id"] = message.message_id
        return self.send_message(chat_id=message.chat.id, **kwargs)

    def get_file_url(self, file_path: str):
        return "{0}{1}".format(self.api.host,
                               self.api.FILE_URL.format(self.token, file_path))

    def get_file_bytes(self, file_path: str, chunk_size=128):
        return self.api.api_caller.get_bytes(
            self.api.FILE_URL.format(self.token, file_path),
            chunk_size=chunk_size,
        )

    def get_deep_link(self,
                      payload: str,
                      host: str = "https://t.me",
                      startgroup: bool = False):
        return "{0}/{1}?{2}={3}".format(
            host, self.user.username, "startgroup" if startgroup else "start",
            payload)

    async def dispatch(self, update):
        logger.debug(
            "\n---------------------------- update ---------------------------------\n{0}"
            .format(pretty_format(update)))
        await self.router.route(self, update)

    def run_polling(self,
                    limit: int = None,
                    timeout: int = 10,
                    allowed_updates: Tuple[str] = None,
                    **kwargs):
        if timeout == 0:
            logger.warning(
                "⚠️You are using 0 as timeout in seconds for long polling which should be used for testing purposes only."
            )
        while True:
            updates = self.api.get_updates(
                self.token,
                offset=self.last_update_id + 1,
                limit=limit,
                timeout=timeout,
                allowed_updates=allowed_updates,
                **kwargs,
            )
            if updates:
                self.last_update_id = updates[-1]["update_id"]
                for update in updates:
                    asyncio.run(self.dispatch(update))

    def __getattr__(self, api_name):
        def api_method(**kwargs):
            return getattr(self.api, api_name)(self.token, **kwargs)

        return api_method
