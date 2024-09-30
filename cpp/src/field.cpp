#include <field.hpp>

Field::Field(unsigned int player_num) {
  if (player_num == 1) {
    mzones_ = {
      SingleCardZone(1, MONSTER_ZONE, 1, COORD.p1.m1),
      SingleCardZone(2, MONSTER_ZONE, 1, COORD.p1.m2),
      SingleCardZone(3, MONSTER_ZONE, 1, COORD.p1.m3),
      SingleCardZone(4, MONSTER_ZONE, 1, COORD.p1.m4),
      SingleCardZone(5, MONSTER_ZONE, 1, COORD.p1.m5),
    };
    stzones_ = {
      SingleCardZone(6, SPELL_TRAP_ZONE, 1, COORD.p1.st1),
      SingleCardZone(7, SPELL_TRAP_ZONE, 1, COORD.p1.st2),
      SingleCardZone(8, SPELL_TRAP_ZONE, 1, COORD.p1.st3),
      SingleCardZone(9, SPELL_TRAP_ZONE, 1, COORD.p1.st4),
      SingleCardZone(10, SPELL_TRAP_ZONE, 1, COORD.p1.st5),
      SingleCardZone(11, FIELD_SPELL_ZONE, 1, COORD.p1.field_spell),
    };
  } else if (player_num == 2) {
    mzones_ = {
      SingleCardZone(1, MONSTER_ZONE, 2, COORD.p2.m5),
      SingleCardZone(2, MONSTER_ZONE, 2, COORD.p2.m4),
      SingleCardZone(3, MONSTER_ZONE, 2, COORD.p2.m3),
      SingleCardZone(4, MONSTER_ZONE, 2, COORD.p2.m2),
      SingleCardZone(5, MONSTER_ZONE, 2, COORD.p2.m1),
    };
    stzones_ = {
      SingleCardZone(6, SPELL_TRAP_ZONE, 2, COORD.p2.st5),
      SingleCardZone(7, SPELL_TRAP_ZONE, 2, COORD.p2.st4),
      SingleCardZone(8, SPELL_TRAP_ZONE, 2, COORD.p2.st3),
      SingleCardZone(9, SPELL_TRAP_ZONE, 2, COORD.p2.st2),
      SingleCardZone(10, SPELL_TRAP_ZONE, 2, COORD.p2.st1),
      SingleCardZone(11, FIELD_SPELL_ZONE, 2, COORD.p2.field_spell),
    };
  }
}

void Field::update(double dt) {
  for (auto& zone : mzones_) {
    zone.update(dt);
  }
  for (auto& zone : stzones_) {
    zone.update(dt);
  }
}

void Field::render(Renderer* renderer) {
  for (auto& zone : stzones_) {
    zone.render(renderer);
  }
  for (auto& zone : mzones_) {
    zone.render(renderer);
  }
}

std::optional<SingleCardZone*> Field::getFreeSTZone() {
  for (auto& zone : stzones_) {
    if (!zone.isOccupied() && zone.getType() == SPELL_TRAP_ZONE) {
      return &zone;
    }
  }
  return std::nullopt;
}

std::optional<SingleCardZone*> Field::getFreeMZone() {
  for (auto& zone : mzones_) {
    if (!zone.isOccupied()) {
      return &zone;
    }
  }
  return std::nullopt;
}

std::optional<SingleCardZone*> Field::getOccupiedZoneByCardID(std::string id) {
  for (auto& zone : mzones_) {
    if (zone.isOccupied() && zone.getCard().value()->getID() == id) {
      return &zone;
    }
  }
  return std::nullopt;
}

std::optional<Card*> Field::getActiveCard(glm::vec2 mouse_pos) {
  std::optional<Card*> active_card;
  for (auto& zone : mzones_) {
    active_card = zone.getActiveCard(mouse_pos);
    if (active_card.has_value()) {
      return active_card;
    }
  }
  for (auto& zone : stzones_) {
    active_card = zone.getActiveCard(mouse_pos);
    if (active_card.has_value()) {
      return active_card;
    }
  }
  if (active_card.has_value()) {
    return active_card;
  }
  return active_card;
}

void Field::removeCard(Card* card) {
  for (auto& zone : mzones_) {
    if (zone.isOccupied() && zone.getCard().value() == card) {
      zone.clear();
    }
  }
  for (auto& zone : stzones_) {
    if (zone.isOccupied() && zone.getCard().value() == card) {
      zone.clear();
    }
  }
}

std::optional<Card*> Field::getCardByCardID(std::string card_id) {
  for (auto& zone : mzones_) {
    if (zone.isOccupied() && zone.getCard().value()->getID() == card_id) {
      return zone.getCard();
    }
  }
  for (auto& zone : stzones_) {
    if (zone.isOccupied() && zone.getCard().value()->getID() == card_id) {
      return zone.getCard();
    }
  }
  return std::nullopt;
}
