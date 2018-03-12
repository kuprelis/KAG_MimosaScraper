import sys
import firebase_admin
from lxml import html
from bs4.dammit import UnicodeDammit
import requests
from json import JSONEncoder, JSONDecoder
from firebase_admin import db, credentials


class Node:
    def __init__(self, name, cat):
        self.name = name
        self.cat = cat  # teacher = 1, room = 2, student = 3
        self.groups = set()


class Group:
    def __init__(self, name):
        self.name = name
        self.lessons = []
        self.nodes = []


class Lesson:
    def __init__(self, day, number):
        self.day = day
        self.number = number
        self.room = None


class CustomEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Node):
            return {
                'name': obj.name,
                'cat': obj.cat
            }
        if isinstance(obj, Group):
            return {
                'name': obj.name,
                'lessons': obj.lessons
            }
        if isinstance(obj, Lesson):
            return {
                'day': obj.day,
                'num': obj.number,
                'room': obj.room
            }
        return json.JSONEncoder.default(self, obj)


with open('data/timetable_url.txt') as file:
    base_url = file.read().strip()
pos = base_url.rfind('/') + 1
index_url = base_url[pos:]
base_url = base_url[:pos]
groups = {}
nodes = {}


def get_tree(page_url):
    resp = requests.get(base_url + page_url.lower(), headers={'User-Agent': ''})
    dammit = UnicodeDammit(resp.content, ['windows-1257'])
    tree = html.fromstring(dammit.unicode_markup)
    return tree


def get_id(page_url, is_node):
    ext = page_url.rfind('.')
    if is_node:
        ret = page_url[5:ext]  # ignore 'x3001'
    else:
        ret = page_url[:ext]
    return ret.lower()


def create_group(group_url, group_name):
    if get_id(group_url, False) in groups:
        return

    table = get_tree(group_url).xpath('/html/body/center[2]/table')[0]
    group = Group(group_name)

    for node in table.xpath('./tr[2]/td[1]/text()'):
        node = node.strip()
        if len(node) == 0:
            continue
        node_id = node[:node.find(' ')].replace('-', '_')
        group.nodes.append(node_id.lower())

    for lesson in table.xpath('./tr[2]/td[2]/text()'):
        lesson = lesson.strip()

        day = lesson[:3]
        if day == 'Pir':
            day_id = 1
        elif day == 'Ant':
            day_id = 2
        elif day == 'Tre':
            day_id = 3
        elif day == 'Ket':
            day_id = 4
        elif day == 'Pen':
            day_id = 5
        else:
            continue
        lesson = lesson[4:]

        first = int(lesson[0])
        last = first
        lesson = lesson[1:]
        if len(lesson) > 0 and lesson[0] == '-':
            last = int(lesson[1])
            lesson = lesson[2:]
        lesson = lesson[1:]

        lesson_index = len(group.lessons)
        for i in range(first, last + 1):
            group.lessons.append(Lesson(day_id, i))

        if len(lesson) > 0 and lesson[0] == '[':
            lesson = lesson[1:-1]
            while len(lesson) > 0:
                comma = lesson.find(',')
                if comma != -1:
                    room = lesson[:comma].lower()
                    lesson = lesson[comma + 1:]
                else:
                    room = lesson.lower()
                    lesson = ''
                group.lessons[lesson_index].room = room.replace('-', '_')
                lesson_index += 1

    groups[get_id(group_url, False)] = group
    return


def create_node(node_url, node_cat):
    table = get_tree(node_url).xpath('/html/body/center[2]/table')[0]
    name = table.xpath('./tr[1]/td/font/b/text()')[0]
    node = Node(name.strip(), node_cat)

    for group in table.xpath('.//a'):
        url = group.xpath('./@href')[0]
        if url == index_url:
            continue
        group_name = group.xpath('./text()')[0]
        create_group(url, group_name.strip())
        node.groups.add(get_id(url, False))

    nodes[get_id(node_url, True)] = node
    return


root = get_tree(index_url)
header = root.xpath('/html/body/center[1]/table')[0]
date = header.xpath('./tr[2]/td[2]/text()')[0].strip()
time = header.xpath('./tr[3]/td[2]/text()')[0].strip()
timestamp = date + ' ' + time

cred = credentials.Certificate('data/service_key.json')
app = firebase_admin.initialize_app(cred, {'databaseURL': 'https://kagandroidapp.firebaseio.com/',
                                           'databaseAuthVariableOverride': {'uid': 'scraper'}})

try:
    prod_ver = db.reference('/timestamp').get()
    if timestamp <= prod_ver:
        sys.exit()
except ValueError:
    pass

current_cat = 0
for row in root.xpath('/html/body/center[2]/center/table/tr'):
    if row.xpath('count(./td)') == 1.0:
        current_cat += 1
        continue

    for link in row.xpath('.//a/@href'):
        create_node(link, current_cat)

data = {'nodes': nodes, 'node_groups': {}, 'groups': groups, 'group_nodes': {}, 'timestamp': timestamp}

for key in nodes:
    val = nodes[key]
    node_groups = {}
    for key_g in val.groups:
        node_groups[key_g] = groups[key_g]
    data['node_groups'][key] = node_groups

for key in groups:
    val = groups[key]
    group_nodes = {}
    for key_n in val.nodes:
        group_nodes[key_n] = nodes[key_n]
    data['group_nodes'][key] = group_nodes

data['times'] = [480, 525, 535, 580, 590, 635, 645, 690, 715, 760, 780, 825, 835, 880, 890, 935]

ref = db.reference('/', app)
json = JSONDecoder().decode(CustomEncoder().encode(data))
ref.set(json)
