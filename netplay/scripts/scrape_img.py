#!/usr/bin/env python3

import time
import csv
import urllib.request

url = 'http://storage.googleapis.com/ygoprodeck.com/pics/'

with open('cards.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in reader:
        card_id = row[0]
        print(row[1])
        urllib.request.urlretrieve(url + card_id + '.jpg', 'img/' + card_id + '.jpg')
        time.sleep(1)
