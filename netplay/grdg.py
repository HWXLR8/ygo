#!/usr/bin/env python3

import random
import sqlite3
import os


def card_table_from_resultset(resultset):
    cards = []
    for row in resultset:
        card = {
            "passcode": row[0],
            "card_name": row[1],
            "card_type": row[2],
            "card_subtype": row[3],
            "card_attribute": row[4],
            "monster_type": row[5],
            "monster_class": row[6],
            "monster_level": row[7],
            "monster_atk": row[8],
            "monster_def": row[9],
            "card_text": row[10],
        }
        cards.append(card)
    return cards


def execute_query(query, arguments, conn):
    cursor = conn.cursor()
    cursor.execute(query, tuple(arguments))
    conn.commit()
    result = [item for item in cursor.fetchall()]
    return result


def cards_by_name(name, conn):
    query = "SELECT * FROM cards WHERE card_name like ?"
    args = [name.upper() + "%"]
    resultset = execute_query(query, args, conn)
    card_table = card_table_from_resultset(resultset)
    return card_table


def nrand_goat_deck_cards_by_type(cardtype, n, conn):
    query = "SELECT * FROM cards where card_type=? and card_subtype!='Fusion' ORDER BY RANDOM() LIMIT ?;"
    args = [cardtype, n]
    resultset = execute_query(query, args, conn)
    card_table = card_table_from_resultset(resultset)
    return card_table


def getFiller(type, num_cards):
    cards = nrand_goat_deck_cards_by_type(type, num_cards, conn)
    cards = [card["passcode"] for card in cards]
    return cards


def one_each_tier(card_pool):
    cards = []
    for tier, tier_pool in card_pool.items():
        for card in random.sample(tier_pool, 1):
            cards.append(card)
    return cards


def by_total_strength(card_pool, total_strength):
    card_pool = [*card_pool]
    random.shuffle(card_pool)

    current_strength = 0
    i = 0

    while total_strength > current_strength and i < len(card_pool):
        current_strength += card_pool[i]["strength"]
        i += 1

    return card_pool[0 : (i + 1)]


t1s = [
    "pot of gree",
    "graceful charit",
    "delinquent duo",
]

t2s = [
    "heavy storm",
    "mystical space",
    "premature bu",
    "snatch st",
    "nobleman of cross",
    "nobleman of cross",
    "metamorphosis",
    "metamorphosis",
    "metamorphosis",
]

t3s = [
    "scapegoat",
    "scapegoat",
    "scapegoat",
    "book of mo",
    "book of mo",
    "book of mo",
    "card destruction",
    "brain control",
    "brain control",
    "brain control",
    "creature swap",
    "creature swap",
]

t4s = [
    "wave-motion cannon",
    "wave-motion cannon",
    "wave-motion cannon",
    "level limit",
    "level limit",
    "messenger of peace",
    "messenger of peace",
    "messenger of peace",
]

w = [
    "reasoning",
    "reasoning",
    "reasoning"
]

t1t = [
    "mirror force",
    "sakuretsu",
    "sakuretsu",
    "sakuretsu",
    "call of the haunted",
    "ring of dest",
]

t2t = [
    "torrential",
    "solemn ju",
    "solemn ju",
    "solemn ju",
    "raigeki break",
    "raigeki break",
    "raigeki break",
    "dust tornado",
    "dust tornado",
    "dust tornado",
]

t3t = [
    "royal decree",
    "royal decree",
    "royal decree",
    "nightmare wheel",
    "nightmare wheel",
    "nightmare wheel",
    "ojama trio",
    "ojama trio",
    "ojama trio",
]

t4t = [
    "just desserts",
    "just desserts",
    "just desserts"
]

t1m = [
    "Black luster soldier - ",
    "chaos sorc",
    "chaos sorc",
    "chaos sorc",
    "sangan",
    "tribe-inf",
    "jinz",
    "breaker the mag",
    "d.d. warrior lady",
    "exiled force",
    "don z",
    "don z",
    "don z",
    "cyber jar",
]

t2m = [
    "sinister",
    "tsuk",
    "tsuk",
    "tsuk",
    "magician of faith",
    "magician of faith",
    "magician of faith",
    "morphing jar",
]

t3m = ["dark magician of cha"]

t4m = [
    "magical merchant",
    "magical merchant",
    "magical merchant"
]

T1_STRENGTH = 5
T2_STRENGTH = 4
T3_STRENGTH = 3
T4_STRENGTH = 2
CORE_CARD_STRENGTH_TARGET = 50
DECK_SIZE_TARGET = 40

tiers = {
    "t1s": [{"approximate_name": card, "strength": T1_STRENGTH} for card in t1s],
    "t2s": [{"approximate_name": card, "strength": T2_STRENGTH} for card in t2s],
    "t3s": [{"approximate_name": card, "strength": T3_STRENGTH} for card in t3s],
    "t4s": [{"approximate_name": card, "strength": T4_STRENGTH} for card in t4s],
    "t1t": [{"approximate_name": card, "strength": T1_STRENGTH} for card in t1t],
    "t2t": [{"approximate_name": card, "strength": T2_STRENGTH} for card in t2t],
    "t3t": [{"approximate_name": card, "strength": T3_STRENGTH} for card in t3t],
    #    "t4t":t4t,
    "t1m": [{"approximate_name": card, "strength": T1_STRENGTH} for card in t1m],
    "t2m": [{"approximate_name": card, "strength": T2_STRENGTH} for card in t2m],
    #    "t3m":t3m,
    #    "t4m":t4m,
    #    "w":w,
}

conn = sqlite3.connect("sql/cards.db")
cursor = conn.cursor()

card_pool = {}

for tier_name, tier in tiers.items():
    tier_cards = []
    for card in tier:
        results = cards_by_name(card["approximate_name"], conn)
        card_info = results[0]  # assume first result
        card = {**card}
        card["passcode"] = card_info["passcode"]
        card["card_name"] = card_info["passcode"]
        tier_cards.append(card)
    card_pool[tier_name] = tier_cards

if not os.path.exists('decks'):
    os.makedirs('decks')
f = open("decks/random_deck.ydk", "w")
f.write("#main\n")

# core_cards = one_each_tier(card_pool)

core_cards = by_total_strength(
    [
        card
        for tier in [tier_pool for tier_pool in card_pool.values()]
        for card in tier
    ],
    CORE_CARD_STRENGTH_TARGET,
)

for card in core_cards:
    f.write(str(card["passcode"]) + "\n")

deck_size = len(core_cards)
remaining_filler = DECK_SIZE_TARGET - deck_size

monster_filler = int(remaining_filler * 0.55)
spell_filler = int(remaining_filler * 0.3)
trap_filler = int(remaining_filler * 0.1)

remaining_filler = DECK_SIZE_TARGET - (deck_size + monster_filler + spell_filler + trap_filler)
monster_filler += remaining_filler

for passcode in getFiller("Monster", monster_filler):
    f.write(str(passcode) + "\n")

for passcode in getFiller("Spell", spell_filler):
    f.write(str(passcode) + "\n")

for passcode in getFiller("Trap", trap_filler):
    f.write(str(passcode) + "\n")

f.write("\n#extra\n\n")
f.write("!side\n")


conn.close()
