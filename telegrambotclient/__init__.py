from telegrambotclient.api import (DEFAULT_API_HOST, TelegramBotAPI,
                                   TelegramBotAPIException)
from telegrambotclient.base import TelegramBotException
from telegrambotclient.bot import TelegramBot
from telegrambotclient.router import TelegramRouter
from telegrambotclient.storage import TelegramStorage


class TelegramBotClient:
    __slots__ = ("bots", "routers", "name", "api_callers")

    def __init__(self, name: str = "default-client") -> None:
        self.bots = {}
        self.routers = {}
        self.api_callers = {}
        self.name = name

    def router(self, name: str = "default-router") -> TelegramRouter:
        router = self.routers.get(name, None)
        if router is None:
            self.routers[name] = TelegramRouter(name)
        return self.routers[name]

    def create_bot(
        self,
        token: str,
        router: TelegramRouter = None,
        storage: TelegramStorage = None,
        i18n_source=None,
        bot_api: TelegramBotAPI = None,
    ) -> TelegramBot:
        bot_api = self.api_callers.get(
            bot_api.host if bot_api else DEFAULT_API_HOST, None)
        if bot_api is None:
            bot_api = TelegramBotAPI()
            self.api_callers[bot_api.host] = bot_api
        router = router or self.router()
        if router.name not in self.routers:
            self.routers[router.name] = router
        bot = TelegramBot(token, router, storage, i18n_source, bot_api)
        try:
            bot.user
        except TelegramBotAPIException as error:
            raise TelegramBotException("The bot is not available") from error
        else:
            self.bots[token] = bot
            return bot

    async def dispatch(self, token: str, update):
        bot = self.bots.get(token, None)
        if bot:
            await bot.dispatch(update)


# default bot proxy
bot_client = TelegramBotClient()
