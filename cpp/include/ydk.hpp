#ifndef YDK_H
#define YDK_H

#include <string>
#include <vector>

struct DeckList {
  std::vector<std::string> main_deck;
  std::vector<std::string> fusion_deck;
};

class YDK {
public:
  YDK(std::string deck);

  inline std::vector<std::string> getMainDeck() {
    return main_deck_;
  }

  inline std::vector<std::string> getFusionDeck() {
    return fusion_deck_;
  }

  inline std::vector<std::string> getSideDeck() {
    return side_deck_;
  }

private:
  std::vector<std::string> main_deck_;
  std::vector<std::string> fusion_deck_;
  std::vector<std::string> side_deck_;
  std::vector<std::string>* current_deck_ = &main_deck_;
};

#endif
