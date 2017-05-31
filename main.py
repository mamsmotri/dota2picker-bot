#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dependencies import *


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
        if any(hero_abbr in hero_name for hero_name in hero_abbrs) or (hero_name.find(hero_abbr)):
            return hero_name


def make_list_form_table(table):
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



def make_list_for_set(heroes_list):
    result = []
    for hero in heroes_list:
        result.append(hero[1])
    return result


def format_pick_table_html(allies, enemies):
    table = "<table>    <tr>    <td> goddamit </td>    </tr>    </table>"

    return table


# custom_keyboard = [['top-left', 'top-right'], ['bottom-left', 'bottom-right']]
#
# reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
# bot.send_message(chat_id=chat_id,
#                  text="Custom Keyboard Test",
#                  reply_markup=custom_keyboard)

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
    heroes = make_list_form_table(table)
    heroes.remove([])

    best_heroes = []

    for hero in heroes:
        if float(hero[3].rstrip('%')) > 50:
            hero[1] = re.sub("\d+|[.]", "", hero[1])
            best_heroes.append(hero)

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
    heroes_versus = make_list_form_table(table)
    heroes_versus.remove([])

    worst_heroes_versus = []

    for hero in heroes_versus:
        if float(hero[2].rstrip('%')) < 0:
            hero[1] = re.sub("\d+|[.]", "", hero[1])
            worst_heroes_versus.append(hero)

    worst_heroes_versus.reverse()

    return worst_heroes_versus


def calculate_pick_statistic(allies = [], enemies = []):

    statistic_heroes = set(make_list_for_set(get_worst_heroes_versus(enemies[0])))
    for enemy in enemies:
        worst_heroes_versus[enemy] = make_list_for_set(get_worst_heroes_versus(enemy))
        print (statistic_heroes)
        print (set(worst_heroes_versus[enemy]))

        statistic_heroes = set(worst_heroes_versus[enemy]) & statistic_heroes

        print ('new result:')
        print (statistic_heroes)
        print ("\n")


    return statistic_heroes


def calculate_player_best_variants(statistic_heroes, player_best_heroes):
    return statistic_heroes & set(make_list_for_set(player_best_heroes))

# calculate_pick_statistic([], ['dazzle', 'huskar', 'arc-warden', 'spectre', 'rubick'])


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Let's begin. Send me your nickname.")
    chatStatus[str(message.chat.id)] = 'waiting_for_nickname'
    enemies[str(message.chat.id)] = []
    allies[str(message.chat.id)] = []


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "Dota 2 counter picker based on your winrate and dotabuff statictics. Send /start to start.")


@bot.message_handler(commands=['change_nickname'])
def change_nickname(message):
    bot.send_message(message.chat.id, "Okay. Send me your new nickname.")
    chatStatus[str(message.chat.id)] = 'waiting_for_nickname'
    enemies[str(message.chat.id)] = []
    allies[str(message.chat.id)] = []


@bot.message_handler(commands=['start_pick'])
def start_pick(message):
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
    print (message.chat.id)
    if str(message.chat.id) in chatStatus:
        if chatStatus[str(message.chat.id)] == 'waiting_for_nickname':
            player = get_player_by_name(message.text)
            bot.reply_to(message, "OK. It seems i found you: \n" + player['name'])
            bot.send_photo(message.chat.id, player['pic_src'])
            best_heroes = get_player_best_heroes(player['id'])

            best_heroes_msg = 'Your best heroes are: \n'
            for hero in best_heroes:
                best_heroes_msg += hero[1] + ' (' + hero[3] + ') - ' + hero[2] +' matches\n'
                if len(best_heroes_msg) > 180:
                    break
            bot.send_message(message.chat.id, best_heroes_msg)

            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            markup.add('/change_nickname', '/start_pick')
            bot.send_message(message.chat.id, 'Good! Now we can start pick phase.', reply_markup=markup)

        if chatStatus[str(message.chat.id)] == 'ally_picked':
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            markup.add('/ally', '/enemy')
            current_hero = find_hero(message.text)
            allies[str(message.chat.id)].append(current_hero)
            msg = calculate_pick_statistic(allies, enemies[str(message.chat.id)])


            bot.send_message(message.chat.id, msg , reply_markup=markup)

        if chatStatus[str(message.chat.id)] == 'enemy_picked':
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            markup.add('/ally', '/enemy')
            current_hero = find_hero(message.text)
            enemies[str(message.chat.id)].append(current_hero)

            # table = format_pick_table_html(allies[str(message.chat.id)], enemies[str(message.chat.id)])
            #
            # bot.send_message(message.chat.id, table, parse_mode='HTML')

            msg = "best heroes for this pick will be:" + str(calculate_pick_statistic(allies, enemies[str(message.chat.id)]))

            bot.send_message(message.chat.id, msg, reply_markup=markup)

            msg = "and with you best heroes it can be:" + str(calculate_player_best_variants(calculate_pick_statistic(allies, enemies[str(message.chat.id)]), get_player_best_heroes(133818581)))

            bot.send_message(message.chat.id, msg, reply_markup=markup)


bot.polling()