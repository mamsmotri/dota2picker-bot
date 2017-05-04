import urllib2
from BeautifulSoup import BeautifulSoup
from pprint import pprint as pp
import time
import json
import string

HID = 0
PLAYS = 2
WR = 3
KDA = 4

CACHE_BEST_HEROES_FILENAME = "cache_best_heroes.json"
CACHE_LATEST_MATCH_FILENAME = "cache_latest_game"

STARTING_MATCH_ID = 1163835940

SECONDS_PER_DAY = 86400.0
MAX_FILE_AGE = int(SECONDS_PER_DAY)

heropageurl = "http://www.dotabuff.com/players/{}/heroes"
personbaseurl = "http://www.dotabuff.com/players/{}"
matchbaseurl = "http://www.dotabuff.com/matches/{}"

#@TODO move these into a config file
people = { 'mike': 136754293,
"woody": 30075956,
"stu": 78479931,
"jon": 65091923,
"matt": 119518678,
"brian": 107023417,
"133818581": 133818581,
"andy": 84388592}

def get_heroes_list(name):
    soup = get_soup_from_url(generate_url_for(heropageurl, name))
    herosoup = soup.table.contents[1]
    heroes = {}
    for hero in herosoup:
        name = hero.contents[HID].img['title']
        matches = int(hero.contents[PLAYS].contents[0])
        wr = float(hero.contents[WR].contents[0][:-1]) / 100.0
        kda = float(hero.contents[KDA].contents[0])
        heroes[name] = {"matches": matches, "wr": wr, "kda": kda}
    return heroes

def get_soup_from_url(url):
    print (url)
    f = urllib2.urlopen(url, timeout=1)
    soup = BeautifulSoup(f.read())
    return soup


def get_recent_match_ids(name, starting_id):
    soup = get_soup_from_url(generate_url_for(personbaseurl, name))
    matches = soup.findAll("article")[1].findAll('tr')
    newmatches = []
    for match in matches[1:]:
        matchid = int(match.findAll('a')[1]['href'][9:])
        if matchid > starting_id:
            newmatches.append(matchid)
    return newmatches

def get_match_results(matchid):
    soup = get_soup_from_url(matchbaseurl.format(matchid))
    winningteam = get_winning_team_from_soup(soup)
    matchduration = get_match_duration_from_soup(soup)
    gamemode = get_game_mode(soup)
    skillbracket = get_skill_bracket(soup)
    lobbytype = get_lobby_type(soup)
    radiant_results = get_faction_results(soup, 'radiant')
    print(winningteam, matchduration, gamemode, skillbracket, lobbytype)
    pp(radiant_results)
    dire_results = get_faction_results(soup, 'dire')
    pp(dire_results)
    results = {}
    results['general'] = [winningteam, matchduration, gamemode, skillbracket, lobbytype]
    results['radiant'] = radiant_results
    results['dire'] = dire_results
    return results

def get_faction_results(soup, faction):

    herorows = soup.findAll('tr', {'class': ' faction-' + faction} )
    result = []
    for row in herorows:
        summ_stub = "{name}: {hero}{tabs} lvl:{lvl} kda:{k}/{d}/{a} lh:{lh} xpm:{xpm} gpm:{gpm}"
        tds = row.findAll('td')
        hero = tds[0].div.a['href'][8:]
        name = tds[1]
        if name.contents[0] != "Anonymous":
            name = name.a.contents[0]
        else:
            name = "Anonymous"
        name = filter(lambda x: x in string.printable, name)
        lvl = tds[3].contents[0]
        k = tds[4].contents[0]
        d = tds[5].contents[0]
        a = tds[6].contents[0]
        gold = tds[7].contents[0]
        lh = tds[8].contents[0]
        dn = tds[9].contents[0]
        xpm = tds[10].contents[0]
        gpm = tds[11].contents[0]
        hd = tds[12].contents[0]
        hh = tds[13].contents[0]
        td = tds[14].contents[0]
        ntabs = 1
        if len(hero) < 14:
            ntabs = 2
        if len(hero) < 9:
            ntabs = 3
        tabs = '\t' * ntabs
        result.append(summ_stub.format(name=name, hero=hero, tabs=tabs, lvl=lvl, k=k, d=d, a=a, lh=lh, xpm=xpm, gpm=gpm))
    return result

def get_skill_bracket(soup):
    result = soup.findAll('div', {"id": "content-header-secondary"})[0].findAll('dd')[0].contents[0]
    return result


def get_lobby_type(soup):
    result = soup.findAll('div', {"id": "content-header-secondary"})[0].findAll('dd')[1].contents[0]
    return result


