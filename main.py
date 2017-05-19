from lxml import html
from bs4 import UnicodeDammit
import requests
import json
from queue import Queue
from threading import Thread


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


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Node):
            return {
                "name": obj.name,
                "category": obj.cat,
                "groups": list(obj.groups)
            }
        if isinstance(obj, Group):
            return {
                "name": obj.name,
                "lessons": obj.lessons,
                "nodes": obj.nodes
            }
        if isinstance(obj, Lesson):
            return {
                "day": obj.day,
                "number": obj.number,
                "room": obj.room
            }
        return json.JSONEncoder.default(self, obj)


print("Įveskite tvarkaraščių tinklapio index.htm adresą, pvz.: http://www.example.com/*/index.htm\n")
base_url = input().strip()
pos = base_url.rfind("/") + 1
index_url = base_url[pos:]
base_url = base_url[:pos]
groups = {}
nodes = {}


def get_tree(page_url):
    resp = requests.get(base_url + page_url.lower())
    dammit = UnicodeDammit(resp.content, ["windows-1257"])
    tree = html.fromstring(dammit.unicode_markup)
    return tree


def get_id(page_url, is_node):
    ext = page_url.rfind(".")
    if is_node:
        ret = page_url[5:ext]  # ignore "x3001"
    else:
        ret = page_url[:ext]
    return ret.lower()


def create_group(group_url, group_name):
    if get_id(group_url, False) in groups:
        return

    table = get_tree(group_url).xpath("/html/body/center[2]/table")[0]
    group = Group(group_name)

    for node in table.xpath("./tr[2]/td[1]/text()"):
        node = node.strip()
        if len(node) == 0:
            continue
        node_id = node[:node.find(" ")].replace("-", "_")
        group.nodes.append(node_id.lower())

    for lesson in table.xpath("./tr[2]/td[2]/text()"):
        lesson = lesson.strip()

        day = lesson[:3]
        if day == "Pir":
            day_id = 1
        elif day == "Ant":
            day_id = 2
        elif day == "Tre":
            day_id = 3
        elif day == "Ket":
            day_id = 4
        elif day == "Pen":
            day_id = 5
        else:
            continue
        lesson = lesson[4:]

        first = int(lesson[0])
        last = first
        lesson = lesson[1:]
        if len(lesson) > 0 and lesson[0] == "-":
            last = int(lesson[1])
            lesson = lesson[2:]
        lesson = lesson[1:]

        lesson_index = len(group.lessons)
        for i in range(first, last + 1):
            group.lessons.append(Lesson(day_id, i))

        if len(lesson) > 0 and lesson[0] == "[":
            lesson = lesson[1:-1]
            while len(lesson) > 0:
                comma = lesson.find(",")
                if comma != -1:
                    room = lesson[:comma].lower()
                    lesson = lesson[comma + 1:]
                else:
                    room = lesson.lower()
                    lesson = ""
                group.lessons[lesson_index].room = room.replace("-", "_")
                lesson_index += 1

    groups[get_id(group_url, False)] = group
    return


def create_node(node_url, node_cat):
    table = get_tree(node_url).xpath("/html/body/center[2]/table")[0]
    name = table.xpath("./tr[1]/td/font/b/text()")[0]
    node = Node(name.strip(), node_cat)

    for group in table.xpath(".//a"):
        url = group.xpath("./@href")[0]
        if url == index_url:
            continue
        group_name = group.xpath("./text()")[0]
        create_group(url, group_name.strip())
        node.groups.add(get_id(url, False))

    nodes[get_id(node_url, True)] = node
    return


def get_times(q):
    print("Kiek minučių trunka pamoka?")
    duration = int(input())
    print("Įveskite pamokų pradžios laikus (formatu HH MM)")
    times = []
    for i in range(1, 9):
        print("{}:".format(i), end=" ")
        time = input().strip()
        space = time.find(" ")
        minutes = int(time[:space]) * 60 + int(time[space:])
        times.append(minutes)
        times.append(minutes + duration)
    q.put(times)
    print("Palaukite, kol bus parsiųsti tvarkaraščiai")
    return

queue = Queue()
thread = Thread(target=get_times, args=[queue])
thread.daemon = True
thread.start()

current_cat = 0
for row in get_tree(index_url).xpath("/html/body/center[2]/center/table/tr"):
    if int(row.xpath("count(./td)")) == 1:
        current_cat += 1
        continue

    for link in row.xpath(".//a/@href"):
        create_node(link, current_cat)

data = {"times": queue.get(), "nodes": nodes, "groups": groups}
with open("data.json", "w", encoding="utf-8") as output:
    json.dump(data, output, cls=CustomEncoder, ensure_ascii=False)
print("Baigta")
