#ifndef GAME_H
#define GAME_H

#include <GLFW/glfw3.h>

#include <map>

#include <player.hpp>
#include <magcard.hpp>
#include <input.hpp>
#include <option_parser.hpp>
#include <network.hpp>


enum GameState {
  CONNECTING_TO_OPPONENT,
  DUEL_ACTIVE,
};

class Game {
 public:
  Game(OptionParser* opts);
  ~Game();
  void run();

private:
  GLFWwindow* window_;
  Player* p1_;
  Player* p2_;
  MagCard* mag_card_;
  std::optional<Card*> active_card_;
  Graphic* bg_;
  Graphic* playmat_;
  Graphic* playmat_fill_;
  Graphic* playmat_shadow_;
  Input* input_;
  GameState game_state_;
  Network* network_;

  void initGLFW();
  void initGLAD();
  void initGL();
  void setViewport();
  void update(double dt);
  void render();
  void getActiveCard();
  void parseOpts(OptionParser* opts);
  void syncRNG();
  void syncDecks(DeckList p1_deck, DeckList& p2_deck);

};

#endif