def get_game_mode(soup):
    result = soup.findAll('div', {"id": "content-header-secondary"})[0].findAll('dd')[2].contents[0]
    return result


def get_match_duration_from_soup(soup):
    result = soup.findAll('div', {"id": "content-header-secondary"})[0].findAll('dd')[4].contents[0]
    return result


def get_winning_team_from_soup(soup):
    try:
        result = soup.findAll('div', {"class": "match-result team dire"})[0].contents[0]
        return result
    except Exception:
        result = soup.findAll('div', {"class": "match-result team radiant"})[0].contents[0]
        return result


def generate_url_for(stub, person):
    return stub.format(people[person])

def cache_data(people):
    now = time.time()
    data = {}
    data['time'] = int(now)
    data['stats'] = people
    strdata = json.dumps(data, indent=2)
    with open(CACHE_BEST_HEROES_FILENAME, 'w') as f:
        f.write(strdata)

def load_cached_data():
    data = None
    with open(CACHE_BEST_HEROES_FILENAME, 'r') as f:
        data = json.load(f)
    return data

def get_data():
    try:
        data = load_cached_data()
        now = time.time()
        age = now - data['time']
        if age < MAX_FILE_AGE:
            age_in_hours = int((age / SECONDS_PER_DAY) * 24.0)
            print("==== [Using cached data {} hours old] ====".format(age_in_hours))
            return data['stats']
    except Exception:
        pass
    print("==== [Scraping new data] ====")
    data = scrape_new_data()
    cache_data(data)
    return data

def scrape_new_data():
    data = dict()
    for person in people:
        heroes = get_heroes_list(person)
        data[person] = heroes
    return data

def find_person_best_at_most_heroes(data, threshold = 0.0, wrthresh = 0.0):
    heronames = []

    # collect all the active hero names
    for person in data:
        for hero in data[person]:
            if hero not in heronames:
                heronames.append(hero)

    bestatheros = dict()

    # find best at each hero
    for hero in heronames:
        # initialize to unknown
        bestatheros[hero] = ['unknown', -1.0]

        # iterate over each person
        for person in people:
            # if this person has played
            if hero in data[person]:
                wr = data[person][hero]['wr']
                matches = data[person][hero]['matches']
                if wr > bestatheros[hero][1] and wr > 0:
                    if matches > threshold and wr > wrthresh:
                        bestatheros[hero] = [person, wr]
    number_of_best = dict()
    for person in people:
        number_of_best[person] = 0
    number_of_best['unknown'] = 0
    for hero in bestatheros:
        number_of_best[bestatheros[hero][0]] += 1
    best = 'unknown'
    number_of_best['unknown'] = 0
    for person in people:
        if number_of_best[person] > number_of_best[best]:
            best = person
    dupes = []
    dupes.append(best)
    for person in people:
        if person != best:
            if number_of_best[person] == number_of_best[best]:
                dupes.append(person)
    if len(dupes) == 1:
        return (best, number_of_best[best])
    else:
        return (dupes, number_of_best[best])

# weighted average of KDA aggregate per player
def get_best_kdas(data):
    kdas = dict()
    for person in people:
        summatches = 0
        sumkda = 0
        for hero in data[person]:
            kda = data[person][hero]['kda']
            matches = data[person][hero]['matches']
            sumkda += kda * matches
            summatches += matches
        kdas[person] = sumkda / summatches
    return kdas



def cache_latest_match(latest):
    with open(CACHE_LATEST_MATCH_FILENAME, 'w') as f:
        f.write(str(latest))

def load_latest_match():
    with open(CACHE_LATEST_MATCH_FILENAME, 'r') as f:
        matchstr = f.readline()
        return int(matchstr)

def get_new_matches():
    newmatches = []
    starting_id = load_latest_match()
    for person in people:
        personmatches = get_recent_match_ids(person, starting_id)
        for match in personmatches:
            if match not in newmatches:
                newmatches.append(match)
    if newmatches:
        latest = max(newmatches)
        cache_latest_match(latest)
    return newmatches

def update_latest_matches():
    print("---updating recent matches---")

    newmatches = get_new_matches()
    if newmatches:
        for match in newmatches:
            get_match_results(match)
    else:
        print("no new matches")

#@TODO Actually do analytics
if __name__ == "__main__":
    update_latest_matches()
    """
    data = get_data()
    for i in range(1, 120):
        best = find_person_best_at_most_heroes(data, i, 0.5)
        if best is not None:
            print("at minimum of {} matches, person best at most heroes is {} with {}".format(i, best[0], best[1]))
    """
    #pp(get_best_kdas(data))