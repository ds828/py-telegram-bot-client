#!/usr/bin/env python
from setuptools import setup

from telegrambotclient.api import TelegramBotAPI

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
    name='py-telegram-bot-client',
    version="{0}.{1}".format(TelegramBotAPI.__version__, 6.4),
    description='A Telegram Bot API Python Client',
    long_description_content_type="text/markdown",
    long_description=long_description,
    url='https://github.com/ds828/py-telegram-bot-client',
    author='ds828',
    author_email='songdi19@gmail.com',
    packages=['telegrambotclient'],
    install_requires=['urllib3', 'ujson'],
    python_requires=">=3.5",
)
