import os

# fractional positions can lead so fucked up textures,
# they are cast to int where necessary

NETPLAY = int(os.getenv('YGONET', 1))
PRINT_FPS = False
VSYNC = 0
MEMES = False
SCALE = float(os.getenv('YGOSCALE', 1))
DECK_DIR = "decks/"
TEXTURE_SMOOTHING = False
SCREEN_WIDTH = 1200 * SCALE
SCREEN_HEIGHT = 900 * SCALE
HAND_CARD_WIDTH = 105 * SCALE
HAND_CARD_HEIGHT = 153 * SCALE
FIELD_CARD_WIDTH = 83 * SCALE
FIELD_CARD_HEIGHT = FIELD_CARD_WIDTH * 1.45762711864
PLAYMAT_WIDTH = 858 * SCALE
PLAYMAT_HEIGHT = 647 * SCALE
LP_DIGIT_WIDTH = 25 * SCALE
LP_DIGIT_HEIGHT = 40 * SCALE
LP_DIGIT_SPACING = int(LP_DIGIT_WIDTH + 4)
LP_DELTA_DIGIT_WIDTH = 15 * SCALE
LP_DELTA_DIGIT_HEIGHT = 20 * SCALE
LP_DELTA_DIGIT_SPACING = int(LP_DELTA_DIGIT_WIDTH + 4)
DECK_COUNT_DIGIT_WIDTH = 15 * SCALE
DECK_COUNT_DIGIT_HEIGHT = 20 * SCALE
DECK_COUNT_DIGIT_SPACING = int(LP_DELTA_DIGIT_WIDTH + 4)
PHASE_WIDTH = 36 * SCALE
PHASE_HEIGHT = 21 * SCALE
PHASE_SPACING = int(PHASE_WIDTH + 15)
ARROW_WIDTH = 14 * SCALE
ARROW_HEIGHT = 24 * SCALE
DEFAULT_TEXT_WIDTH = 10 * SCALE
DEFAULT_TEXT_HEIGHT = 20 * SCALE
DEFAULT_TEXT_SPACING = int(DEFAULT_TEXT_WIDTH * SCALE)
INFO_PANEL_CARD_WIDTH = SCREEN_WIDTH - PLAYMAT_WIDTH
INFO_PANEL_CARD_HEIGHT = int((SCREEN_WIDTH - PLAYMAT_WIDTH) * 1.4576271186)
INFO_PANEL_WIDTH = SCREEN_WIDTH - PLAYMAT_WIDTH
INFO_PANEL_HEIGHT = SCREEN_HEIGHT
DB_CARD_WIDTH = 80 * SCALE
DB_CARD_HEIGHT = DB_CARD_WIDTH * 1.45762711864
DB_CARD_SPACING = 5 * SCALE
DB_TEXT_WIDTH = int(14 * SCALE)
DB_TEXT_HEIGHT = int(14 * SCALE)
DB_TEXT_SPACING = DB_TEXT_WIDTH
DB_SCROLL_RATE = int(20 * SCALE)
DB_ICON_WIDTH = 25 * SCALE
DB_ICON_HEIGHT = 25 * SCALE

COORD = {
    "playmat" : (0 * SCALE, 107 * SCALE, 0),
    "phases" : (int(290 * SCALE), int(425 * SCALE), 0),
    "arrow" : (260 * SCALE, 425 * SCALE, 0),
    "p1" : {
        "m1" : (int(130 * SCALE), int(503 * SCALE), 0),
        "m2" : (int(259 * SCALE), int(503 * SCALE), 0),
        "m3" : (int(387 * SCALE), int(503 * SCALE), 0),
        "m4" : (int(516 * SCALE), int(503 * SCALE), 0),
        "m5" : (int(645 * SCALE), int(503 * SCALE), 0),
        "st1" : (int(130 * SCALE), int(632 * SCALE), 0),
        "st2" : (int(259 * SCALE), int(632 * SCALE), 0),
        "st3" : (int(387 * SCALE), int(632 * SCALE), 0),
        "st4" : (int(516 * SCALE), int(632 * SCALE), 0),
        "st5" : (int(645 * SCALE), int(632 * SCALE), 0),
        "deck" : (761 * SCALE, 632 * SCALE, 0),
        "fusion_deck" : (14 * SCALE, 632 * SCALE, 0),
        "field_spell" : (14 * SCALE, 503 * SCALE, 0),
        "gy" : (761 * SCALE, 503 * SCALE, 0),
        "banish" : (761 * SCALE, 374 * SCALE, 0),
        "hand_y" : 760 * SCALE,
        "lp" : (int(900 * SCALE), int(530 * SCALE), 0),
        "lp_delta" : (int(1050 * SCALE), int(550 * SCALE), 0),
        "deck_count" : (int(810 * SCALE), int(759 * SCALE), 0),
    }, "p2" : {
        "m1" : (int(130 * SCALE), int(237 * SCALE), 0),
        "m2" : (int(259 * SCALE), int(237 * SCALE), 0),
        "m3" : (int(387 * SCALE), int(237 * SCALE), 0),
        "m4" : (int(516 * SCALE), int(237 * SCALE), 0),
        "m5" : (int(645 * SCALE), int(237 * SCALE), 0),
        "st1" : (int(130 * SCALE), int(108 * SCALE), 0),
        "st2" : (int(259 * SCALE), int(108 * SCALE), 0),
        "st3" : (int(387 * SCALE), int(108 * SCALE), 0),
        "st4" : (int(516 * SCALE), int(108 * SCALE), 0),
        "st5" : (int(645 * SCALE), int(108 * SCALE), 0),
        "deck" : (int(14 * SCALE), int(108 * SCALE), 0),
        "fusion_deck" : (761 * SCALE, 108 * SCALE, 0),
        "field_spell" : (761 * SCALE, 237 * SCALE, 0),
        "gy" : (14 * SCALE, 237 * SCALE, 0),
        "banish" : (14 * SCALE, 366 * SCALE, 0),
        "hand_y" : -50 * SCALE,
        "lp" : (int(900 * SCALE), int(580 * SCALE), 0),
        "lp_delta" : (int(1050 * SCALE), int(600 * SCALE), 0),
        "deck_count" : (int(14 * SCALE), int(80 * SCALE), 0),
    }, "db" : {
        "main" : (20 * SCALE, 100 * SCALE, 0),
        "main_label" : (int(20 * SCALE), int(80 * SCALE), 0),
        "fusion" : (20 * SCALE, 610 * SCALE, 0),
        "fusion_label" : (int(20 * SCALE), int(590 * SCALE), 0),
        "side" : (20 * SCALE, 770 * SCALE, 0),
        "side_label" : (int(20 * SCALE), int(750 * SCALE), 0),
        "search" : (int(10 * SCALE), int(10 * SCALE), 0),
        "save_icon" : (int(1150 * SCALE), int(860 * SCALE), 0),
        "new_icon" : (int(1100 * SCALE), int(860 * SCALE), 0),
        "deck_dir" : (int(858 * SCALE), int(510 * SCALE), 0),
    },
}
