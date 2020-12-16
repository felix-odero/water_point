import json
from collections import defaultdict, OrderedDict
from functools import cmp_to_key
from flask import Flask, Response
import requests

app = Flask(__name__)


def get_data_from_url(url):
    """
    :param url:
    :return:
    """
    request = requests.get(url)
    return request.json()


def load_data_file(filename, from_url=False):
    """
    :param from_url:
    :param filename:
    :return:
    """
    if from_url:
        return get_data_from_url(filename)
    with open(filename, 'r+') as fp:
        water_points = json.load(fp=fp)
    return tuple(water_points)


def extract(water_points, key, value):
    """
    :param water_points:
    :param key:
    :param value:
    :return:
    """
    return tuple(filter(lambda water_point: water_point.get(key, '@') == value, water_points))


def get_broken_percentage(all_water_points: defaultdict, broken_water_points: defaultdict):
    """
    :param all_water_points:
    :param broken_water_points:
    """
    iterator = iter(all_water_points)

    while True:
        current = next(iterator, None)
        if not current:
            break
        broken = broken_water_points[current]
        all_points = all_water_points[current]
        record = {
            'name': current,
            'total': all_points,
            'working': all_points - broken,
            'broken': broken_water_points[current],
            'percentage_broken': round(broken / float(all_points) * 100, 2)
        }
        yield record


def comparer(water_point_a, water_point_b):
    """
    :param water_point_a:
    :param water_point_b:
    :return:
    """
    if water_point_a['percentage_broken'] == water_point_b['percentage_broken']:
        return water_point_a['working'] - water_point_b['working']
    return water_point_a['percentage_broken'] - water_point_b['percentage_broken']


def main(data_file, from_url=False):
    """
    :arg
    """
    water_points = load_data_file(data_file, from_url)
    # print(len(tuple(water_points)))
    functioning = extract(water_points, 'water_functioning', 'yes')
    water_points_per_community = defaultdict(int)
    water_points_broken_per_community = defaultdict(int)
    water_point_iterator = iter(water_points)

    while True:
        current = next(water_point_iterator, None)
        if not current:
            break
        water_points_per_community[current['communities_villages']] += 1
        if current['water_functioning'] == 'no':
            water_points_broken_per_community[current['communities_villages']] += 1
    broken_percentage = get_broken_percentage(water_points_per_community, water_points_broken_per_community)
    broken_percentage = tuple(broken_percentage)
    broken_percentage = sorted(broken_percentage, key=cmp_to_key(comparer))
    result = OrderedDict()
    result['number_functional'] = len(functioning)
    result['number_water_points'] = water_points_per_community
    result['community_ranking'] = list(broken_percentage)
    return result


@app.route('/')
def index():
    """
    :return:
    """
    url = 'https://raw.githubusercontent.com/onaio/ona-tech/master/data/water_points.json'
    filename = 'Dataset.json'
    return Response(json.dumps(main(url, from_url=True)), 200, {'Content-Type': 'application/json'})


if __name__ == '__main__':
    app.run(port=8000, debug=True)
