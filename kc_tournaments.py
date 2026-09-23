import requests
import time
from collections import OrderedDict
import cachetools
import pickle

try:
    with open('mycache.pickle', 'rb') as f:
        cache = pickle.load(f)
except FileNotFoundError:
    cache = {} # or cachetools.LRUCache(maxsize=5) or whatever you want

api_key = ''
year = 2026
radius = 75
max_results = 20
startDate = time.strptime(f'{year}-01-01', '%Y-%m-%d')

def get_tournaments():
    url = f'https://api.ifpapinball.com/tournament/search?start_date={year - 1}-10-01&end_date={year}-12-31&rank_type=MAIN&total=200&only_with_results=Y&latitude=39.099724&longitude=-94.578331&radius={radius}&distance_unit=m%20for%20Miles&api_key={api_key}'
    response = requests.get(url)
    return response

@cachetools.cached(cache)
def get_tournament_results(id):
    url = f'https://api.ifpapinball.com/tournament/{id}/results?api_key={api_key}'
    response = requests.get(url)
    return response

response = get_tournaments()

if (response.ok):
    json = response.json()
    players = {}
    for tournament in json['tournaments']:
        if time.strptime(tournament['event_end_date'], '%Y-%m-%d') < startDate:
            continue;
        id = tournament['tournament_id']
        tournament_name = tournament['tournament_name']

        resultsResponse = get_tournament_results(id)
        if (resultsResponse.ok):
            results = resultsResponse.json()
            if 'results' not in results:
                print(f'No results for {tournament_name}')
                continue
            # print(f'Got results for {tournament_name}')
            for result in results['results']:
                player_id = result['player_id']
                if player_id not in players:
                    players[player_id] = {'name': result['name'], 'points': []}
                players[player_id]['points'].append(float(result['points']))
        else:
            print(f'Failed to get results for {tournament_name}')
    for k, v in players.items():
        v['points'].sort(reverse=True)
        v['counted'] = len(v['points'][:max_results])
        v['total'] = sum(v['points'][:max_results])

    ordered = OrderedDict(sorted(players.items(), reverse=True, key=lambda item: item[1]['total']))
    print('KC Results:')
    print(f'Number of tournaments: {json['total_results']}')
    print(f'Number of unique players: {len(players)}')
    print(f'{'Rank':<5}{'Player':25}{'Events':>8}{'Points':>10}    (Total Events - Total Points)')
    i = 1
    for k, v in ordered.items():
        print(f'{i:<5}{v['name']:25}{v['counted']:8}{round(v['total'],2):10}    ({len(v['points'])} - {round(sum(v['points']), 2)})')
        i += 1
        if i > 100:
            break

with open('mycache.pickle', 'wb') as f:
    pickle.dump(cache, f)
