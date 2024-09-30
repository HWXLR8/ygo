#include <algorithm>

#include <rng.hpp>

std::random_device RNG::rdev;
std::mt19937 RNG::rgen(rdev());
std::default_random_engine RNG::eng1;
std::default_random_engine RNG::eng2;

std::string RNG::randID(unsigned int len) {
  std::string alphanum = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
  std::string id = "";
  for (unsigned int i = 0; i < len; i++) {
    id += alphanum[randInt(0, 61)];
  }
  return id;
}

std::string RNG::generateCardID(unsigned int player_num, unsigned int len) {
  std::string alphanum = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
  std::string id = "";
  std::uniform_int_distribution<int> distr(0, 61);
  if (player_num == 1) {
    for (unsigned int i = 0; i < len; i++) {
      id += alphanum[distr(eng1)];
    }
  } else if (player_num == 2) {
    for (unsigned int i = 0; i < len; i++) {
      id += alphanum[distr(eng2)];
    }
  }
  return id;
}

int RNG::randInt(int min, int max) {
  std::uniform_int_distribution<int> distr(min, max);
  return distr(rgen);
}

void RNG::shuffleCards(unsigned int player_num, std::vector<Card>& vec) {
  if (player_num == 1) {
    std::shuffle(std::begin(vec), std::end(vec), eng1);
  } else if (player_num == 2) {
    std::shuffle(std::begin(vec), std::end(vec), eng2);
  }
}

void RNG::seedRNG(unsigned int player_num, std::string seed_str) {
  std::seed_seq seed (seed_str.begin(), seed_str.end());
  if (player_num == 1) {
    eng1 = std::default_random_engine(seed);
  } else if (player_num == 2) {
    eng2 = std::default_random_engine(seed);
  }
}
