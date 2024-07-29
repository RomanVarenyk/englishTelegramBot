import random
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from threading import Timer, Event
from dotenv import load_dotenv
import os
import gptStuff
import logging
from datetime import datetime, timedelta
import time

load_dotenv()
telegramKey = os.getenv('telegramKey')
bot = telebot.TeleBot(telegramKey)

user_state = {}
user_timers = {}
user_word = {}
restart_times = []

MAX_RESTARTS = 15
RESTART_WINDOW = timedelta(hours=24)

wordList = []
with open('data/words.txt', 'r', encoding='utf-8') as file:
    for line in file:
        wordList.append(line.strip())

wordDef = {}
for i in wordList:
    sp = i.split(" - ")
    wordDef[sp[0]] = sp[1]

def log_error_and_restart(exception):
    global restart_times
    current_time = datetime.now()

    # Clean up old restart times
    restart_times = [t for t in restart_times if current_time - t < RESTART_WINDOW]

    if len(restart_times) >= MAX_RESTARTS:
        print("Max restarts reached. Exiting.")
        return False

    # Log the error
    log_filename = f"log_{current_time.strftime('%Y-%m-%d_%H-%M-%S')}.txt"
    with open(log_filename, 'w') as log_file:
        log_file.write(f"Error occurred at {current_time}:\n")
        log_file.write(f"{exception}\n")

    # Record the restart time
    restart_times.append(current_time)

    # Restart the bot
    print(f"Restarting bot ({len(restart_times)}/{MAX_RESTARTS})...")
    time.sleep(5)
    main()
    return True

def doGrammarStuff(chat_id):
    wordNum = random.randint(0, len(wordList) - 1)
    cW = wordList[wordNum].split(" - ")
    user_word[chat_id] = cW[0]
    return cW[0]

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
    bot.send_message(chat_id, "Якщо вам треба зі мною зв'язатись, @RomanVarenyk")
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("Слова", callback_data='words'),
        InlineKeyboardButton("Граматика", callback_data='grammar'),
        InlineKeyboardButton("Задайте питання про англійську! (експерементально)", callback_data='convo')
    )
    bot.send_message(chat_id, "Оберіть що ви хочете зробити", reply_markup=markup)
    reset_state(chat_id)
    cancel_timer(chat_id)

def send_word_prompt(chat_id):
    currentWord = doGrammarStuff(chat_id)
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
    timer = Timer(300.0, send_main_menu_if_inactive, [chat_id, stop_event])
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
        reset_timer(call.message.chat.id)

    elif call.data == 'show':
        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        markup.add(
            InlineKeyboardButton("Продовжити", callback_data='words'),
            InlineKeyboardButton("В головне меню", callback_data='stop')
        )
        bot.send_message(call.message.chat.id,
                         f"The definition of the word is: {wordDef.get(user_word.get(call.message.chat.id))}",
                         reply_markup=markup)
        doGrammarStuff(call.message.chat.id)
        reset_timer(call.message.chat.id)
        reset_state(call.message.chat.id)

    elif call.data == 'grammar':
        doGrammar(call.message.chat.id)
        reset_timer(call.message.chat.id)
        user_state[call.message.chat.id] = 'waiting_grammar'

    elif call.data == 'convo':
        bot.send_message(call.message.chat.id, "Яке у вас питання?")
        user_state[call.message.chat.id] = 'await_ai_response'
        reset_timer(call.message.chat.id)

    elif call.data == 'continue':
        send_word_prompt(call.message.chat.id)
        reset_timer(call.message.chat.id)
        user_state[call.message.chat.id] = 'waiting_grammar'

    elif call.data == 'stop':
        send_main_menu(call.message.chat.id)
        reset_timer(call.message.chat.id)
        reset_state(call.message.chat.id)

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
            InlineKeyboardButton("В головне меню", callback_data='stop')
        )
        bot.send_message(chat_id, gptRes, reply_markup=markup)

    elif chat_id in user_state and user_state[chat_id] == 'grammar_response_wait':
        bot.send_message(chat_id, gptStuff.answerCheck(message.text, gptRes))
        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        markup.add(
            InlineKeyboardButton("В головне меню", callback_data='stop'),
            InlineKeyboardButton("Продовжити", callback_data='grammar')
        )
        bot.send_message(chat_id, "Хочете продовжити?", reply_markup=markup)
        user_state[chat_id] = 'waiting_grammar'

    elif chat_id in user_state and user_state[chat_id] == 'await_ai_response':
        bot.send_message(chat_id, 'Почекайте будь ласка')
        bot.send_message(chat_id, gptStuff.askQuestions(message.text))
        send_main_menu(chat_id)
        reset_state(chat_id)

def main():
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        if log_error_and_restart(e):
            return

if __name__ == '__main__':
    main()
