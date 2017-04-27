from lxml import html
from bs4 import UnicodeDammit
import requests
import json


class Node:
    def __init__(self, name, cat):
        self.name = name
        self.cat = cat  # teacher = 1, room = 2, student = 3
        self.groups = set()


class Group:
    def __init__(self, name):
        self.name = name
        self.times = []
        self.nodes = []  # (day, lesson number)


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Node):
            return {
                "name": obj.name,
                "cat": obj.cat,
                "groups": list(obj.groups)
            }
        if isinstance(obj, Group):
            return {
                "name": obj.name,
                "times": obj.times,
                "nodes": obj.nodes
            }
        return json.JSONEncoder.default(self, obj)


print("Įveskite tvarkaraščių tinklapio index.htm adresą, pvz.: http://www.example.com/*/index.htm\n")
base_url = input().strip()[:-9]
index_url = "index.htm"
groups = {}
nodes = {}


def get_tree(page_url):
    resp = requests.get(base_url + page_url.lower())
    dammit = UnicodeDammit(resp.content, ["windows-1257"])
    tree = html.fromstring(dammit.unicode_markup)
    return tree


def get_id(page_url, is_node):
    if is_node:
        ret = page_url[5:-4]  # ignore "x3001"
    else:
        ret = page_url[:-4]
    return ret.lower()


def create_group(group_url, group_name):
    if get_id(group_url, False) in groups:
        return

    table = get_tree(group_url).xpath("/html/body/center[2]/table")[0]
    group = Group(group_name)

    for node in table.xpath("./tr[2]/td[1]/text()"):
        if len(node) <= 2:
            continue
        node_id = node[:node.index(" ")].lstrip()  # trim invisible chars
        group.nodes.append(str.lower(node_id))

    for time in table.xpath("./tr[2]/td[2]/text()"):
        day = time[2:5]
        if day == "Pir":
            day = 1
        elif day == "Ant":
            day = 2
        elif day == "Tre":
            day = 3
        elif day == "Ket":
            day = 4
        elif day == "Pen":
            day = 5
        else:
            continue

        time = time[6:]
        times = []
        rooms = []

        if time[1] == "-":
            for i in range(int(time[0]), int(time[2]) + 1):
                times.append((day, i))
            time = time[4:]
        else:
            times.append((day, int(time[0])))
            time = time[2:]

        if len(time) > 0 and time[0] == "[":
            time = time[1:-1]
            while True:
                comma = time.find(",")
                if comma != -1:
                    rooms.append(time[:comma].lower())
                    time = time[comma + 1:]
                else:
                    rooms.append(time.lower())
                    break

        if len(rooms) > 0:
            for i in range(len(rooms)):
                group.times.append((times[i], rooms[i]))
        else:
            group.times.extend(times)

    groups[get_id(group_url, False)] = group
    return


def create_node(node_url, node_cat):
    table = get_tree(node_url).xpath("/html/body/center[2]/table")[0]
    name = table.xpath("./tr[1]/td/font/b/text()")[0]
    node = Node(name.rstrip(), node_cat)  # trim spaces on the right

    for group in table.xpath(".//a"):
        url = group.xpath("./@href")[0]
        if url == index_url:
            continue
        name = group.xpath("./text()")[0]
        create_group(url, name)
        node.groups.add(get_id(url, False))

    nodes[get_id(node_url, True)] = node
    return

current_cat = 0
for row in get_tree(index_url).xpath("/html/body/center[2]/center/table/tr"):
    if int(row.xpath("count(./td)")) == 1:
        current_cat += 1
        continue

    for link in row.xpath(".//a/@href"):
        create_node(link, current_cat)


def write(filename, obj):
    with open(filename, "w", encoding="utf-8") as output:
        json.dump(obj, output, cls=CustomEncoder, ensure_ascii=False)
    return

write("groups.json", groups)
write("nodes.json", nodes)
