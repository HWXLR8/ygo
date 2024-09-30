#include <fstream>

#include <ydk.hpp>

YDK::YDK(std::string deck) {
  std::ifstream f(deck);
  std::string line;
  while (getline(f, line)) {
    if (line == "#main") {
      continue;
    } else if (line == "#extra") {
      current_deck_ = &fusion_deck_;
      continue;
    } else if (line == "!side") {
      current_deck_ = &side_deck_;
      continue;
    } else if (line == "") {
      continue;
    }
    current_deck_->push_back(line);
  }
  f.close();
}
