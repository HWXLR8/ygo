#include <player.hpp>
#include <config.hpp>
#include <mixer.hpp>

Player::Player(unsigned int player_num, DeckList deck_list) {
  player_num_ = player_num;

  if (player_num == 1) {
    // field
    field_ = new Field(1);

    // main deck
    main_deck_ = new Deck(player_num, COORD.p1.deck, deck_list.main_deck, MAIN_DECK);
    main_deck_->shuffle();

    // fusion deck
    fusion_deck_ = new Deck(player_num, COORD.p1.fusion_deck, deck_list.fusion_deck, FUSION_DECK);

    // gy + banish
    gy_ = new MultiCardZone(player_num, COORD.p1.gy, GRAVEYARD);
    banish_ = new MultiCardZone(player_num, COORD.p1.banish, BANISH_PILE);
  } else {
    // field
    field_ = new Field(2);

    // main deck
    main_deck_ = new Deck(player_num, COORD.p2.deck, deck_list.main_deck, MAIN_DECK);
    main_deck_->shuffle();

    // fusion deck
    fusion_deck_ = new Deck(player_num, COORD.p2.fusion_deck, deck_list.fusion_deck, FUSION_DECK);

    // gy + banish
    gy_ = new MultiCardZone(player_num, COORD.p2.gy, GRAVEYARD);
    banish_ = new MultiCardZone(player_num, COORD.p2.banish, BANISH_PILE);
  }
  // hand
  hand_ = new Hand(player_num);
};

void Player::update(double dt) {
  main_deck_->update(dt);
  fusion_deck_->update(dt);
  hand_->update(dt);
  field_->update(dt);
  gy_->update(dt);
  banish_->update(dt);
}

void Player::render(Renderer* renderer) {
  fusion_deck_->render(renderer);
  main_deck_->render(renderer);
  hand_->render(renderer);
  field_->render(renderer);
  gy_->render(renderer);
  banish_->render(renderer);
}

void Player::draw(double dt) {
  main_deck_->fullyCollapse();
  if (main_deck_->isEmpty()) {
    return;
  }
  Mixer::playSound("draw");
  Card card = main_deck_->popLastCard();
  card.forceFaceDownATK();
  hand_->addCard(card, dt);
}

void Player::mill(double dt) {
  if (main_deck_->isEmpty()) {
    return;
  }
  Mixer::playSound("generic_move");
  main_deck_->fullyCollapse();
  gy_->fullyCollapse();
  Card card = main_deck_->popLastCard();
  card.forceFaceDownATK();
  gy_->addCard(card, dt);
}

std::optional<Card*> Player::getActiveCard(glm::vec2 mouse_pos) {
  std::optional<Card*> card;

  card = main_deck_->getActiveCard(mouse_pos);
  if (card.has_value()) {
    return card;
  }

  card = gy_->getActiveCard(mouse_pos);
  if (card.has_value()) {
    return card;
  }

  card = banish_->getActiveCard(mouse_pos);
  if (card.has_value()) {
    return card;
  }

  card = field_->getActiveCard(mouse_pos);
  if (card.has_value()) {
    return card;
  }

  card = hand_->getActiveCard(mouse_pos);
  return card;
}

unsigned int Player::getPlayerNum() {
  return player_num_;
}

void Player::shuffleHand(double dt) {
  hand_->shuffle(dt);
}

void Player::activateCard(Card* card, double dt) {
  std::optional<SingleCardZone*> zone = field_->getFreeSTZone();
  if (card->isMonster() ||
      card->inDeck() ||
      card->inGY() ||
      card->inBanish()) {
    return;
  }
  if (card->inHand()) {
    if (!zone.has_value()) {
      return;
    }
    moveCardToZone(*card, *zone.value(), dt);
    removeCard(card);
  } else if (card->onField()) {
    card->flip(DEFAULT_FLIP_SPEED, dt);
  }
}

void Player::normalSummonCard(Card* card, double dt) {
  std::optional<SingleCardZone*> zone = field_->getFreeMZone();
  if (!zone.has_value() ||
      card->onField() ||
      !card->isMonster() ||
      (!card->isFaceUp() && player_num_ == 1)) {
    return;
  }
  if (card->isFusion()) {
    fusion_deck_->fullyCollapse();
  }
  moveCardToZone(*card, *zone.value(), dt);
  removeCard(card);
}

void Player::moveCardToZone(Card card, SingleCardZone& zone, double dt) {
  card.setLocation(FIELD);
  card.move(zone.getCoord(), 0.1, dt);
  card.changeSize(FIELD_CARD_SIZE, DEFAULT_GROWTH_SPEED, dt);
  zone.occupy(card);
}

void Player::moveSetCardToZone(Card card, SingleCardZone& zone, double dt) {
  card.setLocation(FIELD);
  card.move(zone.getCoord(), 0.1, dt);
  card.changeSize(FIELD_CARD_SIZE, DEFAULT_GROWTH_SPEED, dt);
  zone.occupy(card);
}

void Player::sendCardToGY(Card* card, double dt) {
  if (card->getLocation() == GRAVEYARD) {
    return;
  }
  if (card->isToken()) {
    removeCard(card);
    return;
  }
  Mixer::playSound("generic_move");
  gy_->addCard(*card, dt);
  removeCard(card);
}

