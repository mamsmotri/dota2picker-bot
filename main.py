#!/usr/bin/env python
# -*- coding: utf-8 -*-
import config
import telebot
from telebot import types
import requests
from bs4 import BeautifulSoup
import re
from lxml import html


bot = telebot.TeleBot(config.token)
chatStatus = {}


def makelist(table):
  result = []
  allrows = table.findAll('tr')
  for row in allrows:
    result.append([])
    allcols = row.findAll('td')
    for col in allcols:
      thestrings = [unicode(s) for s in col.findAll(text=True)]
      thetext = ''.join(thestrings)
      result[-1].append(thetext)
  return result

def get_player_by_name(player_name):

    url = 'http://www.dotabuff.com/search?utf8=%E2%9C%93&q=' + player_name + '&commit=Search'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    }
    r = requests.get(url, headers=headers)
    result_page = r.text

    parsed_page = BeautifulSoup(result_page, 'html.parser')

    player_id = parsed_page.find('div', {'class': 'result-player'}).find('div', {'class': 'inner'}).get('data-player-id')
    player_name = parsed_page.find('div', {'class': 'result-player'}).get('data-filter-value')
    player_pic_src = parsed_page.find('div', {'class': 'result-player'}).find('img').get('src')
    player = {
        'id': player_id,
        'name': player_name,
        'pic_src': player_pic_src
    }

    return player

def get_best_heroes(player_id):
    url = 'https://ru.dotabuff.com/players/' + str(player_id) + '/heroes'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    }
    r = requests.get(url, headers=headers)
    result_page = r.text

    parsed_page = BeautifulSoup(result_page, 'html.parser')

    table = parsed_page.find('table', {'class': 'sortable'})
    heroes = makelist(table)
    heroes.remove([])

    best_heroes = []

    for hero in heroes:
        if float(hero[3].rstrip('%')) > 50:
            hero[1] = re.sub("\d+|[.]", "", hero[1])
            best_heroes.append(hero)
        if len(best_heroes) == 3:
            break

    return best_heroes


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Let's begin. Send me your nickname.")
    chatStatus[str(message.chat.id)] = 'waitingForNickname'

@bot.message_handler(commands=['pick_starts'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('😊 ally', '😡 enemy') #Имена кнопок
    msg = bot.reply_to(message, 'Test text', reply_markup=markup)
    bot.register_next_step_handler(msg, process_step)

@bot.message_handler()
def ask_nickname(message):
    if str(message.chat.id) in chatStatus:
        if chatStatus[str(message.chat.id)] == 'waitingForNickname':
            player = get_player_by_name(message.text)
            bot.reply_to(message, "OK. It seems i found you: \n" + player['name'])
            bot.send_photo(message.chat.id, player['pic_src'])
            best_heroes = get_best_heroes(player['id'])

            best_heroes_msg = 'Your best heroes are: \n'
            for hero in best_heroes:
                best_heroes_msg += hero[1] + ' (' + hero[3] + ') \n'
            bot.send_message(message.chat.id, best_heroes_msg)
            bot.send_message(message.chat.id, 'To start pick send /pick_starts')
            # chatStatus[str(message.chat.id)] = 'gotNickname'



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