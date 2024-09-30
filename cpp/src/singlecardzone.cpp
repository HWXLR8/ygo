#include <singlecardzone.hpp>
#include <config.hpp>

SingleCardZone::SingleCardZone(unsigned int id, ZoneType type, unsigned int player_num, glm::vec2 coord)
  : id_(id), type_(type), player_num_(player_num), coord_(coord){
  set_coord_ = glm::vec2(coord_.x + 0.5 * FIELD_CARD_SIZE.x - 0.5 * FIELD_CARD_SIZE.y,
			 coord_.y + 0.5 * FIELD_CARD_SIZE.y - 0.5 * FIELD_CARD_SIZE.x);
}

void SingleCardZone::incrementCounter() {
  if (counter_ != 9) {
    counter_ += 1;
  }
}

void SingleCardZone::decrementCounter() {
  if (counter_ != 0) {
    counter_ -= 1;
  }
}

unsigned int SingleCardZone::getID() {
  return id_;
}

unsigned int SingleCardZone::getOwner() {
  return player_num_;
}

ZoneType SingleCardZone::getType() {
  return type_;
}

glm::vec2 SingleCardZone::getCoord() {
  return coord_;
}

void SingleCardZone::occupy(Card card) {
  card_ = card;
}

bool SingleCardZone::isOccupied() {
  return card_.has_value();
}

std::optional<Card*> SingleCardZone::getCard() {
  if (card_.has_value()) {
    return &card_.value();
  }
  return std::nullopt;
}

std::optional<Card*> SingleCardZone::getActiveCard(glm::vec2 mouse_pos) {
  if (isActive(mouse_pos) && isOccupied()) {
    return &card_.value();
  }
  return std::nullopt;
}


void SingleCardZone::clear() {
  card_ = std::nullopt;
}

bool SingleCardZone::isActive(glm::vec2 mouse_pos) {
  return ((coord_.x <= mouse_pos.x) &&
	  (mouse_pos.x <= coord_.x + FIELD_CARD_SIZE.x) &&
	  (coord_.y <= mouse_pos.y) &&
	  (mouse_pos.y <= coord_.y + FIELD_CARD_SIZE.y));
}

void SingleCardZone::update(double dt) {
  // TODO UPDATE COUNTER
  if (isOccupied()) {
    card_.value().update(dt);
  }
}

void SingleCardZone::render(Renderer* renderer) {
  if (isOccupied()) {
    card_.value().render(renderer);
  }
}
