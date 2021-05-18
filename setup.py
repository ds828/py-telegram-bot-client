#!/usr/bin/env python
from setuptools import setup

from telegrambotclient.api import TelegramBotAPI

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
    name='py-telegram-bot-client',
    version="{0}.{1}".format(TelegramBotAPI.__version__, 5),
    description='A Telegram Bot API Python Client',
    long_description_content_type="text/markdown",
    long_description=long_description,
    url='https://github.com/songdi/py-telegram-bot-client',
    author='Di SONG',
    author_email='songdi19@gmail.com',
    packages=['telegrambotclient'],
    install_requires=['urllib3', 'redis', 'ujson'],
    python_requires=">=3.5",
)
