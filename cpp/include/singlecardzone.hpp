#ifndef SINGLECARDZONE_H
#define SINGLECARDZONE_H

#include <glm/glm.hpp>

#include <card.hpp>

enum ZoneType {
  SPELL_TRAP_ZONE,
  MONSTER_ZONE,
  FIELD_SPELL_ZONE,
};

class SingleCardZone {
public:
  SingleCardZone(unsigned int id, ZoneType type, unsigned int player_num, glm::vec2 coord);
  void incrementCounter();
  void decrementCounter();
  unsigned int getID();
  unsigned int getOwner();
  ZoneType getType();
  glm::vec2 getCoord();
  void occupy(Card card);
  bool isOccupied();
  std::optional<Card*> getCard();
  std::optional<Card*> getActiveCard(glm::vec2 mouse_pos);
  void clear();
  bool isActive(glm::vec2 mouse_pos);
  void update(double dt);
  void render(Renderer *renderer);

private:
  unsigned int id_;
  ZoneType type_;
  unsigned int player_num_;
  glm::vec2 coord_;
  glm::vec2 set_coord_;
  unsigned int token_index_;
  unsigned int counter_ = 0;
  std::optional<Card> card_;
};

#endif
