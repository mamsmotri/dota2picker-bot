#!/usr/bin/env python
# -*- coding: utf-8 -*-
import config
import telebot
from telebot import types
import requests
from bs4 import BeautifulSoup
import re
import json
from pprint import pprint
from lxml import html


bot = telebot.TeleBot(config.token)
chatStatus = {}
enemies = {}
allies = {}
worst_heroes_versus = {}
best_heroes_against = {}

with open('heroes.json') as data_file:
    heroes = json.load(data_file)


def find_hero(hero_abbr):
    hero_abbr = hero_abbr.lower()
    for hero_name, hero_abbrs in heroes.items():
        if any(hero_abbr in hero_name for hero_name in hero_abbrs) or (hero_abbr == hero_name):
            return hero_name


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


def get_player_best_heroes(player_id):
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


def get_worst_heroes_versus(hero_name):
    url = 'https://www.dotabuff.com/heroes/' + str(hero_name) + '/matchups'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    }
    r = requests.get(url, headers=headers)
    result_page = r.text

    parsed_page = BeautifulSoup(result_page, 'html.parser')

    table = parsed_page.find('table', {'class': 'sortable'})
    heroes_versus = makelist(table)
    heroes_versus.remove([])

    worst_heroes_versus = []

    for hero in heroes_versus:
        if float(hero[2].rstrip('%')) < 0:
            hero[1] = re.sub("\d+|[.]", "", hero[1])
            worst_heroes_versus.append(hero)

    worst_heroes_versus.reverse()

    return worst_heroes_versus


def calculate_pick(allies = [], enemies = []):
    result = get_worst_heroes_versus(enemies[0])
    for enemy in enemies:
        worst_heroes_versus[enemy] = get_worst_heroes_versus(enemy)
        result = set(worst_heroes_versus[enemy]) and set(result)
        print result

    return result[0][1]

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Let's begin. Send me your nickname.")
    chatStatus[str(message.chat.id)] = 'waiting_for_nickname'
    enemies[str(message.chat.id)] = []
    allies[str(message.chat.id)] = []


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "Dota 2 counter picker based on your winrate and dotabuff statictics. Send /start to start.")


@bot.message_handler(commands=['pick_starts'])
def pick_starts(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('/ally', '/enemy')
    bot.reply_to(message, 'Who has already picked?', reply_markup=markup)


@bot.message_handler(commands=['enemy'])
def enemy_picked(message):
    bot.reply_to(message, 'What hero?')
    chatStatus[str(message.chat.id)] = 'enemy_picked'


@bot.message_handler(commands=['ally'])
def ally_picked(message):
    bot.reply_to(message, 'What hero?')
    chatStatus[str(message.chat.id)] = 'ally_picked'


@bot.message_handler()
def ask_nickname(message):
    if str(message.chat.id) in chatStatus:
        if chatStatus[str(message.chat.id)] == 'waiting_for_nickname':
            player = get_player_by_name(message.text)
            bot.reply_to(message, "OK. It seems i found you: \n" + player['name'])
            bot.send_photo(message.chat.id, player['pic_src'])
            best_heroes = get_player_best_heroes(player['id'])

            best_heroes_msg = 'Your best heroes are: \n'
            for hero in best_heroes:
                best_heroes_msg += hero[1] + ' (' + hero[3] + ') - ' + hero[2] +' matches\n'
            bot.send_message(message.chat.id, best_heroes_msg)
            bot.send_message(message.chat.id, 'To start pick send /pick_starts')

        if chatStatus[str(message.chat.id)] == 'ally_picked':
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            markup.add('/ally', '/enemy')
            current_hero = find_hero(message.text)
            allies[str(message.chat.id)].append(current_hero)
            msg = calculate_pick(allies, enemies[str(message.chat.id)])
            bot.send_message(message.chat.id, msg , reply_markup=markup)

        if chatStatus[str(message.chat.id)] == 'enemy_picked':
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            markup.add('/ally', '/enemy')
            current_hero = find_hero(message.text)
            enemies[str(message.chat.id)].append(current_hero)
            msg = calculate_pick(allies, enemies[str(message.chat.id)])
            bot.send_message(message.chat.id, msg, reply_markup=markup)


bot.polling()