try:
    import ujson as json
except ImportError:
    import json

from io import BytesIO
from typing import Optional, Union
import urllib3

from telegrambotclient.base import (BotCommandScope, InputFile, InputMedia,
                                    TelegramBotException, TelegramObject)


def exclude_none(**kwargs):
    return {key: value for key, value in kwargs.items() if value is not None}


class TelegramBotAPIException(TelegramBotException):
    __slots__ = ("ok", "error_code", "parameters")

    def __init__(self, **kwargs) -> None:
        super().__init__(kwargs["description"])
        self.ok = kwargs["ok"]
        self.error_code = kwargs["error_code"]
        self.parameters = TelegramObject(
            **kwargs["parameters"]) if "parameters" in kwargs else {}


class TelegramBotAPI:
    API_URL = "/bot{0}/{1}"
    FILE_URL = "/file/bot{0}/{1}"
    __slots__ = ("api_caller", "host")

    def __init__(self,
                 host: str = "https://api.telegram.org",
                 maxsize: int = 10,
                 block: bool = True,
                 **pool_kwargs):
        class _TelegramBotAPICaller:
            __slots__ = ("pool", )

            def __init__(_self, maxsize: int, block: bool,
                         **connection_pool_kwargs):
                connection_pool_kwargs.get("headers", {}).update({
                    "connection":
                    "keep-alive",
                    "user-agent":
                    "telegram-bot-client: A Telegram Bot API Python client",
                })
                # from urllib3.connection.default_socket_options
                from socket import IPPROTO_TCP, SOL_SOCKET, TCP_NODELAY, SO_KEEPALIVE
                connection_pool_kwargs[
                    "socket_options"] = connection_pool_kwargs.get(
                        "socket_options", []) + [
                            (IPPROTO_TCP, TCP_NODELAY, 1),
                            (SOL_SOCKET, SO_KEEPALIVE, 1),
                        ]
                if self.host.startswith("https://"):
                    _self.pool = urllib3.HTTPSConnectionPool(
                        host=self.host[8:],
                        maxsize=maxsize,
                        block=block,
                        **connection_pool_kwargs)
                elif self.host.startswith("http://"):
                    _self.pool = urllib3.HTTPConnectionPool(
                        host=self.host[7:],
                        maxsize=maxsize,
                        block=block,
                        **connection_pool_kwargs)
                else:
                    raise TelegramBotException(
                        "Telegram Bot API only supports https:// and http://")

            @classmethod
            def __format_response__(cls, response):
                if response.status == 500:
                    raise TelegramBotException(response.data)
                json_response = json.loads(response.data.decode("utf-8"))
                if response.status == 200 and json_response["ok"]:
                    result = json_response.get("result", None)
                    if result and isinstance(result, dict):
                        return TelegramObject(**result)
                    return result
                raise TelegramBotAPIException(**json_response)

            def request(_self, api_url: str, data: dict, files: list):

                if not files:
                    return _self.__format_response__(
                        _self.pool.request(
                            "POST",
                            api_url,
                            body=json.dumps(data),
                            headers={'Content-Type': 'application/json'}))
                for file in files:
                    data[file[0]] = file[1]
                return _self.__format_response__(
                    _self.pool.request("POST", api_url, fields=data))

            def get_bytes(_self, file_path: str, chunk_size: int) -> bytes:
                response = _self.pool.request("GET",
                                              file_path,
                                              preload_content=False)
                try:
                    if response.status == 200:
                        with BytesIO() as buffer:
                            for chunk in response.stream(chunk_size):
                                buffer.write(chunk)
                            return buffer.getvalue()
                    raise TelegramBotException(response.data)
                finally:
                    response.release_conn()

        self.host = host
        self.api_caller = _TelegramBotAPICaller(maxsize=maxsize,
                                                block=block,
                                                **pool_kwargs)

    @classmethod
    def __prepare_request_params__(cls, **kwargs):
        api_data = exclude_none(**kwargs)
        files = []
        for field in tuple(api_data.keys()):
            value = api_data[field]
            if isinstance(value, (str, int, bool, float)):
                continue
            if isinstance(value, (list, tuple)):
                api_data[field] = json.dumps(value)
                continue
            if isinstance(value, TelegramObject):
                api_data[field] = value.data_
                continue
            if isinstance(value, InputFile):
                if field == "thumb":
                    files.append((value.attach_key, value.file_tuple))
                    api_data["thumb"] = value.attach_str
                else:
                    files.append((field, value.file_tuple))
                    del api_data[field]
        return api_data, files

    def call_api(self,
                 token: str,
                 api_name: str,
                 data: dict = {},
                 files: list = []):
        return self.api_caller.request(
            self.API_URL.format(token,
                                api_name.replace("_", "").lower()), data,
            files)

    def send_media_group(self, token: str, chat_id, media, **kwargs):
        assert 2 <= len(media) <= 10, True
        media_files = []
        media_group = []
        for input_media in media:
            assert isinstance(input_media, InputMedia), True
            media_files.extend(input_media.files)
            media_group.append(input_media.data_)
        api_data, files = self.__prepare_request_params__(chat_id=chat_id,
                                                          media=media_group,
                                                          **kwargs)
        return self.call_api(token,
                             "sendMediaGroup",
                             data=api_data,
                             files=media_files + files)

    def edit_message_media(self, token: str, chat_id: Optional[Union[int,
                                                                     str]],
                           message_id: Optional[int],
                           inline_message_id: Optional[int],
                           media: Optional[InputMedia], **kwargs):
        assert isinstance(media, InputMedia), True
        api_data, files = self.__prepare_request_params__(
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
            media=media,
            **kwargs)
        return self.call_api(token,
                             "editMessageMedia",
                             data=api_data,
                             files=media.files + files)

    def get_my_commands(self, token: str, scope: Optional[BotCommandScope],
                        language_code: Optional[str]):
        return tuple([
            TelegramObject(**raw_command) for raw_command in
            self.getMyCommands(token, scope=scope, language_code=language_code)
        ])

    def __getattr__(self, api_name: str):
        def bot_api_method(token: str, **kwargs):
            api_data, files = self.__prepare_request_params__(**kwargs)
            return self.call_api(token, api_name, data=api_data, files=files)

        return bot_api_method
