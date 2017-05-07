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
        self.times = []  # (day, lesson number, room if given)
        self.nodes = []


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
        node_id = node[:node.find(" ")]
        group.nodes.append(node_id.lower())

    for time in table.xpath("./tr[2]/td[2]/text()"):
        time = time.strip()

        day = time[:3]
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
        time = time[4:]

        first = int(time[0])
        last = first
        time = time[1:]
        if len(time) > 0 and time[0] == "-":
            last = int(time[1])
            time = time[2:]
        time = time[1:]

        rooms = []
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

        for i in range(first, last + 1):
            if len(rooms) > 0:
                group.times.append((day_id, i, rooms[i - first]))
            else:
                group.times.append((day_id, i))

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

current_cat = 0
for row in get_tree(index_url).xpath("/html/body/center[2]/center/table/tr"):
    if int(row.xpath("count(./td)")) == 1:
        current_cat += 1
        continue

    for link in row.xpath(".//a/@href"):
        create_node(link, current_cat)


data = {"nodes": nodes, "groups": groups}
with open("data.json", "w", encoding="utf-8") as output:
    json.dump(data, output, cls=CustomEncoder, ensure_ascii=False)
