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

nodes = []
groups = {}


def create_node(link, type):
    print(link, type)


row_count = int(tree.xpath("count(/html/body/center[2]/center/table//tr)"))
node_type = 0
for i in range(2, row_count + 1):
    if int(tree.xpath("count(" + "/html/body/center[2]/center/table/tr[{}]/td".format(i) + ")")) == 1:
        node_type += 1
        continue

    for j in range(1, 4):
        link = tree.xpath("/html/body/center[2]/center/table/tr[{}]/td[{}]/a/@href".format(i, j))
        if len(link) > 0:
            create_node(link[0], node_type)
        else:
            break

# json_data = json.dumps(data)
