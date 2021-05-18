import asyncio
import logging
import os
from contextlib import contextmanager
from typing import Callable, Dict, Iterable, Optional, Tuple

from telegrambotclient.api import TelegramBotAPI
from telegrambotclient.base import (InputFile, Message, TelegramBotException,
                                    Update)
from telegrambotclient.storage import (MemoryStorage, TelegramSession,
                                       TelegramStorage)
from telegrambotclient.utils import (build_force_reply_data,
                                     parse_force_reply_data, pretty_format)

logger = logging.getLogger("telegram-bot-client")


class TelegramBot:
    _force_reply_key_format = "bot:force_reply:{0}"
    __slots__ = ("_bot_id", "_token", "_router", "_bot_api", "_storage",
                 "_i18n_source", "last_update_id", "_bot_user")

    def __init__(
        self,
        token: str,
        router,
        storage: Optional[TelegramStorage] = None,
        i18n_source: Optional[Dict] = None,
        bot_api: Optional[TelegramBotAPI] = None,
    ):
        try:
            self._bot_id = int(token.split(":")[0])
        except IndexError as error:
            raise TelegramBotException(
                "wrong token format: {0}".format(token)) from error
        self._token = token
        self._router = router
        if storage:
            assert isinstance(storage, TelegramStorage), True
        else:
            logger.warning(
                "You are using a memory storage which can not be persisted.")
            storage = MemoryStorage()
        self._storage = storage
        self._i18n_source = i18n_source
        if bot_api:
            assert isinstance(bot_api, TelegramBotAPI), True
        else:
            logger.warning(
                "Your bot api is not a TelegramBotAPI instance. A default bot api is using."
            )
            bot_api = TelegramBotAPI()
        self._bot_api = bot_api
        self.last_update_id = 0
        self._bot_user = None

    def __getattr__(self, api_name):
        if api_name.startswith("reply"):

            def reply_method(message: Message, **kwargs):
                """reply shotcuts.
                Such as sendMessge, sendPhoto, you can use reply_xxx to reply directly

                Args:
                    message (Message): message sent from the replying user
                    kwargs: other kwargs of sendXXX api method
                """
                kwargs.update({
                    "chat_id": message.chat.id,
                    "reply_to_message_id": message.message_id,
                })
                return getattr(self._bot_api, "send{0}".format(
                    api_name.split("reply")[1]))(self.token, **kwargs)

            return reply_method

        def api_method(**kwargs):
            return getattr(self._bot_api, api_name)(self.token, **kwargs)

        return api_method

    @property
    def token(self) -> str:
        return self._token

    @property
    def router(self):
        return self._router

    @property
    def api(self):
        return self._bot_api

    @property
    def id(self) -> int:
        return self._bot_id

    @property
    def user(self):
        if self._bot_user is None:
            self._bot_user = self.get_me()
        return self._bot_user

    @property
    def next_call(self):
        return self.router.next_call

    @property
    def stop_call(self):
        return self.router.stop_call

    async def dispatch(self, update: Update):
        logger.debug(
            """
----------------------- UPDATE BEGIN ---------------------------
%s
----------------------- UPDATE  END  ---------------------------
""",
            pretty_format(update),
        )
        await self._router.route(self, update)

    def join_force_reply(
        self,
        user_id: int,
        callback: Callable,
        *force_reply_args,
        expires: int = 1800,
    ):
        force_reply_callback_name = "{0}.{1}".format(callback.__module__,
                                                     callback.__name__)
        if not self.router.has_force_reply_callback(force_reply_callback_name):
            raise TelegramBotException(
                "{0} is not a force reply callback".format(
                    force_reply_callback_name))
        field = self._force_reply_key_format.format(user_id)
        with self.session(user_id, expires) as session:
            if force_reply_args:
                session.set(
                    field,
                    build_force_reply_data(force_reply_callback_name,
                                           *force_reply_args))
            else:
                session.set(field,
                            build_force_reply_data(force_reply_callback_name))

    def force_reply_done(self, user_id: int):
        session = self.get_session(user_id)
        del session[self._force_reply_key_format.format(user_id)]

    def get_force_reply(self, user_id: int) -> Tuple:
        session = self.get_session(user_id)
        force_reply_data = session.get(
            self._force_reply_key_format.format(user_id), None)
        if not force_reply_data:
            return None, None
        return parse_force_reply_data(force_reply_data)

    def get_session(self,
                    user_id: int,
                    expires: int = 1800) -> TelegramSession:
        return TelegramSession(self.id, user_id, self._storage, expires)

    @contextmanager
    def session(self, user_id: int, expires: int = 1800):
        session = self.get_session(user_id, expires)
        try:
            yield session
        finally:
            session.save()

    def get_text(self, lang_code: str, text: str) -> str:
        if self._i18n_source:
            lang_source = self._i18n_source.get(lang_code, None)
            if lang_source:
                if isinstance(lang_source, dict):
                    return lang_source.get(text, text)
                return lang_source.gettext(text)
        return text

    def setup_webhook(
        self,
        webhook_url: str,
        certificate: Optional[InputFile] = None,
        max_connections: Optional[int] = None,
        allowed_updates: Optional[Iterable[str]] = None,
        **kwargs,
    ) -> bool:
        """set a bot run in webhook model

        Args:
            webhook_url (str): webhook_url
            certificate (Optional[InputFile]): certificate
            max_connections (Optional[int]): max_connections
            allowed_updates (Optional[Iterable[str]]): allowed_updates
            kwargs:

        Returns:
            bool:
        """
        webhook_info = self.get_webhook_info()
        if webhook_info.url != webhook_url:
            self.set_webhook()
            return self.set_webhook(
                url=webhook_url,
                certificate=certificate,
                max_connections=max_connections,
                allowed_updates=allowed_updates,
                **kwargs,
            )
        return True

    def download_file(self, src_file_path: str, save_to_file: str):
        """download_file.

        Args:
            src_file_path (str): src_file_path
            save_to_file (str): save_to_file
        """
        file_path = os.path.dirname(save_to_file)
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        file_bytes = self.get_file_bytes(file_path=src_file_path)
        with open(save_to_file, "wb") as new_file:
            new_file.write(file_bytes)

    def run_polling(
        self,
        limit: Optional[int] = None,
        timeout: Optional[int] = None,
        allowed_updates: Optional[Iterable[str]] = None,
        **kwargs,
    ):
        """run a bot in long loop model.

        Args:
            get_updates_kwargs: kwargs of telegram bot api 'getUpdates'
        """
        if not timeout:
            logger.warning(
                "You are using 0 as timeout in seconds for long polling which should be used for testing purposes only."
            )
        while True:
            updates = self._bot_api.get_updates(
                self.token,
                offset=self.last_update_id + 1,
                limit=limit,
                timeout=timeout,
                allowed_updates=allowed_updates,
                **kwargs,
            )
            if updates:
                self.last_update_id = updates[-1].update_id
                for update in updates:
                    asyncio.run(self.dispatch(update))
