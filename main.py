import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from threading import Timer, Event

bot = telebot.TeleBot('7318218701:AAEXYGbFXbgg-EsG6RJOGEo-W8X4Cc3dl4k')

user_state = {}
user_timers = {}


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
        InlineKeyboardButton("Practice words", callback_data='practice_words'),
        InlineKeyboardButton("Practice grammar", callback_data='practice_grammar'),
        InlineKeyboardButton("Practice listening", callback_data='practice_listening'),
        InlineKeyboardButton("Practice conversation (experimental)", callback_data='practice_conversation')
    )
    bot.send_message(chat_id, "Pick one", reply_markup=markup)
    reset_state(chat_id)
    cancel_timer(chat_id)


def send_word_prompt(chat_id):
    bot.send_message(chat_id, "Please type a word")
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


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global user_state

    if call.data == 'practice_words':
        send_word_prompt(call.message.chat.id)

    elif call.data == 'practice_grammar':
        bot.send_message(call.message.chat.id, "How are you?")
        reset_state(call.message.chat.id)

    elif call.data == 'practice_listening':
        bot.send_message(call.message.chat.id, "Good")
        reset_state(call.message.chat.id)

    elif call.data == 'practice_conversation':
        bot.send_message(call.message.chat.id, "Fuuuuuuucl")
        reset_state(call.message.chat.id)

    elif call.data == 'continue':
        send_word_prompt(call.message.chat.id)

    elif call.data == 'stop':
        send_main_menu(call.message.chat.id)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    global user_state

    chat_id = message.chat.id
    if chat_id in user_state and user_state[chat_id] == 'waiting_for_word':
        if message.text.lower() == "weee":
            bot.send_message(chat_id, "Correct!")
            markup = InlineKeyboardMarkup()
            markup.row_width = 1
            markup.add(
                InlineKeyboardButton("Continue", callback_data='continue'),
                InlineKeyboardButton("Stop", callback_data='stop')
            )
            bot.send_message(chat_id, "Woo!", reply_markup=markup)
        else:
            bot.send_message(chat_id, "Incorrect, try again.")
            reset_timer(chat_id)


def main():
    bot.polling(none_stop=True)


if __name__ == '__main__':
    main()
