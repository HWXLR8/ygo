#!/usr/bin/env python3

import csv
import sqlite3

conn = sqlite3.connect('cards.db')
c = conn.cursor()

with open('cards.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in reader:
        print(row)
        c.execute('INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?)', row)
        print(row[1])
        card_id = row[0]
        card_name = row[1]
        card_type = row[2]
        card_subtype = row[3]
        card_attribute = row[4]
        monster_type = row[5]
        monster_class = row[6]
        monster_level = row[7]
        monster_atk = row[8]
        monster_def = row[9]
        card_text = row[10]
conn.commit()

