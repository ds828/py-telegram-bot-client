import pprint
from functools import wraps
from io import StringIO
from typing import Iterable, Pattern, Dict, Tuple

try:
    import ujson as json
except ImportError:
    import json


def exclude_none(**kwargs) -> Dict:
    return {key: value for key, value in kwargs.items() if value is not None}


_pp = pprint.PrettyPrinter(indent=2)


def pretty_print(data: Dict):
    _pp.pprint(data)


def pretty_json(data: Dict) -> str:
    return _pp.pformat(data)


def regex_match(regex_patterns: Iterable[Pattern]):
    def decorate(method):
        @wraps(method)
        def wrapper(bot, message, *args, **kwargs):
            for pattern in regex_patterns:
                match_result = pattern.match(message.text)
                if match_result:
                    return method(bot, message, *args, match_result, **kwargs)
            return True

        return wrapper

    return decorate


def i18n(source: Dict):
    def decorate(method):
        @wraps(method)
        def wrapper(bot, data, *args, **kwargs):
            def _(text, lang=data.from_user.language_code):
                lang_source = source.get(lang, None)
                if lang_source:
                    if isinstance(lang_source, dict):
                        return lang_source.get(text, text)
                    return lang_source.gettext(text)
                return text

            return method(bot, data, *args, _, **kwargs)

        return wrapper

    return decorate


def build_callback_data(name: str, *args) -> str:
    return "{0}|{1}".format(name, json.dumps(args))


def parse_callback_data(callback_data: str, name: str):
    if callback_data.startswith(name):
        return tuple(json.loads(callback_data.split("|")[1]))
    return None


def build_force_reply_data(*args):
    return args


def parse_force_reply_data(force_reply_data: Iterable) -> Tuple:
    return force_reply_data[0], tuple(force_reply_data[1:])


def compose_message_entities(text_entities: Iterable, sep: str = " "):
    with StringIO() as buffer_:
        entities = []
        for text_entity in text_entities:
            if isinstance(text_entity, str):
                buffer_.write(text_entity)
                buffer_.write(sep)
                continue
            text, entity = text_entity
            entity.offset = buffer_.tell()
            entities.append(entity)
            if isinstance(text, str):
                buffer_.write(text)
                buffer_.write(sep)
                entity.length = len(text)
            elif isinstance(text, (list, tuple)):
                inner_text, inner_entities = compose_message_entities(text)
                offset = buffer_.tell()
                for inner_entity in inner_entities:
                    inner_entity.offset += offset
                buffer_.write(inner_text)
                buffer_.write(sep)
                entities += inner_entities
                entity.length = len(inner_text)
        return buffer_.getvalue(), tuple(entities)
