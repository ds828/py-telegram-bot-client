from telegrambotclient.api import (DEFAULT_API_HOST, TelegramBotAPI,
                                   TelegramBotAPIException)
from telegrambotclient.base import TelegramBotException, Update
from telegrambotclient.bot import TelegramBot
from telegrambotclient.router import TelegramRouter
from telegrambotclient.storage import TelegramStorage


class TelegramBotClient:
    __slots__ = ("_bot_data", "_router_data", "_name", "_bot_api_data")

    def __init__(self, name: str = "default-client") -> None:
        self._bot_data = {}
        self._router_data = {}
        self._bot_api_data = {}
        self._name = name

    @property
    def name(self):
        return self._name

    def router(self, name: str = "default-router") -> TelegramRouter:
        router = self._router_data.get(name, None)
        if router is None:
            self._router_data[name] = TelegramRouter(name)
        return self._router_data[name]

    def create_bot(
        self,
        token: str,
        router: TelegramRouter = None,
        storage: TelegramStorage = None,
        i18n_source=None,
        bot_api: TelegramBotAPI = None,
    ) -> TelegramBot:
        bot_api = self._bot_api_data.get(
            bot_api.host if bot_api else DEFAULT_API_HOST, None)
        if bot_api is None:
            bot_api = TelegramBotAPI()
            self._bot_api_data[bot_api.host] = bot_api
        router = router or self.router()
        bot = TelegramBot(token, router, storage, i18n_source, bot_api)
        try:
            bot.user
        except TelegramBotAPIException as error:
            raise TelegramBotException("The bot is not available") from error
        else:
            self._bot_data[token] = bot
            return bot

    def bot(self, token: str) -> TelegramBot:
        return self._bot_data.get(token, None)

    async def dispatch(self, token: str, raw_update):
        simple_bot = self._bot_data.get(token, None)
        if simple_bot is None:
            raise TelegramBotException(
                "No bot found with token: '{0}'".format(token))
        await simple_bot.dispatch(Update(**raw_update))


# default bot proxy
bot_client = TelegramBotClient()
