import io
import logging
import os
import zipfile
import datetime

import telebot
import validators
import pandas as pd

from typing import List
from pytube import YouTube
from telebot import types, custom_filters, StateMemoryStorage
from telebot.handler_backends import StatesGroup, State

from bot.tools import get_video, save_csv

state_storage = StateMemoryStorage()
bot = telebot.TeleBot(os.getenv("TELEGRAM_API_KEY"), state_storage=state_storage)
logger = logging.getLogger("bot")

FEEDBACK_OK = "👍"
FEEDBACK_BAD = "👎"

feedbacks = []
feedbacks_fname = f"feedbacks_{datetime.datetime.now()}.csv"


class MyStates(StatesGroup):
    start = State()
    upload_zip = State()
    upload_video = State()
    send_questions = State()
    generation = State()
    feedback = State()


@bot.message_handler(commands=['get_state'])
def get_state(message):
    bot.send_message(message.chat.id, str(bot.get_state(message.from_user.id, message.chat.id)))


@bot.message_handler(content_types=['text'], state=MyStates.start)
def handle_text(message):
    if message.text == "Картинки (zip)":
        bot.set_state(message.from_user.id, MyStates.upload_zip, message.chat.id)
        bot.reply_to(message, "Отправьте zip архив с картинками")
    if message.text == "Видео (ссылка)":
        bot.set_state(message.from_user.id, MyStates.upload_video, message.chat.id)
        bot.reply_to(message, "Отправьте ссылку на видео в Youtube")


@bot.message_handler(content_types=['document'], state=MyStates.upload_zip)
def handle_zip(message):
    file_info = bot.get_file(message.document.file_id)
    logger.debug(f"file_info: {file_info}")
    bytes = bot.download_file(file_info.file_path)
    z = zipfile.ZipFile(io.BytesIO(bytes))
    images_path = f'unzipped_images_{message.chat.id}'
    z.extractall(path=images_path)
    input_processed_info(message, images_path, msg='Картинки загружены')


@bot.message_handler(content_types=['text'], state=MyStates.upload_video)
def handle_video(message):
    if not validators.url(message.text):
        bot.reply_to(message, "Отправьте ссылку")
        return
    try:
        bot.send_message(message.chat.id, "Видео загружается. Подождите, пожалуйста. ")
        title, video_fname = get_video(message.text)
    except LookupError:
        bot.reply_to(message, "Cant download video")
        return
    images_path = process_video(video_fname)
    print('images processed')
    input_processed_info(message, images_path, msg='Видео загружено')


@bot.message_handler(content_types=['text'], state=MyStates.send_questions)
def handle_questions(message):
    if message.text == 'Завершить ввод вопросов':
        bot.set_state(message.from_user.id, MyStates.generation, message.chat.id)
        bot.reply_to(message, "Генерация данных начата. Подождите, пожалуйста.")
        generate_and_get_feedback(message)
    else:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['questions'].append(message.text)
        ask_questions(message)


@bot.message_handler(content_types=['text'], state=MyStates.feedback)
def handle_feedback(message):
    now = datetime.datetime.now()
    feedbacks.append((now, message.chat.id, message.text))
    pd.DataFrame(feedbacks, columns=['time', 'chat_id', 'text']).to_csv(feedbacks_fname, index=False)
    bot.delete_state(message.from_user.id, message.chat.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = types.KeyboardButton("/start")
    markup.add(btn)
    bot.send_message(message.chat.id, "Спасибо за обратную связь!",
                     reply_markup=markup)


@bot.message_handler(content_types=['text'])
def send_welcome(message):
    bot.set_state(message.from_user.id, MyStates.start, message.chat.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn1 = types.KeyboardButton("Картинки (zip)")
    btn2 = types.KeyboardButton("Видео (ссылка)")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id,
                     "Привет, {0.first_name}... . Выбери формат загружаемых данных.".format(message.from_user),
                     reply_markup=markup)


def input_processed_info(message, images_path, msg='Картинки загружены'):
    bot.set_state(message.from_user.id, MyStates.send_questions, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['images_folder'] = images_path
        data['questions'] = []

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = types.KeyboardButton("Завершить ввод вопросов")
    markup.add(btn)
    bot.send_message(message.chat.id, f"{msg}. Введите вопросы, на которые вы хотите получить ответы: ",
                     reply_markup=markup)


def ask_questions(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = types.KeyboardButton("Завершить ввод вопросов")
    markup.add(btn)
    bot.reply_to(message, "Вопрос записан, вы можете задать следующий вопрос.", reply_markup=markup)


def generate_and_get_feedback(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        res = generate(images_folder=data['images_folder'], questions=data['questions'])
    csv_path = f'df_{message.chat.id}.csv'
    res.to_csv(csv_path, index=False)
    bot.send_message(message.chat.id, "Данные успешно сгенерированы. ")
    bot.send_document(chat_id=message.chat.id, document=open(csv_path, 'rb'))
    ask_feedback(message)


def ask_feedback(message):
    bot.set_state(message.from_user.id, MyStates.feedback, message.chat.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn1 = types.KeyboardButton(FEEDBACK_OK)
    btn2 = types.KeyboardButton(FEEDBACK_BAD)
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "Оцените, пожалуйста, результат генерации".format(message.from_user),
                     reply_markup=markup)


def process_video(video_fname: str) -> str:
    # split video to images and save to folder
    result_folder_path = "some_images_path"
    return result_folder_path


def generate(images_folder: str, questions: List[str]) -> pd.DataFrame:
    # process images and get result
    res = pd.DataFrame({'test': [1]})
    print('images folder', images_folder)
    print('questions', questions)
    return res


def main():
    logging.getLogger("bot").setLevel(logging.DEBUG)
    telebot.logger.setLevel(logging.DEBUG)
    bot.add_custom_filter(custom_filters.StateFilter(bot))
    bot.infinity_polling(logger_level=logging.DEBUG)


if __name__ == '__main__':
    main()
