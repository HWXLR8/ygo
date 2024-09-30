 #include <card.hpp>
#include <config.hpp>
#include <resource_manager.hpp>

std::optional<Texture2D> Card::back_texture_;

Card::Card(std::string id, std::string passcode, unsigned int player_num, CardLocation location) : Graphic("", glm::vec2{}, glm::vec2{}, false) {
  id_ = id;
  passcode_ = passcode;
  player_num_ = player_num;
  location_ = location;
  card_info_ = Database::queryCardInfoByPasscode(passcode_);
  size_ = FIELD_CARD_SIZE;
  if (player_num_ == 1) {
    if (isFusion()) {
      position_.x = COORD.p1.fusion_deck.x;
      position_.y = COORD.p1.fusion_deck.y;
      } else {
      position_.x = COORD.p1.deck.x;
      position_.y = COORD.p1.deck.y;
    }
  } else {
    rotation_ = {0.0f, 0.0f, 180.0f};
    if (isFusion()) {
      position_.x = COORD.p2.fusion_deck.x;
      position_.y = COORD.p2.fusion_deck.y;
      } else {
      position_.x = COORD.p2.deck.x;
      position_.y = COORD.p2.deck.y;
    }
  }
  if (!back_texture_.has_value()) {
    back_texture_ = ResourceManager::getTexture(std::string("../netplay/assets/blank_card_back.png"), false);
  }
  std::string tex_path = std::string("../netplay/assets/card_images/") + passcode_ + std::string(".jpg");
  texture_ = ResourceManager::getTexture(tex_path, false);
}

bool Card::operator ==(const Card& rhs) {
    return id_ == rhs.id_;
}

bool Card::operator !=(const Card& rhs) {
    return id_ != rhs.id_;
}

void Card::update(double dt) {
  if (flip_in_progress_) {
    flip(flip_speed_, dt);
  }
  if (position_change_in_progress_) {
    changeBattlePosition(dt);
  }
  if (tsuk_in_progress_) {
    tsuk(dt);
  }
  Graphic::update(dt);
}

void Card::render(Renderer* renderer) {
  if (!visible_) {
    return;
  }
  if (rotation_.y >= 90 || rotation_.x >= 90) {
    renderer->blit(back_texture_.value(), position_, size_, rotation_, color_);
  } else if ((in_atk_position_ && rotation_.y < 90) ||
	     (!in_atk_position_ && rotation_.x < 90)) {
    renderer->blit(texture_, position_, size_, rotation_, color_);
  }
}

void Card::changeBattlePosition(double dt) {
  position_change_in_progress_ = true;

  // how much are we moving this frame?
  double rotation_chunk = DEFAULT_POSITION_CHANGE_SPEED * dt;
  if ((in_atk_position_ && face_up_) ||
      (!in_atk_position_ && !face_up_)) {
    rotation_chunk *= -1;
  }

  rotation_.z += rotation_chunk;

  // are we done?
  if (in_atk_position_ && rotation_.z <= -90) {
    rotation_.z = -90;
    in_atk_position_ = false;
    position_change_in_progress_ = false;
  } else if (!in_atk_position_ && rotation_.z >= 0) {
    rotation_.z = 0;
    in_atk_position_ = true;
    position_change_in_progress_ = false;
  }
}

void Card::flip(double speed, double dt) {
  flip_in_progress_ = true;
  flip_speed_ = speed;
  if (face_up_) {
    flipDown(dt);
  } else {
    flipUp(dt);
  }
}

void Card::flipUp(double dt) {
  if (in_atk_position_) {
    rotation_.y -= flip_speed_ * dt;
  } else {
    rotation_.x -= flip_speed_ * dt;
  }
  // are we done?
  if (in_atk_position_ && rotation_.y <= 0) {
    rotation_.y = 0;
    flip_in_progress_ = false;
    face_up_ = true;
  } else if (!in_atk_position_ && rotation_.x <= 0) {
    rotation_.x = 0;
    flip_in_progress_ = false;
    face_up_ = true;
  }
}

void Card::flipDown(double dt) {
  if (in_atk_position_) {
    rotation_.y += flip_speed_ * dt;
  } else {
    rotation_.x += flip_speed_ * dt;
  }
  // are we done?
  if (in_atk_position_ && rotation_.y >= 180) {
    rotation_.y = 180;
    flip_in_progress_ = false;
    face_up_ = false;
  } else if (!in_atk_position_ && rotation_.x >= 180) {
    rotation_.x = 180;
    flip_in_progress_ = false;
    face_up_ = false;
  }
}

