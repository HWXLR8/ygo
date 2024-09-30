#ifndef CARD_H
#define CARD_H

#include <string>
#include <optional>

#include <database.hpp>
#include <renderer.hpp>
#include <graphic.hpp>

enum CardLocation {
  MAIN_DECK,
  FUSION_DECK,
  FIELD,
  HAND,
  GRAVEYARD,
  BANISH_PILE,
};

class Card : public Graphic{
public:
  Card(std::string id, std::string passcode, unsigned int player_num, CardLocation location);
  bool operator ==(const Card& rhs);
  bool operator !=(const Card& rhs);
  void flip(double speed, double dt);
  void flipUp(double dt);
  void flipDown(double dt);
  void changeBattlePosition(double dt);
  void tsuk(double dt);
  void update(double dt);
  void render(Renderer* renderer);
  std::string getID();
  std::string getPasscode();
  bool isFaceUp();
  bool isFusion();
  bool isMonster();
  bool isSpellOrTrap();
  bool isToken();
  bool inAttackPosition();
  bool inFaceUpDefensePosition();
  bool inDeck();
  bool inFusionDeck();
  bool inGY();
  bool inBanish();
  bool inHand();
  bool onField();
  void switchToFaceUpATK(double dt);
  void forceFaceUpATK();
  void forceFaceDownATK();
  void forceFaceDownDEF();
  void setLocation(CardLocation location);
  CardLocation getLocation();
  bool animationInProgress();
  std::string getName();

private:
  std::string id_;
  std::string passcode_;
  unsigned int player_num_;
  CardLocation location_;

  bool flip_in_progress_ = false;
  double flip_speed_;

  bool position_change_in_progress_ = false;
  bool tsuk_in_progress_ = false;
  bool face_up_ = true;
  bool in_atk_position_ = true;
  CardInfo card_info_;

  static std::optional<Texture2D> back_texture_;
};


#endif
