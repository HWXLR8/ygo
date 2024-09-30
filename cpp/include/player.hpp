#ifndef PLAYER_H
#define PLAYER_H

#include <string>
#include <optional>

#include <deck.hpp>
#include <hand.hpp>
#include <singlecardzone.hpp>
#include <field.hpp>
#include <ydk.hpp>

class Player {
public:
  Player(unsigned int player_num, DeckList deck_list);
  void fade();
  void illuminate();
  bool animationInProgress();
  void update(double dt);
  void render(Renderer* renderer);
  void draw(double dt);
  void mill(double dt);
  void activateCard(Card* card, double dt);
  void normalSummonCard(Card* card, double dt);
  void sendCardToGY(Card* card, double dt);
  void moveCardToZone(Card card, SingleCardZone& zone, double dt);
  void moveSetCardToZone(Card card, SingleCardZone& zone, double dt);
  std::optional<Card*> getActiveCard(glm::vec2 mouse_pos);
  unsigned int getPlayerNum();
  void shuffleHand(double dt);
  void flipCard(Card* card, double dt);
  void banishCard(Card* card, double dt);
  void changeCardBattlePosition(Card* card, double dt);
  void returnCardToHand(Card* card, double dt);
  void tsukCard(Card* card, double dt);
  void setCard(Card* card, double dt);
  void spreadCards(glm::vec2 mouse_pos);
  void collapseCards(glm::vec2 mouse_pos);
  Card* getCardByCardID(std::string card_id);

private:
  Hand* hand_;
  Deck* main_deck_;
  Deck* fusion_deck_;
  MultiCardZone* gy_;
  MultiCardZone* banish_;
  Field* field_;
  unsigned int player_num_;

  void removeCard(Card* card);
  bool mouseAlignedWithGY(glm::vec2 mouse_pos);
  bool mouseAlignedWithBanish(glm::vec2 mouse_pos);
  bool mouseAlignedWithMainDeck(glm::vec2 mouse_pos);
};


#endif
