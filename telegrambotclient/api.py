try:
    import ujson as json
except ImportError:
    import json

import socket
from io import BytesIO
from typing import List

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

    DEFAULT_API_HOST = "https://api.telegram.org"
    API_URL = "/bot{0}/{1}"
    FILE_URL = "/file/bot{0}/{1}"
    __slots__ = ("api_caller", )

    def __init__(self,
                 api_host: str = None,
                 maxsize: int = 10,
                 block: bool = True,
                 **pool_kwargs):
        class _TelegramBotAPICaller:
            __slots__ = ("pool", "api_host")

            def __init__(self, api_host: str, maxsize: int, block: bool,
                         **connection_pool_kwargs):
                self.api_host = api_host
                connection_pool_kwargs.get("headers", {}).update({
                    "connection":
                    "keep-alive",
                    "user-agent":
                    "telegram-bot-client: A Telegram Bot API Python Provider",
                })
                connection_pool_kwargs["socket_options"] = (
                    connection_pool_kwargs.get("socket_options", []) + [
                        (socket.IPPROTO_TCP, socket.TCP_NODELAY,
                         1),  # from urllib3.connection.default_socket_options
                        (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
                    ])
                if api_host.startswith("https://"):
                    self.pool = urllib3.HTTPSConnectionPool(
                        host=self.api_host[8:],
                        maxsize=maxsize,
                        block=block,
                        **connection_pool_kwargs)
                elif api_host.startswith("http://"):
                    self.pool = urllib3.HTTPConnectionPool(
                        host=self.api_host[7:],
                        maxsize=maxsize,
                        block=block,
                        **connection_pool_kwargs)
                else:
                    raise TelegramBotException(
                        "Telegram Bot API Host only supports https:// and http://"
                    )

            @staticmethod
            def __format_response__(response):
                if response.status == 500:
                    raise TelegramBotException(response.data)
                json_response = json.loads(response.data.decode("utf-8"))
                if response.status == 200 and json_response["ok"]:
                    result = json_response["result"]
                    if result and isinstance(result, dict):
                        return TelegramObject(**result)
                    return result
                raise TelegramBotAPIException(**json_response)

            def call(self, api_url: str, data=None, files=None):
                if data is None:
                    data = {}
                if not files:
                    return self.__format_response__(
                        self.pool.request(
                            "POST",
                            api_url,
                            body=json.dumps(data).encode("utf-8"),
                            headers={"Content-Type": "application/json"},
                        ))
                for _ in files:
                    data[_[0]] = _[1]
                return self.__format_response__(
                    self.pool.request("POST", api_url, fields=data))

            def get_bytes(self,
                          file_path: str,
                          chunk_size: int = 128) -> bytes:
                response = self.pool.request("GET",
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

        self.api_caller = _TelegramBotAPICaller(
            api_host=api_host.lower() if api_host else self.DEFAULT_API_HOST,
            maxsize=maxsize,
            block=block,
            **pool_kwargs)

    @property
    def host(self):
        return self.api_caller.api_host

    @staticmethod
    def __prepare_request_data__(**kwargs):
        api_data = exclude_none(**kwargs)
        files = []
        for field in tuple(api_data.keys()):
            value = api_data[field]
            if isinstance(value, (str, int, bool, float, list, tuple)):
                continue
            if isinstance(value, TelegramObject):
                api_data[field] = value.data_
            elif isinstance(value, InputFile):
                if field == "thumb":
                    files.append((value.attach_key, value.file_tuple))
                    api_data["thumb"] = value.attach_str
                else:
                    files.append((field, value.file_tuple))
                    del api_data[field]
        return api_data, files

    def call_api(self, token: str, api_name: str, data=None, files=None):
        return self.api_caller.call(
            self.API_URL.format(token,
                                api_name.replace("_", "").lower()), data,
            files)

    def __getattr__(self, api_name: str):
        def bot_api_method(token: str, **kwargs):
            api_data, files = self.__prepare_request_data__(**kwargs)
            return self.call_api(token, api_name, data=api_data, files=files)

        return bot_api_method

    def get_updates(self, token: str, **kwargs):
        if "allowed_updates" in kwargs:
            kwargs["allowed_updates"] = json.dumps(kwargs["allowed_updates"])
        return tuple(self.getUpdates(token, **kwargs))

    def set_webhook(self, token: str, **kwargs):
        if "allowed_updates" in kwargs:
            kwargs["allowed_updates"] = json.dumps(kwargs["allowed_updates"])
        return self.setWebhook(token, **kwargs)

    def send_media_group(self, token: str, chat_id, media: List[InputMedia],
                         **kwargs):
        assert 2 <= len(media) <= 10, True
        all_files = []
        media_group = []
        for input_media in media:
            assert isinstance(input_media, InputMedia), True
            all_files.extend(input_media.files)
            media_group.append(input_media.data_)
        api_data, files = self.__prepare_request_data__(
            chat_id=chat_id, media=json.dumps(media_group), **kwargs)
        return self.call_api(token,
                             "sendMediaGroup",
                             data=api_data,
                             files=all_files + files)

    def edit_message_media(self,
                           token: str,
                           chat_id=None,
                           message_id: int = None,
                           inline_message_id: int = None,
                           media: InputMedia = None,
                           **kwargs):
        assert isinstance(media, InputMedia), True
        api_data, files = self.__prepare_request_data__(
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
            media=json.dumps(media.data_),
            **kwargs)
        return self.call_api(token,
                             "editMessageMedia",
                             data=api_data,
                             files=media.files + files)

    def set_my_commands(self,
                        token: str,
                        commands,
                        scope: BotCommandScope = None,
                        language_code: str = None):
        assert len(commands) <= 100, True
        data = {
            "commands": json.dumps(commands),
            "scope": json.dumps(scope) if scope else None,
            "language_code": language_code
        }
        return self.call_api(token, "setmycommands", data=exclude_none(**data))

    def delete_my_commands(self,
                           token: str,
                           scope: BotCommandScope = None,
                           language_code: str = None):
        data = {
            "scope": json.dumps(scope) if scope else None,
            "language_code": language_code,
        }
        return self.call_api(token,
                             "deletemycommands",
                             data=exclude_none(**data))

    def get_my_commands(self,
                        token: str,
                        scope: BotCommandScope = None,
                        language_code: str = None):
        data = {
            "scope": json.dumps(scope) if scope else None,
            "language_code": language_code,
        }
        return tuple(
            TelegramObject(**command) for command in self.call_api(
                token, "getmycommands", data=exclude_none(**data)))

    def send_poll(self, token: str, chat_id, question: str, options: List[str],
                  **kwargs):
        assert 2 <= len(options) <= 10, True
        api_data, files = self.__prepare_request_data__(
            chat_id=chat_id,
            question=question,
            options=json.dumps(options),
            **kwargs)
        return self.call_api(token, "sendPoll", data=api_data, files=files)

    def answer_inline_query(self, token: str, inline_query_id: str, results,
                            **kwargs):
        assert len(results) <= 50, True
        api_data, files = self.__prepare_request_data__(
            inline_query_id=inline_query_id,
            results=json.dumps(results),
            **kwargs)
        return self.call_api(token,
                             "answerInlineQuery",
                             data=api_data,
                             files=files)

    def send_invoice(self, token: str, chat_id: int, title: str,
                     description: str, payload: str, provider_token: str,
                     currency: str, prices, **kwargs):
        provider_data = kwargs.get("provider_data", None)
        if provider_data:
            kwargs["provider_data"] = json.dumps(provider_data)
        suggested_tip_amounts = kwargs.get("suggested_tip_amounts", None)
        if suggested_tip_amounts:
            kwargs["suggested_tip_amounts"] = json.dumps(suggested_tip_amounts)
        api_data, files = self.__prepare_request_data__(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token=provider_token,
            currency=currency,
            prices=json.dumps(prices),
            **kwargs)
        return self.call_api(token, "sendInvoice", data=api_data, files=files)

    def answer_shipping_query(self,
                              token: str,
                              shipping_query_id: str,
                              ok: bool = True,
                              **kwargs):

        if ok:
            assert "shipping_options" in kwargs, True
            kwargs["shipping_options"] = json.dumps(kwargs["shipping_options"])
        else:
            assert "error_message" in kwargs, True
        api_data, files = self.__prepare_request_data__(
            shipping_query_id=shipping_query_id, ok=ok, **kwargs)
        return self.call_api(token,
                             "answerShippingQuery",
                             data=api_data,
                             files=files)

    def set_passport_data_errors(self, token: str, user_id: int, errors):
        api_data, files = self.__prepare_request_data__(
            user_id=user_id, errors=json.dumps(errors))
        return self.call_api(token,
                             "setPassportDataErrors",
                             data=api_data,
                             files=files)
