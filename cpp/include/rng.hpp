#ifndef RNG_H
#define RNG_H

#include <random>

#include <card.hpp>

class RNG {
public:
  static std::string randID(unsigned int len);
  static std::string generateCardID(unsigned int player_num, unsigned int len);
  static int randInt(int min, int max);
  static void shuffleCards(unsigned int player_num, std::vector<Card>& vec);
  static void seedRNG(unsigned int player_num, std::string seed_str);

private:
  // used for random IDs, different for each player
  static std::random_device rdev;
  static std::mt19937 rgen;

  // used for shuffling cards/hands, different for each player, but
  // tracked by each player for consistency
  static std::default_random_engine eng1;
  static std::default_random_engine eng2;
};

#endif
