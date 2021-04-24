#!/usr/bin/env python
from setuptools import setup

from simpletelegrambot import __version__

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
    name='simple-telegram-bot',
    version=__version__,
    description='A Telegram Bot API Client written by Python',
    long_description=long_description,
    url='https://github.com/songdi/simple-telegram-bot',
    author='Di SONG',
    author_email='songdi19@gmail.com',
    packages=['simpletelegrambot'],
    install_requires=['urllib3', 'redis', 'ujson'],
    python_requires=">=3.5",
)
