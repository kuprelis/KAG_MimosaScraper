from lxml import html
import requests
import json

# print("Įveskite tvarkaraščių tinklapio adresą:\n")
# rootUrl = input()

baseUrl = "http://www.azuolynas.klaipeda.lm.lt/tvark/tvark_2016-2017_2pusm/"

page = requests.get(baseUrl + "index.htm")

tree = html.fromstring(page.content)
tree.make_links_absolute(baseUrl)

table = tree.xpath("/html/body/center[2]/center/table")[0]

# html.open_in_browser(table)

# json_data = json.dumps(data)
