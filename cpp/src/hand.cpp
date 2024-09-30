#include <algorithm>

#include <hand.hpp>
#include <rng.hpp>
#include <config.hpp>
#include <mixer.hpp>

Hand::Hand(unsigned int player_num) :
  player_num_(player_num) {};

void Hand::update(double dt) {
  for (auto& card : cards_) {
    card.update(dt);
  }
  if (refresh_needed_) {
    quickRefresh(dt);
    refresh_needed_ = false;
  }
}

void Hand::render(Renderer* renderer) {
  for (auto& card : cards_) {
    card.render(renderer);
  }
}

void Hand::addCard(Card card, double dt) {
  card.setVisible();
  CardLocation old_loc = card.getLocation();
  card.setLocation(HAND);
  if (old_loc == FIELD && !card.inAttackPosition()) {
    if (player_num_ == 1) {
      if (!card.isFaceUp()) {
	card.tsuk(dt);
      } else {
	card.changeBattlePosition(dt);
      }
    } else {
      if (card.isFaceUp()) {
	card.tsuk(dt);
      } else {
	card.changeBattlePosition(dt);
      }
    }
  }
  card.changeSize(HAND_CARD_SIZE, DEFAULT_GROWTH_SPEED, dt);
  // show card to opponent when appropriate
  if (card.isFaceUp() && (old_loc == MAIN_DECK || old_loc == GRAVEYARD || old_loc == BANISH_PILE)) {
    card.flip(500, dt);
  }
  if (player_num_ == 1 && !card.isFaceUp() && old_loc == MAIN_DECK) {
    card.flip(500, dt);
  }
  cards_.push_back(card);
  refresh(dt);
}

void Hand::refresh(double dt) {
  int c = 0;
  int num_cards = cards_.size();
  glm::vec2 coord;

  if (num_cards >= 6) {
    overlap_ = (HAND_CARD_SIZE.x / num_cards) * (num_cards - 6);
  } else {
    overlap_ = 0;
  }

  if (num_cards > 6) {
    for (auto& card : cards_) {
      card.stopMoving();
    }
  }

  for (auto& card : cards_) {
    double offset;
    if (player_num_ == 1) {
      offset = c * (HAND_CARD_SIZE.x - overlap_);
      coord = glm::vec2{COORD.p1.hand.x + offset, COORD.p1.hand.y};
    } else {
      offset = (SCREEN_SIZE.x - HAND_CARD_SIZE.x - MAG_CARD_SIZE.x) - (c * (HAND_CARD_SIZE.x - overlap_));
      coord = glm::vec2{COORD.p2.hand.x + offset, COORD.p2.hand.y};
    }

    if (card == cards_.back()) {
      card.move(coord, 0.3, dt);
    } else {
      if (card.isMoving()) {
	card.steerMovement(coord);
      }
      card.move(coord, 0.15, dt);
    }

    c++;
  }
}

// simple refresh method to be used for hand shuffle, and compressing
// hand after playing a card
void Hand::quickRefresh(double dt) {
  int c = 0;
  int num_cards = cards_.size();
  glm::vec2 coord;

  if (num_cards >= 6) {
    overlap_ = (HAND_CARD_SIZE.x / num_cards) * (num_cards - 6);
  } else {
    overlap_ = 0;
  }

  for (auto& card : cards_) {
    double offset;
    if (player_num_ == 1) {
      offset = c * (HAND_CARD_SIZE.x - overlap_);
      coord = glm::vec2{COORD.p1.hand.x + offset, COORD.p1.hand.y};
    } else {
      offset = (SCREEN_SIZE.x - HAND_CARD_SIZE.x - MAG_CARD_SIZE.x) - (c * (HAND_CARD_SIZE.x - overlap_));
      coord = glm::vec2{COORD.p2.hand.x + offset, COORD.p2.hand.y};
    }
    card.move(coord, 0.1, dt);
    c++;
  }
}

std::optional<Card*> Hand::getActiveCard(glm::vec2 mouse_pos) {
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

void Hand::shuffle(double dt) {
  if (cards_.empty()) {
    return;
  }
  Mixer::playSound("hand_shuffle");
  RNG::shuffleCards(player_num_, cards_);
  quickRefresh(dt);
}

void Hand::removeCard(Card* card) {
  cards_.erase(std::remove(cards_.begin(), cards_.end(), *card), cards_.end());
  refresh_needed_ = true;
}

std::optional<Card*> Hand::getCardByCardID(std::string card_id) {
  for (Card& card : cards_) {
    if (card.getID() == card_id) {
      return &card;
    }
  }
  return std::nullopt;
}
