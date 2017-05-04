#!/usr/bin/env python
# -*- coding: utf-8 -*-
import config
import telebot
from telebot import types
import dotabuff
import urllib2


bot = telebot.TeleBot(config.token)
chatStatus = {}


def get_player_id_by_name(player_name):
    hdr = {'User-Agent': 'super happy flair bot by /u/spladug'}
    # req = urllib2.Request(url, headers=hdr)
    # html = urllib2.urlopen(req).read()
    print ('http://www.dotabuff.com/search?utf8=%E2%9C%93&q=' + player_name + '&commit=Search')
    response = urllib2.urlopen('http://www.dotabuff.com/search?utf8=%E2%9C%93&q=' + player_name + '&commit=Search', headers=hdr)
    result_page = response.read()
    print result_page


def get_best_heroes(player_id):
    print (player_id)


@bot.message_handler(commands=['start'])
def send_help(message):
    bot.send_message(message.chat.id, "Let's begin. Send me your nickname.")
    chatStatus[message.chat.id] = 'waitingForNickname'

@bot.message_handler()
def send_help(message):
    # print (chatStatus[118096950])
    if chatStatus[message.chat.id] == 'waitingForNickname':
        player_heroes = get_player_id_by_name(message.text)
        # print (dotabuff.get_heroes_list(message.text))
        bot.reply_to(message, "OK. It seems you excelled on:" + playerHeroes)




@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('😊 ally', '😡 enemy') #Имена кнопок
    msg = bot.reply_to(message, 'Test text', reply_markup=markup)
    bot.register_next_step_handler(msg, process_step)

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "Dota 2 counter picker based on your winrate and dotabuff statictics")



allies = []
enemies = []


def process_step(message):
    chat_id = message.chat.id
    if message.text=='😊 ally':
        allies.add()
    else:
        enemies.add()

bot.polling()