void Card::tsuk(double dt) {
  tsuk_in_progress_ = true;

  // how much are we moving this frame?
  glm::vec3 tsuk_chunk;
  if (face_up_) {
    tsuk_chunk = {
      DEFAULT_TSUK_SPEED.x * dt,
      DEFAULT_TSUK_SPEED.y * dt,
      DEFAULT_TSUK_SPEED.z * dt * -1,
    };
  } else {
    tsuk_chunk = {
      DEFAULT_TSUK_SPEED.x * dt * -1,
      DEFAULT_TSUK_SPEED.y * dt,
      DEFAULT_TSUK_SPEED.z * dt,
    };
  }

  rotation_ += tsuk_chunk;

  // are we done?
  if (in_atk_position_ && rotation_.z <= -90) {
    in_atk_position_ = false;
    face_up_ = false;
    rotation_.x = 180;
    rotation_.z = -90;
    tsuk_in_progress_ = false;
  } else if (!in_atk_position_ && rotation_.z >= 0) {
    in_atk_position_ = true;
    face_up_ = true;
    rotation_.x = 0;
    rotation_.z = 0;
    tsuk_in_progress_ = false;
  }
}

std::string Card::getID() {
  return id_;
}

std::string Card::getName() {
  return card_info_.card_name;
}

std::string Card::getPasscode() {
  return passcode_;
}

bool Card::isFaceUp() {
  return face_up_;
}

bool Card::isFusion() {
  return card_info_.card_subtype == "Fusion";
}

bool Card::isMonster() {
  return card_info_.card_type == "Monster";
}

bool Card::isSpellOrTrap() {
  return (card_info_.card_type == "Spell" ||
	  card_info_.card_type == "Trap");
}

bool Card::isToken() {
  return card_info_.card_type == "Token";
}

bool Card::inAttackPosition() {
  return in_atk_position_;
}

bool Card::inFaceUpDefensePosition() {
  return (face_up_ && !in_atk_position_);
}

bool Card::inHand() {
  return location_ == HAND;
}

bool Card::onField() {
  return location_ == FIELD;
}

bool Card::inDeck() {
  return location_ == MAIN_DECK;
}

bool Card::inFusionDeck() {
  return location_ == FUSION_DECK;
}

bool Card::inGY() {
  return location_ == GRAVEYARD;
}

bool Card::inBanish() {
  return location_ == BANISH_PILE;
}

void Card::switchToFaceUpATK(double dt) {
  // f/d defense
  if (!face_up_ && !in_atk_position_) {
    tsuk(dt);
    return;
  }
  // f/u defense
  if (face_up_ && !in_atk_position_) {
    changeBattlePosition(dt);
    return;
  }
  // f/d atk
  if (!face_up_ && in_atk_position_) {
    flip(DEFAULT_FLIP_SPEED, dt);
  }
}

void Card::forceFaceUpATK() {
  if (player_num_ == 1) {
    rotation_ = glm::vec3{0.0f, 0.0f, 0.0f};
  } else {
    rotation_ = glm::vec3{0.0f, 0.0f, 180.0f};
  }
  in_atk_position_ = true;
  face_up_ = true;
}

void Card::forceFaceDownATK() {
  if (player_num_ == 1) {
    rotation_ = glm::vec3{0.0f, 180.0f, 0.0f};
  } else {
    rotation_ = glm::vec3{0.0f, 180.0f, 180.0f};
  }
  in_atk_position_ = true;
  face_up_ = false;
}

void Card::forceFaceDownDEF() {
  if (player_num_ == 1) {
    rotation_ = glm::vec3{180.0f, 0.0f, -90.0f};
  } else {
    rotation_ = glm::vec3{180.0f, 0.0f, 90.0f};
  }
  in_atk_position_ = false;
  face_up_ = false;
}

void Card::setLocation(CardLocation location) {
  location_ = location;
}

CardLocation Card::getLocation() {
  return location_;
}

bool Card::animationInProgress() {
  return (flip_in_progress_ ||
	  move_in_progress_ ||
	  tsuk_in_progress_ ||
	  position_change_in_progress_);
}
