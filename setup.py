#!/usr/bin/env python
from setuptools import setup

from telegrambotclient import __version__

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
    name='py-telegram-bot-client',
    version=__version__,
    description='A Telegram Bot API Client written in Python',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/songdi/py-telegram-bot-client',
    author='Di SONG',
    author_email='songdi19@gmail.com',
    packages=['telegrambotclient'],
    install_requires=['urllib3', 'redis', 'ujson'],
    python_requires=">=3.5",
)
