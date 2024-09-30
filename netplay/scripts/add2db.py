#!/usr/bin/env python3

import sqlite3

conn = sqlite3.connect('../sql/cards.db')
c = conn.cursor()

card_id = "73915052"
card_name = "Sheep Token"
card_type = "Token"
card_subtype = "Normal"
card_attribute = "Earth"
monster_type = "Beast"
monster_class = ""
monster_level = "1"
monster_atk = "0"
monster_def = "0"
card_text = "This card can be used as any Token."

row = [
    card_id,
    card_name,
    card_type,
    card_subtype,
    card_attribute,
    monster_type,
    monster_class,
    monster_level,
    monster_atk,
    monster_def,
    card_text
]

c.execute('INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?)', row)
conn.commit()
