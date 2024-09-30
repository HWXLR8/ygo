#ifndef CONFIG_H
#define CONFIG_H

#include <glm/glm.hpp>

const int NETWORK_PORT = 6969;

const float SCALE = 1.0;
const glm::vec2 SCREEN_SIZE {1600, 900};
const glm::vec2 FIELD_CARD_SIZE {86, 123};
const glm::vec2 HAND_CARD_SIZE {105, 153};
const glm::vec2 PLAYMAT_SIZE {858, 647};
const glm::vec2 MAG_CARD_SIZE {500 * 1/1.4576271186, 500};
const glm::vec2 DEFAULT_GROWTH_SPEED {210, 306};
const glm::vec3 DEFAULT_TSUK_SPEED {700, 0, 400};
const int DEFAULT_FLIP_SPEED = 800;
const int DEFAULT_POSITION_CHANGE_SPEED = 500;

struct EditorCoord {
  glm::vec2 main;
  glm::vec2 main_label;
  glm::vec2 fusion;
  glm::vec2 fusion_label;
  glm::vec2 side;
  glm::vec2 side_label;
  glm::vec2 search;
  glm::vec2 save_icon;
  glm::vec2 new_icon;
  glm::vec2 deck_dir;
};

struct PlayerCoord {
  glm::vec2 m1;
  glm::vec2 m2;
  glm::vec2 m3;
  glm::vec2 m4;
  glm::vec2 m5;
  glm::vec2 st1;
  glm::vec2 st2;
  glm::vec2 st3;
  glm::vec2 st4;
  glm::vec2 st5;
  glm::vec2 deck;
  glm::vec2 fusion_deck;
  glm::vec2 field_spell;
  glm::vec2 gy;
  glm::vec2 banish;
  glm::vec2 hand;
  glm::vec2 lp;
  glm::vec2 lp_delta;
  glm::vec2 deck_count;
};

struct GameCoord {
  glm::vec2 playmat {371, 107};
  glm::vec2 phases {290, 425};
  glm::vec2 arrow {260, 425};
  glm::vec2 mag_card {0, 0};
  PlayerCoord p1 = {
    p1.m1 = glm::vec2 {495, 502},
    p1.m2 = glm::vec2 {626, 502},
    p1.m3 = glm::vec2 {757, 502},
    p1.m4 = glm::vec2 {888, 502},
    p1.m5 = glm::vec2 {1019, 502},
    p1.st1 = glm::vec2 {495, 631},
    p1.st2 = glm::vec2 {626, 631},
    p1.st3 = glm::vec2 {757, 631},
    p1.st4 = glm::vec2 {888, 631},
    p1.st5 = glm::vec2 {1019, 631},
    p1.deck = glm::vec2 {1143, 631},
    p1.fusion_deck = glm::vec2 {371, 631},
    p1.field_spell = glm::vec2 {14, 502},
    p1.gy = glm::vec2 {1143, 502},
    p1.banish = glm::vec2 {1143, 373},
    p1.hand = glm::vec2 {430, 760},
    p1.lp = glm::vec2 {900, 530},
    p1.lp_delta = glm::vec2 {1050, 550},
    p1.deck_count = glm::vec2 {1050, 550},
  };
  PlayerCoord p2 = {
    p2.m1 = glm::vec2 {130, 237},
    p2.m2 = glm::vec2 {259, 237},
    p2.m3 = glm::vec2 {387, 237},
    p2.m4 = glm::vec2 {516, 237},
    p2.m5 = glm::vec2 {645, 237},
    p2.st1 = glm::vec2 {130, 108},
    p2.st2 = glm::vec2 {259, 108},
    p2.st3 = glm::vec2 {387, 108},
    p2.st4 = glm::vec2 {516, 108},
    p2.st5 = glm::vec2 {645, 108},
    p2.deck = glm::vec2 {14, 108},
    p2.fusion_deck = glm::vec2 {761, 108},
    p2.field_spell = glm::vec2 {761, 108},
    p2.gy = glm::vec2 {14, 237},
    p2.banish = glm::vec2 {14, 237},
    p2.hand = glm::vec2 {0, -50},
    p2.lp = glm::vec2 {900, 580},
    p2.lp_delta = glm::vec2 {1050, 600},
    p2.deck_count = glm::vec2 {14, 80},
  };
  /* EditorCoord ed; */
} const COORD;

#endif
