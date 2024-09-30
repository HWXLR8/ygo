#include <iostream>
#include <vector>
#include <string>
#include <optional>

#include <game.hpp>
#include <option_parser.hpp>

int main(int argc, char** argv) {
  Game* game = nullptr;
  try {
    std::vector<std::string> optional_opts = {"-s", "-c", "-d", "-e", "-g"};
    std::vector<std::string> opts_with_value = {"-c", "-d"};
    OptionParser* opts = new OptionParser(argc, argv, std::nullopt, optional_opts, opts_with_value);

    game = new Game(opts);
    game->run();
  } catch (const std::exception& e) {
    std::cerr << "\033[1;31mERROR: \033[0m" << e.what() << std::endl;
  }
  // only delete game if it was successfully initialized
  if (game != nullptr) {
    delete game;
  }
  return 0;
}
