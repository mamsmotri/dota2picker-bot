#!/usr/bin/env python
# -*- coding: utf-8 -*-
import config
import telebot
from telebot import types

bot = telebot.TeleBot(config.token)

@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('😊 ally', '😡 enemy') #Имена кнопок
    msg = bot.reply_to(message, 'Test text', reply_markup=markup)
    bot.register_next_step_handler(msg, process_step)

allies = []
enemies = []


def process_step(message):
    chat_id = message.chat.id
    if message.text=='😊 ally':
        allies.add()
    else:
        enemies.add()

bot.polling()