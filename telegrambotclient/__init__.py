import logging
import sys
from typing import Dict, Iterable, Optional

from telegrambotclient.api import TelegramBotAPICaller
from telegrambotclient.base import TelegramBotException, Update
from telegrambotclient.bot import TelegramBot
from telegrambotclient.handler import UpdateHandler
from telegrambotclient.router import TelegramRouter
from telegrambotclient.storage import TelegramStorage

logger = logging.getLogger("telegram-bot-client")
formatter = logging.Formatter(
    '%(levelname)s %(asctime)s (%(filename)s:%(lineno)d): "%(message)s"')
console_output_handler = logging.StreamHandler(sys.stderr)
console_output_handler.setFormatter(formatter)
logger.addHandler(console_output_handler)
logger.setLevel(logging.INFO)


class TelegramBotClient:
    """
    A bots and routers manager and updates dispatcher
    Attributes:
        _bot_data: a dict for saving bots
        _router_data: a dict for saving routers
        router: a function for creating a router
        _name: this proxy's name

    """

    __slots__ = ("_bot_data", "_router_data", "_name")

    def __init__(self, name: Optional[str] = None) -> None:
        self._bot_data = {}
        self._router_data = {}
        self._name = name or "default"

    @property
    def name(self):
        return self._name

    def router(
        self,
        name: Optional[str] = None,
        handlers: Optional[Iterable[UpdateHandler]] = None,
    ) -> TelegramRouter:
        name = name or "default"
        router = self._router_data.get(name, None)
        if router is None:
            self._router_data[name] = TelegramRouter(name, handlers)
        else:
            router.register_handlers(handlers)
        return self._router_data[name]

    def create_bot(self,
                   token: str,
                   router: Optional[TelegramRouter] = None,
                   handlers: Optional[Iterable[UpdateHandler]] = None,
                   storage: Optional[TelegramStorage] = None,
                   i18n_source: Optional[Dict] = None,
                   api_host: Optional[str] = None,
                   **urllib3_pool_kwargs):
        router = router or self.router(handlers=handlers)
        self._bot_data[token] = TelegramBot(
            token,
            router,
            storage,
            i18n_source,
            TelegramBotAPICaller(api_host=api_host
                                 or "https://api.telegram.org",
                                 **urllib3_pool_kwargs),
        )
        return self._bot_data[token]

    def bot(self, token: str) -> Optional[TelegramBot]:
        return self._bot_data.get(token, None)

    async def dispatch(self, token: str, raw_update: Dict):
        simple_bot = self._bot_data.get(token, None)
        if simple_bot is None:
            raise TelegramBotException(
                "No bot found with token: '{0}'".format(token))
        await simple_bot.dispatch(Update(**raw_update))


# default bot proxy
bot_client = TelegramBotClient()
