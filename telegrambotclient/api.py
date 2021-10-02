try:
    import ujson as json
except ImportError:
    import json

import socket

import urllib3

from telegrambotclient.base import (BotCommandScope, InputFile, InputMedia,
                                    TelegramBotException, TelegramDict,
                                    TelegramList)
from telegrambotclient.utils import exclude_none

DEFAULT_API_HOST = "https://api.telegram.org"


class TelegramBotAPIException(TelegramBotException):
    def __init__(self, ok, description, error_code, parameters={}) -> None:
        super().__init__(description)
        self.ok = ok
        self.error_code = error_code
        self.parameters = TelegramDict(**parameters)


class TelegramBotAPI:

    __version__ = "5.3"
    _api_url = "/bot{0}/{1}"
    download_url = "/file/bot{0}/{1}"
    __slots__ = ("_api_caller", )

    def __init__(self,
                 api_host: str = DEFAULT_API_HOST,
                 maxsize: int = 10,
                 block: bool = True,
                 **pool_kwargs):
        class TelegramBotAPICaller:
            __slots__ = ("_pool", "api_host")
            _json_header = {"Content-Type": "application/json"}

            def __init__(self, api_host: str, maxsize: int, block: bool,
                         **other_pool_kwargs):
                self.api_host = api_host.lower(
                ) if api_host else DEFAULT_API_HOST
                other_pool_kwargs.get("headers", {}).update({
                    "connection":
                    "keep-alive",
                    "user-agent":
                    "telegram-bot-client: A Telegram Bot API Python Provider",
                })
                other_pool_kwargs["socket_options"] = (
                    other_pool_kwargs.get("socket_options", []) + [
                        (socket.IPPROTO_TCP, socket.TCP_NODELAY,
                         1),  # from urllib3.connection.default_socket_options
                        (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
                    ])
                if api_host.startswith("https://"):
                    self._pool = urllib3.HTTPSConnectionPool(
                        host=self.api_host[8:],
                        maxsize=maxsize,
                        block=block,
                        **other_pool_kwargs)
                elif api_host.startswith("http://"):
                    self._pool = urllib3.HTTPConnectionPool(
                        host=self.api_host[7:],
                        maxsize=maxsize,
                        block=block,
                        **other_pool_kwargs)
                else:
                    raise TelegramBotException(
                        "Telegram Bot API Host only supports https:// and http://"
                    )

            @staticmethod
            def __format_response(response):
                if response.status == 500:
                    raise TelegramBotException(response.data)
                json_response = json.loads(response.data.decode("utf-8"))
                if response.status == 200 and json_response["ok"]:
                    result = json_response["result"]
                    if isinstance(result, dict):
                        return TelegramDict(**result)
                    if isinstance(result, list):
                        return TelegramList(result)
                    return result
                raise TelegramBotAPIException(**json_response)

            def __call__(self, api_url: str, data=None, files=None):
                if data is None:
                    data = {}
                if not files:
                    return self.__format_response(
                        self._pool.request(
                            "POST",
                            api_url,
                            body=json.dumps(data).encode("utf-8"),
                            headers=self._json_header,
                        ))
                for _ in files:
                    data[_[0]] = _[1]
                return self.__format_response(
                    self._pool.request("POST", api_url, fields=data))

        self._api_caller = TelegramBotAPICaller(api_host=api_host,
                                                maxsize=maxsize,
                                                block=block,
                                                **pool_kwargs)

    @property
    def host(self):
        return self._api_caller.api_host

    @staticmethod
    def __prepare_request_data(api_name, **kwargs):
        api_data = exclude_none(**kwargs)
        attached_files = []
        for field in tuple(api_data.keys()):
            value = api_data[field]
            if isinstance(value, TelegramDict):
                api_data[field] = value.param
                continue
            if isinstance(value, InputFile):
                if field == "thumb":
                    attached_files.append((value.attach_key, value.file_tuple))
                    api_data["thumb"] = value.attach_str
                else:
                    attached_files.append((field, value.file_tuple))
                    del api_data[field]
        return api_name.replace("_", "").lower(), api_data, attached_files

    def __call_api(self, token: str, api_name: str, data=None, files=None):
        return self._api_caller(self._api_url.format(token, api_name), data,
                                files)

    def __getattr__(self, api_name: str):
        def bot_api_method(token: str, **kwargs):
            real_api_name, form_data, attached_files = self.__prepare_request_data(
                api_name, **kwargs)
            return self.__call_api(token,
                                   real_api_name,
                                   data=form_data,
                                   files=attached_files)

        return bot_api_method

    def get_updates(self, token: str, **kwargs):
        if "allowed_updates" in kwargs:
            kwargs["allowed_updates"] = json.dumps(kwargs["allowed_updates"])
        return tuple(self.getUpdates(token, **kwargs))

    def set_webhook(self, token: str, **kwargs):
        if "allowed_updates" in kwargs:
            kwargs["allowed_updates"] = json.dumps(kwargs["allowed_updates"])
        return self.setwebhook(token, **kwargs)

    def send_media_group(self, token: str, chat_id, media, **kwargs):
        if 2 <= len(media) <= 10:
            files = []
            media_group = []
            for input_media in media:
                if isinstance(input_media, InputMedia):
                    files.extend(input_media.attached_files)
                    media_group.append(input_media.media_data)
            real_api_name, form_data, attached_files = self.__prepare_request_data(
                "sendMediaGroup",
                chat_id=chat_id,
                media=json.dumps(media_group),
                **kwargs)
            return self.__call_api(
                token,
                real_api_name,
                data=form_data,
                files=attached_files + files if attached_files else files,
            )
        raise TelegramBotException("'media' must include 2-10 items")

    def edit_message_media(self,
                           token: str,
                           chat_id=None,
                           message_id: int = None,
                           inline_message_id: int = None,
                           media: InputMedia = None,
                           **kwargs):
        if not media:
            raise TelegramBotException("'media' is required")
        real_api_name, form_data, attached_files = self.__prepare_request_data(
            "editMessageMedia",
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
            media=json.dumps(media.media_data),
            **kwargs)
        return self.__call_api(
            token,
            real_api_name,
            data=form_data,
            files=attached_files +
            media.attached_files if attached_files else media.attached_files,
        )

    def set_my_commands(self,
                        token: str,
                        commands,
                        scope: BotCommandScope = None,
                        language_code: str = None):
        data = {
            "commands": json.dumps(commands),
            "scope": json.dumps(scope) if scope else None,
            "language_code": language_code
        }
        return self.__call_api(token,
                               "setmycommands",
                               data=exclude_none(**data))

    def delete_my_commands(self,
                           token: str,
                           scope: BotCommandScope = None,
                           language_code: str = None):
        data = {
            "scope": json.dumps(scope) if scope else None,
            "language_code": language_code,
        }
        return self.__call_api(token,
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
        return self.__call_api(token,
                               "getmycommands",
                               data=exclude_none(**data))

    def send_poll(self, token: str, chat_id, question: str, options, **kwargs):
        real_api_name, form_data, attached_files = self.__prepare_request_data(
            "sendPoll",
            chat_id=chat_id,
            question=question,
            options=json.dumps(options),
            **kwargs)
        return self.__call_api(token,
                               real_api_name,
                               data=form_data,
                               files=attached_files)

    def answer_inline_query(self, token: str, inline_query_id: str, results,
                            **kwargs):
        real_api_name, form_data, attached_files = self.__prepare_request_data(
            "answerInlineQuery",
            inline_query_id=inline_query_id,
            results=json.dumps(results),
            **kwargs)
        return self.__call_api(token,
                               real_api_name,
                               data=form_data,
                               files=attached_files)

    def send_invoice(self, token: str, chat_id: int, title: str,
                     description: str, payload: str, provider_token: str,
                     currency: str, prices, **kwargs):
        provider_data = kwargs.get("provider_data", None)
        if provider_data:
            kwargs["provider_data"] = json.dumps(provider_data)
        suggested_tip_amounts = kwargs.get("suggested_tip_amounts", None)
        if suggested_tip_amounts:
            kwargs["suggested_tip_amounts"] = json.dumps(suggested_tip_amounts)
        real_api_name, form_data, attached_files = self.__prepare_request_data(
            "sendInvoice",
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token=provider_token,
            currency=currency,
            prices=json.dumps(prices),
            **kwargs)
        return self.__call_api(token,
                               real_api_name,
                               data=form_data,
                               files=attached_files)

    def answer_shipping_query(self,
                              token: str,
                              shipping_query_id: str,
                              ok: bool = True,
                              **kwargs):

        if ok:
            if "shipping_options" not in kwargs:
                raise TelegramBotException(
                    "'shipping_options' is required when ok is True")
            kwargs["shipping_options"] = json.dumps(kwargs["shipping_options"])
        else:
            if "error_message" not in kwargs:
                raise TelegramBotException(
                    "'error_message' is required when ok is False")
        real_api_name, form_data, attached_files = self.__prepare_request_data(
            "answerShippingQuery",
            shipping_query_id=shipping_query_id,
            ok=ok,
            **kwargs)
        return self.__call_api(token,
                               real_api_name,
                               data=form_data,
                               files=attached_files)

    def set_passport_data_errors(self, token: str, user_id: int, errors):
        real_api_name, form_data, attached_files = self.__prepare_request_data(
            "setPassportDataErrors",
            user_id=user_id,
            errors=json.dumps(errors))
        return self.__call_api(token,
                               real_api_name,
                               data=form_data,
                               files=attached_files)
