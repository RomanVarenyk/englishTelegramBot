import random
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from threading import Timer, Event
from dotenv import load_dotenv
import os

import gptStuff

load_dotenv()
telegramKey = os.getenv('telegramKey')
currentWord = ""
bot = telebot.TeleBot(telegramKey)

user_state = {}
user_timers = {}

wordList = []
with open('words.txt', 'r', encoding='utf-8') as file:
    for line in file:
        wordList.append(line.strip())


def reset_state(chat_id):
    global user_state
    if chat_id in user_state:
        del user_state[chat_id]


def cancel_timer(chat_id):
    if chat_id in user_timers:
        user_timers[chat_id][1].set()
        user_timers[chat_id][0].cancel()
        del user_timers[chat_id]


def send_main_menu(chat_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("Practice words", callback_data='words'),
        InlineKeyboardButton("Practice grammar", callback_data='grammar'),
        InlineKeyboardButton("Practice listening", callback_data='listening'),
        InlineKeyboardButton("Practice conversation (experimental)", callback_data='convo')
    )
    bot.send_message(chat_id, "Pick one", reply_markup=markup)
    reset_state(chat_id)
    cancel_timer(chat_id)


def send_word_prompt(chat_id):
    wordNum = random.randint(0, len(wordList) - 1)
    currentWord = wordList[wordNum]
    bot.send_message(chat_id, f'Слово: {currentWord}')
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("Показати", callback_data='show'))
    bot.send_message(chat_id,
                     "У вас є 1 хвилина щоб згадати слово, І натиснути кнопку показати. Якщо не натисните то ви повернетесь в головне меню",
                     reply_markup=markup)
    user_state[chat_id] = 'waiting_for_word'
    reset_timer(chat_id)


def reset_timer(chat_id):
    cancel_timer(chat_id)
    stop_event = Event()
    timer = Timer(30.0, send_main_menu_if_inactive, [chat_id, stop_event])
    user_timers[chat_id] = (timer, stop_event)
    timer.start()


def send_main_menu_if_inactive(chat_id, stop_event):
    if not stop_event.is_set():
        send_main_menu(chat_id)


@bot.message_handler(commands=['start'])
def start(message):
    send_main_menu(message.chat.id)


def doGrammar(chat_id):
    bot.send_message(chat_id, "Що ви хочете по практикуватись в граматиці?")
    user_state[chat_id] = 'waiting_grammar'


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global user_state

    if call.data == 'words':
        send_word_prompt(call.message.chat.id)
    elif call.data == 'show':
        bot.send_message(call.message.chat.id, "How are you?")  # TODO make words return)))
        reset_state(call.message.chat.id)

    elif call.data == 'grammar':
        doGrammar(call.message.chat.id)

    elif call.data == 'listening':
        bot.send_message(call.message.chat.id, "Good")
        reset_state(call.message.chat.id)

    elif call.data == 'convo':
        bot.send_message(call.message.chat.id, "Fuuuuuuucl")
        reset_state(call.message.chat.id)

    elif call.data == 'continue':
        send_word_prompt(call.message.chat.id)

    elif call.data == 'stop':
        send_main_menu(call.message.chat.id)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    global user_state, gptRes

    chat_id = message.chat.id

    if chat_id in user_state and user_state[chat_id] == 'waiting_grammar':
        bot.send_message(chat_id, 'Почекайте будь ласка')
        gptRes = gptStuff.grammar(message.text.lower())
        user_state[chat_id] = 'grammar_response_wait'
        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        markup.add(
            InlineKeyboardButton("Stop", callback_data='stop')
        )
        bot.send_message(chat_id, gptRes, reply_markup=markup)

    elif chat_id in user_state and user_state[chat_id] == 'grammar_response_wait':
        bot.send_message(chat_id, gptStuff.answerCheck(message.text, gptRes))
        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        markup.add(
            InlineKeyboardButton("Stop", callback_data='stop'),
            InlineKeyboardButton("Продовжити", callback_data='grammar')
        )
        bot.send_message(chat_id, "Хочете продовжити?", reply_markup=markup)


def main():
    bot.polling(none_stop=True)


if __name__ == '__main__':
    main()
