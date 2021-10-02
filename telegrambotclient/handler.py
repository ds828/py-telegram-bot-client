import asyncio
import re
from typing import Callable, Tuple, Union

from telegrambotclient.base import CallbackQuery, MessageField, UpdateField


class UpdateHandler:
    __slots__ = ("_callback", "_update_field")

    def __init__(self, callback: Callable, update_field: Union[UpdateField,
                                                               str]):
        self._callback = callback
        self._update_field = update_field.value if isinstance(
            update_field, UpdateField) else update_field

    @property
    def name(self):
        return "{0}.{1}".format(self._callback.__module__,
                                self._callback.__name__)

    @property
    def update_field(self) -> str:
        return self._update_field

    def __repr__(self) -> str:
        return self.name

    async def __call__(self, *args, **kwargs):
        return await self._callback(
            *args, **kwargs) if asyncio.iscoroutinefunction(
                self._callback) else self._callback(*args, **kwargs)


class ErrorHandler(UpdateHandler):
    __slots__ = ("errors", )

    def __init__(self, callback: Callable, errors: Tuple = None):
        super().__init__(callback=callback, update_field="error")
        self.errors = errors or (Exception, )


class CommandHandler(UpdateHandler):
    __slots__ = ("cmds", "delimiter")

    def __init__(self,
                 callback: Callable,
                 cmds: Tuple[str],
                 delimiter: str = " "):
        super().__init__(callback=callback, update_field="command")
        self.cmds = cmds
        self.delimiter = delimiter


class ForceReplyHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback=callback, update_field="force_reply")


class _MessageHandler(UpdateHandler):
    __slots__ = ("fields", )

    def __init__(self,
                 callback: Callable,
                 update_field: Union[UpdateField, str] = UpdateField.MESSAGE,
                 fields: Union[MessageField, str] = None):
        super().__init__(callback=callback, update_field=update_field)
        if isinstance(fields, MessageField):
            self.fields = fields.fields
        else:
            self.fields = fields


class MessageHandler(_MessageHandler):
    def __init__(self,
                 callback: Callable,
                 fields: Union[MessageField, str] = None):
        super().__init__(callback=callback,
                         update_field=UpdateField.MESSAGE,
                         fields=fields)


class EditedMessageHandler(_MessageHandler):
    def __init__(self,
                 callback: Callable,
                 fields: Union[MessageField, str] = None):
        super().__init__(callback=callback,
                         update_field=UpdateField.EDITED_MESSAGE,
                         fields=fields)


class ChannelPostHandler(_MessageHandler):
    def __init__(self,
                 callback: Callable,
                 fields: Union[MessageField, str] = None):
        super().__init__(callback=callback,
                         update_field=UpdateField.CHANNEL_POST,
                         fields=fields)


class EditedChannelPostHandler(_MessageHandler):
    def __init__(self,
                 callback: Callable,
                 fields: Union[MessageField, str] = None):
        super().__init__(callback=callback,
                         update_field=UpdateField.EDITED_CHANNEL_POST,
                         fields=fields)


class CallbackQueryHandler(UpdateHandler):
    __slots__ = ("callback_data", "callback_data_name",
                 "callback_data_patterns", "callback_data_parser",
                 "game_short_name", "_kwargs")

    def __init__(self,
                 callback: Callable,
                 callback_data: str = None,
                 callback_data_name: str = None,
                 callback_data_regex: Tuple[str] = None,
                 callback_data_parser: Callable = None,
                 game_short_name: str = None,
                 **kwargs):
        super().__init__(callback=callback,
                         update_field=UpdateField.CALLBACK_QUERY)
        self.callback_data = callback_data
        self.callback_data_name = callback_data_name
        self.callback_data_patterns = tuple(
            re.compile(regex) for regex in callback_data_regex) if isinstance(
                callback_data_regex, tuple) else ()
        self.callback_data_parser = callback_data_parser
        self.game_short_name = game_short_name
        self._kwargs = kwargs

    def match_callback_data(self, callback_query: CallbackQuery):
        for pattern in self.callback_data_patterns:
            if isinstance(callback_query.data, str):
                result = pattern.match(callback_query.data)
                if result:
                    return result
        return None

    def parse_callback_data(self, callback_query: CallbackQuery):
        if self.callback_data_parser:
            return self.callback_data_parser(callback_query.data,
                                             **self._kwargs)
        return False


class InlineQueryHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback=callback,
                         update_field=UpdateField.INLINE_QUERY)


class ChosenInlineResultHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback,
                         update_field=UpdateField.CHOSEN_INLINE_RESULT)


class ShippingQueryHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_field=UpdateField.SHIPPING_QUERY)


class PreCheckoutQueryHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_field=UpdateField.PRE_CHECKOUT_QUERY)


class PollHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_field=UpdateField.POLL)


class PollAnswerHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_field=UpdateField.POLL_ANSWER)


class MyChatMemberHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_field=UpdateField.MY_CHAT_MEMBER)


class ChatMemberHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_field=UpdateField.CHAT_MEMBER)


HandlerMapping = {
    UpdateField.MESSAGE: MessageHandler,
    UpdateField.EDITED_MESSAGE: EditedMessageHandler,
    UpdateField.CHANNEL_POST: ChannelPostHandler,
    UpdateField.EDITED_CHANNEL_POST: EditedChannelPostHandler,
    UpdateField.INLINE_QUERY: InlineQueryHandler,
    UpdateField.CHOSEN_INLINE_RESULT: ChosenInlineResultHandler,
    UpdateField.CALLBACK_QUERY: CallbackQueryHandler,
    UpdateField.SHIPPING_QUERY: ShippingQueryHandler,
    UpdateField.PRE_CHECKOUT_QUERY: PreCheckoutQueryHandler,
    UpdateField.POLL: PollHandler,
    UpdateField.POLL_ANSWER: PollAnswerHandler,
    UpdateField.MY_CHAT_MEMBER: MyChatMemberHandler,
    UpdateField.CHAT_MEMBER: ChatMemberHandler
}
