import logging
import os

import telebot
import validators
import pandas as pd
from pytube import YouTube

from bot.tools import get_video, save_csv

bot = telebot.TeleBot(os.getenv("TELEGRAM_API_KEY"))


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    button1 = telebot.types.InlineKeyboardButton("Сервис генерации синтетических данных", url='https://promo.sber.ru/syntdata')
    markup.add(button1)
    bot.send_message(message.chat.id,
                     "Привет, {0.first_name}".format(message.from_user),
                     reply_markup=markup)


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    # send reversed message if text is not link
    if not validators.url(message.text):
        bot.reply_to(message, message.text[::-1])
        return

    try:
        title, video_fname = get_video(message.text)
    except LookupError:
        bot.reply_to(message, "Cant download video")
        return
    bot.send_video(chat_id=message.chat.id, video=open(video_fname, 'rb'), supports_streaming=True)

    csv_fname = save_csv(title)
    bot.send_document(chat_id=message.chat.id, document=open(csv_fname, 'rb'))


def main():
    telebot.logger.setLevel(logging.DEBUG)
    bot.infinity_polling(logger_level=logging.DEBUG)


if __name__ == '__main__':
    main()
