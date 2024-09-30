#ifndef HAND_H
#define HAND_H

#include <vector>

#include <card.hpp>

class Hand {
 public:
  Hand(unsigned int player_num);
  void update(double dt);
  void render(Renderer* renderer);
  void addCard(Card card, double dt);
  void refresh(double dt);
  void quickRefresh(double dt);
  std::optional<Card*> getActiveCard(glm::vec2 mouse_pos);
  void shuffle(double dt);
  void removeCard(Card* card);
  std::optional<Card*> getCardByCardID(std::string card_id);

private:
  std::vector<Card> cards_ = {};
  unsigned int player_num_;
  int overlap_ = 0;
  bool refresh_needed_ = false;
};

#endif
