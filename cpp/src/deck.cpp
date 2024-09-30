#include <deck.hpp>
#include <rng.hpp>
#include <config.hpp>

Deck::Deck(unsigned int player_num, glm::vec2 coord, std::vector<std::string>& deck_list, CardLocation location_type)
  : MultiCardZone(player_num, coord, location_type){
  coord_ = coord;
  loadCardsFromPasscodeList(deck_list);
  dummy_card_ = new Graphic("../netplay/assets/blank_card_back.png", coord_, FIELD_CARD_SIZE, false);
}

void Deck::shuffle() {
  RNG::shuffleCards(player_num_, cards_);
}

Card Deck::popLastCard() {
    Card card = cards_.back();
    cards_.pop_back();
    return card;
}

void Deck::render(Renderer* renderer) {
  for (auto& card : cards_) {
    card.render(renderer);
  }
  if (!cards_.empty() &&
      (num_cards_exposed_ == 1 && top_card_displacement_ == 0)) {
    dummy_card_->render(renderer);
  }
}

void Deck::update(double dt) {
  if (cards_.empty()) {
    return;
  }
  for (auto& card : cards_) {
    if (!card.animationInProgress()) {
      card.forceFaceUpATK();
    }
  }
  MultiCardZone::update(dt);
}

// override to make sure cards get flipped face down instead of face up
void Deck::addCard(Card card, double dt) {
  fullyCollapse();
  card.changeSize(FIELD_CARD_SIZE, DEFAULT_GROWTH_SPEED, dt);
  if (card.isFaceUp()) {
    card.flip(DEFAULT_FLIP_SPEED, dt);
  }
  if (!card.inAttackPosition()) {
    card.changeBattlePosition(dt);
  }
  card.setLocation(location_type_);
  card.move(coord_, 0.2, dt);
  cards_.push_back(card);
}

std::optional<Card*> Deck::getActiveCard(glm::vec2 mouse_pos) {
  if (!isSpread()) {
    return std::nullopt;
  }
  return MultiCardZone::getActiveCard(mouse_pos);
}
