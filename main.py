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


class CustomEncoder(json.JSONEncoder):  # TODO fix this
    def default(self, obj):
        if isinstance(obj, Node):
            return obj.name
        elif isinstance(obj, Group):
            return obj.name
        return json.JSONEncoder.default(self, obj)


# print("Įveskite tvarkaraščių tinklapio index.htm adresą (pvz. http://www.example.com/*/index.htm)\n")
# base_url = input()[:-9]
base_url = "http://www.azuolynas.klaipeda.lm.lt/tvark/tvark_2016-2017_2pusm/"
index_url = "index.htm"
groups = {}
nodes = {}


def decode_html(html_string):
    converted = UnicodeDammit(html_string)
    if not converted.unicode_markup:
        raise UnicodeDecodeError(
            "Failed to detect encoding, tried [%s]",
            ', '.join(converted.tried_encodings))
    return converted.unicode_markup


def get_tree(page_url):
    page = requests.get(base_url + page_url)
    tree = html.fromstring(decode_html(page.content))
    return tree


def get_id(page_url, is_node):
    if is_node:
        return page_url[5:-4]
    return page_url[:-4]


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

    # TODO get room node from time
    for time in table.xpath("./tr[2]/td[2]/text()"):
        time = time[2:]
        day = time[:3]

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

        if time[5] == "-":
            for i in range(int(time[4]), int(time[6]) + 1):
                group.times.append((day, i))
        else:
            group.times.append((day, int(time[4])))

    groups[get_id(group_url, False)] = group
    return


def create_node(node_url, node_cat):
    # TODO check result code
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
# create_group("3_lie_jov_1_45.htm", "tst")

for row in get_tree(index_url).xpath("/html/body/center[2]/center/table/tr"):
    if int(row.xpath("count(./td)")) == 1:
        current_cat += 1
        continue

    for link in row.xpath(".//a/@href"):
        create_node(link, current_cat)

with open("groups.json", "w") as output:
    json.dump(groups, output, cls=CustomEncoder)

with open("nodes.json", "w") as output:
    json.dump(nodes, output, cls=CustomEncoder)
