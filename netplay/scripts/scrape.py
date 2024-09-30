#!/usr/bin/env python3

import urllib.parse
import requests
import json
import csv
import time

url = "https://db.ygoprodeck.com/api/v7/cardinfo.php?name="

f = open("card_id.csv", "w")

with open('cards.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    iterreader = iter(reader)
    next(iterreader)
    for row in iterreader:
        card_name = row[0]
        url_card_name = urllib.parse.quote(row[0])
        response = requests.get(url + url_card_name)
        card_id = response.json()["data"][0]["id"]
        f.write(str(card_id) + ", " + str(card_name) + '\n')
        print(str(card_id) + ", " + str(card_name))
        time.sleep(0.1)
        
f.close()

