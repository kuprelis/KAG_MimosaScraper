from lxml import html
from bs4 import UnicodeDammit
import requests
import json


def decode_html(html_string):
    converted = UnicodeDammit(html_string)
    if not converted.unicode_markup:
        raise UnicodeDecodeError(
            "Failed to detect encoding, tried [%s]",
            ', '.join(converted.tried_encodings))
    return converted.unicode_markup

# print("Įveskite tvarkaraščių tinklapio index.htm adresą:\n")
# index_url = input()
base_url = "http://www.azuolynas.klaipeda.lm.lt/tvark/tvark_2016-2017_2pusm/"

page = requests.get(base_url + "index.htm")
tree = html.fromstring(decode_html(page.content))
tree.make_links_absolute(base_url)

# ----------------------------------------------------------------------------------------------------------------------


class Node:
    def __init__(self, name, cat):
        self.name = name
        self.cat = cat  # category
        self.groups = []

    def add_group(self, group_id):
        self.groups.append(group_id)


class Group:
    def __init__(self, week_day, lesson_num, teacher, room):
        self.week_day = week_day
        self.lesson_num = lesson_num
        self.teacher = teacher
        self.room = room
        self.students = []

    def add_student(self, student_id):
        self.students.append(student_id)

groups = {}
nodes = {}


def create_group(group_url):
    return


def create_node(node_url, node_type):
    return


row_count = int(tree.xpath("count(/html/body/center[2]/center/table//tr)"))
current_cat = 0
for i in range(2, row_count + 1):
    if int(tree.xpath("count(" + "/html/body/center[2]/center/table/tr[{}]/td".format(i) + ")")) == 1:
        current_cat += 1
        continue

    for j in range(1, 4):
        url = tree.xpath("/html/body/center[2]/center/table/tr[{}]/td[{}]/a/@href".format(i, j))
        if len(url) > 0:
            create_node(url[0], current_cat)
        else:
            break

# json_data = json.dumps(data)
