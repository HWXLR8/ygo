#ifndef MULTICARDZONE_H
#define MULTICARDZONE_H

#include <glm/glm.hpp>

#include <vector>

#include <card.hpp>

class MultiCardZone {
 public:
  MultiCardZone(unsigned int player_num, glm::vec2 coord, CardLocation location_type);
  void loadCardsFromPasscodeList(std::vector<std::string>& passcodes);
  void fullyCollapse();
  void update(double dt);
  virtual std::optional<Card*> getActiveCard(glm::vec2 mouse_pos);
  virtual void addCard(Card card, double dt);
  bool isEmpty();
  bool isSpread();
  void fade();
  void illuminate();
  void render(Renderer *renderer);
  void spread();
  void collapse();
  glm::vec2 getCoord();
  std::optional<Card*> getCardByCardID(std::string card_id);

protected:
  unsigned int player_num_;
  glm::vec2 coord_;
  CardLocation location_type_;
  std::vector<Card> cards_ = {};
  int num_cards_exposed_ = 1;
  int top_card_displacement_ = 0;
};


#endif
