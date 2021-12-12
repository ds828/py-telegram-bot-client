import asyncio
from typing import Callable, Union

from telegrambotclient.base import MessageField, UpdateField


class UpdateHandler:
    __slots__ = ("callback", "update_field")

    def __init__(self, callback: Callable, update_field: Union[UpdateField,
                                                               str]):
        self.callback = callback
        self.update_field = update_field.value if isinstance(
            update_field, UpdateField) else update_field

    @property
    def callback_name(self):
        return "{0}.{1}".format(self.callback.__module__,
                                self.callback.__name__)

    def __repr__(self) -> str:
        return self.callback_name

    async def __call__(self, *args, **kwargs):
        return await self.callback(
            *args, **kwargs) if asyncio.iscoroutinefunction(
                self.callback) else self.callback(*args, **kwargs)


class ErrorHandler(UpdateHandler):
    __slots__ = ("errors", )

    def __init__(self, callback: Callable, *errors):
        super().__init__(callback=callback, update_field="error")
        self.errors = errors or (Exception, )


class CommandHandler(UpdateHandler):
    __slots__ = ("cmds", )

    def __init__(self, callback: Callable, *cmds):
        super().__init__(callback=callback, update_field="command")
        self.cmds = cmds


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
            self.fields = tuple(fields.fields)
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
    __slots__ = ("data", )

    def __init__(self,
                 callback: Callable,
                 callback_data: str = None,
                 game_short_name: str = None):
        super().__init__(callback=callback,
                         update_field=UpdateField.CALLBACK_QUERY)
        self.data = callback_data or game_short_name
        assert bool(self.data), True


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


class ChatJoinRequestHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_field=UpdateField.CHAT_JOIN_REQUEST)
