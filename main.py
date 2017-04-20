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


# print("Įveskite tvarkaraščių tinklapio index.htm adresą:\n")
# index_url = input()
base_url = "http://www.azuolynas.klaipeda.lm.lt/tvark/tvark_2016-2017_2pusm/"
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
    page = requests.get(page_url)
    tree = html.fromstring(decode_html(page.content))
    tree.make_links_absolute(base_url)
    return tree


def get_id(page_url):
    for i in range(-5, -len(page_url), -1):
        if page_url[i] == '/':
            return page_url[i + 1:-4]


def create_group(group_url):
    return


def create_node(node_url, node_cat):
    node_tree = get_tree(node_url)
    node_name = node_tree.xpath("/html/body/center[2]/table/tr[1]/td/font/b/text()")[0]
    node = Node(node_name, node_cat)
    links = node_tree.xpath("//a/@href")
    for i in range(1, len(links) - 1):
        create_group(links[i])
        node.groups.add(get_id(links[i]))
    nodes[get_id(node_url)] = node
    return


index_tree = get_tree(base_url + "index.htm")
row_count = int(index_tree.xpath("count(/html/body/center[2]/center/table//tr)"))
current_cat = 0

for i in range(2, row_count + 1):
    if int(index_tree.xpath("count(" + "/html/body/center[2]/center/table/tr[{}]/td".format(i) + ")")) == 1:
        current_cat += 1
        continue

    for j in range(1, 4):
        url = index_tree.xpath("/html/body/center[2]/center/table/tr[{}]/td[{}]/a/@href".format(i, j))
        if len(url) > 0:
            create_node(url[0], current_cat)
        else:
            break
