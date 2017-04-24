from lxml import html
from bs4 import UnicodeDammit
import requests
import json


class Node:
    def __init__(self, name, cat):
        self.name = name
        self.cat = cat  # teacher = 0, room = 1, student = 2
        self.groups = set()


class Group:
    def __init__(self, name):
        self.name = name
        self.lessons = []
        self.teachers = []
        self.rooms = []
        self.students = []


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


def get_id(page_url):
    return page_url[:-4]


def create_group(group_url):
    """
    group_tree = get_tree(group_url)
    group_table = group_tree
    top_string = group_tree.xpath("/html/body/center[2]/table/tr[1]/td/text()")[0]

    a, b = None, None
    for i in range(len(top_string)):
        if top_string[i] == '\x97':
            if a is None:
                a = i + 2
            else:
                b = i - 1
                break
    group_name = top_string[a:b]

    print(group_name)
    """
    return


def create_node(node_url, node_cat):
    node_table = get_tree(node_url).xpath("/html/body/center[2]/table")[0]
    node_name = node_table.xpath("./tr[1]/td/font/b/text()")[0]
    node = Node(node_name, node_cat)
    for group in node_table.xpath(".//a/@href"):
        if group == index_url:
            continue
        create_group(group)
        node.groups.add(get_id(group))
    nodes[get_id(node_url)] = node
    return

current_cat = 0
# create_group("3_it_p_2_1.htm")
for row in get_tree(index_url).xpath("/html/body/center[2]/center/table/tr"):
    if int(row.xpath("count(./td)")) == 1:
        current_cat += 1
        continue

    for link in row.xpath(".//a/@href"):
        create_node(link, current_cat)
