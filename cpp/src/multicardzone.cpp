#include <multicardzone.hpp>
#include <rng.hpp>
#include <config.hpp>

MultiCardZone::MultiCardZone(unsigned int player_num, glm::vec2 coord, CardLocation location_type)
  : player_num_(player_num), coord_(coord), location_type_(location_type) {}

void MultiCardZone::loadCardsFromPasscodeList(std::vector<std::string>& passcodes) {
  cards_ = {};
  for (auto passcode : passcodes) {
    std::string id = RNG::generateCardID(player_num_, 15);
    Card card(id, passcode, player_num_, location_type_);
    addCard(card, 0);
  }
}

void MultiCardZone::fullyCollapse() {
  num_cards_exposed_ = 1;
  top_card_displacement_ = 0;
  for (auto& card : cards_) {
    if (!card.animationInProgress()) {
      card.move(coord_, 0, 0);
    }
  }
}

void MultiCardZone::update(double dt) {
  for (auto& card : cards_) {
    card.update(dt);
    // if cards are not spread
    if (!isSpread()) {
      card.setInvisible();
    }
  }

  // we cant make shit invisible until the new top card has completely
  // covererd the zone
  if (cards_.empty()) {
    return;
  }

  if (cards_.back().animationInProgress()) {
    // we show up to max of 6 cards in case there are tons of cards
    // moving into the zone (quick mill etc). tbh i have no fucking
    // idea how this shit works
    int visible_cards = std::min(static_cast<int>(cards_.size()) - 1, 5);
    int stop = cards_.size() - visible_cards - 1;
    for (int i = cards_.size() - 1; i >= stop; i--) {
      cards_[i].setVisible();
    }
  }
  // top card is always visible
  cards_.back().setVisible();
}

std::optional<Card*> MultiCardZone::getActiveCard(glm::vec2 mouse_pos) {
  Card* active_card = nullptr;
  for (auto& card : cards_) {
    if (card.isActive(mouse_pos)) {
      active_card = &card;
    }
  }
  if (active_card == nullptr) {
    return std::nullopt;
  }
  return active_card;
}

void MultiCardZone::addCard(Card card, double dt) {
  fullyCollapse();
  card.changeSize(FIELD_CARD_SIZE, DEFAULT_GROWTH_SPEED, dt);
  card.switchToFaceUpATK(dt);
  card.setLocation(location_type_);
  card.move(coord_, 0.2, dt);
  cards_.push_back(card);
}

bool MultiCardZone::isEmpty() {
  return cards_.empty();
}

bool MultiCardZone::isSpread() {
  return !(num_cards_exposed_ == 1 && top_card_displacement_ == 0);
}

void MultiCardZone::fade() {
  for (auto& card : cards_) {
    card.fade();
  }
}

void MultiCardZone::illuminate() {
  for (auto& card : cards_) {
    card.illuminate();
  }
}

void MultiCardZone::render(Renderer *renderer) {
  for (auto& card : cards_) {
    card.render(renderer);
  }
}

void MultiCardZone::spread() {
  if (cards_.empty() ||
      static_cast<std::vector<Card>::size_type>(num_cards_exposed_) == cards_.size()) {
    return;
  }

  double dx = FIELD_CARD_SIZE.x / 2;
  top_card_displacement_ += dx;
  auto rv = cards_.rbegin();
  for (int i = 0; i < num_cards_exposed_; i++) {
    rv[i].setVisible();
    rv[i + 1].setVisible();
    glm::vec2 current_pos = rv[i].getPosition();
    glm::vec2 new_pos = current_pos - glm::vec2 {dx, 0};
    rv[i].move(new_pos, 0, 0);
  }

  if (top_card_displacement_ == FIELD_CARD_SIZE.x) {
    top_card_displacement_ = 0;
    num_cards_exposed_ += 1;
  }
}

void MultiCardZone::collapse() {
  if (cards_.empty() ||
      (static_cast<std::vector<Card>::size_type>(num_cards_exposed_) == 1 && top_card_displacement_ == 0)) {
    return;
  }

  auto rv = cards_.rbegin();
  if (static_cast<std::vector<Card>::size_type>(num_cards_exposed_) != cards_.size()) {
    if (static_cast<std::vector<Card>::size_type>(num_cards_exposed_) == cards_.size() - 1) {
      rv[num_cards_exposed_ + 1].setInvisible();
    } else if (static_cast<std::vector<Card>::size_type>(num_cards_exposed_) <= cards_.size() - 2) {
      rv[num_cards_exposed_+ 1].setInvisible();
      rv[num_cards_exposed_+ 2].setInvisible();
    }
  }

  double dx = FIELD_CARD_SIZE.x / 2;
  if (top_card_displacement_ == 0) {
    top_card_displacement_ = FIELD_CARD_SIZE.x;
    num_cards_exposed_ -= 1;
  }
  top_card_displacement_ -= dx;
  for (int i = 0; i < num_cards_exposed_; i++) {
    glm::vec2 current_pos = rv[i].getPosition();
    glm::vec2 new_pos = current_pos + glm::vec2 {dx, 0};
    rv[i].move(new_pos, 0, 0);
  }
}

glm::vec2 MultiCardZone::getCoord() {
  return coord_;
}

std::optional<Card*> MultiCardZone::getCardByCardID(std::string card_id) {
  for (Card& card : cards_) {
    if (card.getID() == card_id) {
      return &card;
    }
  }
  return std::nullopt;
}
