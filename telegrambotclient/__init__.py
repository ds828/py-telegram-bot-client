from telegrambotclient.api import TelegramBotAPI
from telegrambotclient.bot import TelegramBot
from telegrambotclient.router import TelegramRouter
from telegrambotclient.storage import TelegramStorage


class TelegramBotClient:
    __slots__ = ("bots", "routers", "name", "api_callers")

    def __init__(self, name: str = "bot-client") -> None:
        self.bots = {}
        self.routers = {}
        self.api_callers = {}
        self.name = name

    def router(self, name: str = "bot-router") -> TelegramRouter:
        router = self.routers.get(name, None)
        if router is None:
            self.routers[name] = TelegramRouter(name)
        return self.routers[name]

    def create_bot(self,
                   token: str,
                   router: TelegramRouter = None,
                   bot_api: TelegramBotAPI = None,
                   storage: TelegramStorage = None,
                   i18n_source=None,
                   session_expires: int = 1800) -> TelegramBot:

        router = router or self.router()
        if router.name not in self.routers:
            self.routers[router.name] = router
        bot_api = self.api_callers.get(
            bot_api.host if bot_api else TelegramBotAPI.DEFAULT_API_HOST, None)
        if bot_api is None:
            bot_api = TelegramBotAPI()
            self.api_callers[bot_api.host] = bot_api
        bot = TelegramBot(token, router, bot_api, storage, i18n_source,
                          session_expires)
        self.bots[token] = bot
        return bot

    async def dispatch(self, token: str, raw_update):
        bot = self.bots.get(token, None)
        if bot:
            await bot.dispatch(raw_update)


# default bot proxy
bot_client = TelegramBotClient()

__all__ = ("bot_client", )
