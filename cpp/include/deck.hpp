#ifndef DECK_H
#define DECK_H

#include <multicardzone.hpp>

class Deck : public MultiCardZone {
public:
  Deck(unsigned int player_num, glm::vec2 coord, std::vector<std::string>& deck_list, CardLocation location_type);
  void shuffle();
  Card popLastCard();
  void update(double dt);
  void render(Renderer* renderer);
  void addCard(Card card, double dt) override;
  std::optional<Card*> getActiveCard(glm::vec2 mouse_pos) override;

private:
  Graphic* dummy_card_;
};

#endif
