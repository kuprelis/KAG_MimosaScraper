from lxml import html
import requests
import json

# print("Įveskite tvarkaraščių tinklapio adresą:\n")
# rootUrl = input()
rootUrl = "http://www.azuolynas.klaipeda.lm.lt/tvark/tvark_2016-2017_2pusm/index.htm"
page = requests.get(rootUrl)
tree = html.fromstring(page.content)

rowCount = tree.xpath("count(//table//tr)")
for i in range(1, int(rowCount) + 1):
    print(i)

test = tree.xpath("//table/*/tr[147]")
print(test)
# json_data = json.dumps(data)