// remove a card from wherever it resides
void Player::removeCard(Card* card) {
  CardLocation location = card->getLocation();

  switch (location) {
  case HAND:
    hand_->removeCard(card);
    break;

  case FIELD:
    field_->removeCard(card);
    break;

  case MAIN_DECK:
    throw std::runtime_error("main_deck_->remove() not implemented");
    break;

  case FUSION_DECK:
    throw std::runtime_error("fusion_deck_->remove() not implemented");
    break;

  case GRAVEYARD:
    throw std::runtime_error("gy_->remove() not implemented");
    break;

  case BANISH_PILE:
    throw std::runtime_error("banish_->remove() not implemented");
    break;
  }
}

void Player::flipCard(Card* card, double dt) {
  if (card->isToken()) {
    return;
  }
  if (!card->onField() &&
      !card->inHand()) {
    return;
  }
  if (card->onField() &&
      card->isMonster() &&
      card->inAttackPosition()) {
    return;
  }
  card->flip(DEFAULT_FLIP_SPEED, dt);
}

void Player::banishCard(Card* card, double dt) {
  if (card->getLocation() == BANISH_PILE) {
    return;
  }
  if (card->isToken()) {
    removeCard(card);
    return;
  }
  Mixer::playSound("generic_move");
  banish_->addCard(*card, dt);
  removeCard(card);
}

void Player::changeCardBattlePosition(Card* card, double dt) {
  if (!card->onField() ||
      !card->isFaceUp() ||
      (!card->isMonster() && !card->isToken())) {
    return;
  }
  Mixer::playSound("change_position");
  card->changeBattlePosition(dt);
}

void Player::returnCardToHand(Card* card, double dt) {
  if (card->isToken() ||
      card->inHand() ||
      (card->isFusion() && card->inFusionDeck())) {
    return;
  }
  Mixer::playSound("draw");
  hand_->addCard(*card, dt);
  removeCard(card);
}

void Player::tsukCard(Card* card, double dt) {
  if (card->isToken() ||
      !card->onField() ||
      !card->isMonster() ||
      (card->inFaceUpDefensePosition())) {
    return;
  }
  Mixer::playSound("change_position");
  card->tsuk(dt);
}

void Player::setCard(Card* card, double dt) {
  if (!card->inHand() ||
      !card->isFaceUp()) {
    return;
  }

  std::optional<SingleCardZone*> zone;
  if (card->isMonster()) {
    zone = field_->getFreeMZone();
  } else if (card->isSpellOrTrap()) {
    zone = field_->getFreeSTZone();
  }
  if (!zone.has_value()) {
    return;
  }

  if (card->isMonster()) {
    card->forceFaceDownDEF();
  } else if (card->isSpellOrTrap()) {
    card->forceFaceDownATK();
  }

  moveCardToZone(*card, *zone.value(), dt);
  removeCard(card);
}

void Player::spreadCards(glm::vec2 mouse_pos) {
  if (mouseAlignedWithMainDeck(mouse_pos)) {
    main_deck_->spread();
  }
  else if (mouseAlignedWithGY(mouse_pos)) {
    gy_->spread();
  } else if (mouseAlignedWithBanish(mouse_pos)) {
    banish_->spread();
  }
}

void Player::collapseCards(glm::vec2 mouse_pos) {
  if (mouseAlignedWithMainDeck(mouse_pos)) {
    main_deck_->collapse();
  }
  else if (mouseAlignedWithGY(mouse_pos)) {
    gy_->collapse();
  } else if (mouseAlignedWithBanish(mouse_pos)) {
    banish_->collapse();
  }
}

Card* Player::getCardByCardID(std::string card_id) {
  std::optional<Card*> card;

  // hand
  card = hand_->getCardByCardID(card_id);
  if (card.has_value()) {
    return card.value();
  }

  // main deck
  card = main_deck_->getCardByCardID(card_id);
  if (card.has_value()) {
    return card.value();
  }

  // fusion deck
  card = fusion_deck_->getCardByCardID(card_id);
  if (card.has_value()) {
    return card.value();
  }

  // gy
  card = gy_->getCardByCardID(card_id);
  if (card.has_value()) {
    return card.value();
  }

  // banish
  card = banish_->getCardByCardID(card_id);
  if (card.has_value()) {
    return card.value();
  }

  // check field
  card = field_->getCardByCardID(card_id);
  if (card.has_value()) {
    return card.value();
  }
}

bool Player::mouseAlignedWithMainDeck(glm::vec2 mouse_pos) {
  glm::vec2 main_deck_coord = main_deck_->getCoord();
  return ((mouse_pos.y > main_deck_coord.y) &&
	  (mouse_pos.y < main_deck_coord.y + FIELD_CARD_SIZE.y));
}

bool Player::mouseAlignedWithGY(glm::vec2 mouse_pos) {
  glm::vec2 gy_coord = gy_->getCoord();
  return ((mouse_pos.y > gy_coord.y) &&
	  (mouse_pos.y < gy_coord.y + FIELD_CARD_SIZE.y));
}

bool Player::mouseAlignedWithBanish(glm::vec2 mouse_pos) {
  glm::vec2 banish_coord = banish_->getCoord();
  return ((mouse_pos.y > banish_coord.y) &&
	  (mouse_pos.y < banish_coord.y + FIELD_CARD_SIZE.y));
}
