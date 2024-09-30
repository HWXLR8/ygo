#ifndef INPUT_H
#define INPUT_H

#include <GLFW/glfw3.h>
#include <glm/glm.hpp>

#include <player.hpp>
#include <network.hpp>

enum MouseAction {
  LEFT_CLICK,
  RIGHT_CLICK,
  MIDDLE_CLICK,
  SCROLL_UP,
  SCROLL_DOWN,
  NONE,
};

class Input {
public:
  Input(GLFWwindow* window, Player* p1, Player* p2, Network* network);
  void processLocalInput(std::optional<Card*> active_card, double dt);
  void processNetworkInput(double dt);
  glm::vec2 getMousePosition();

private:
  bool keys_[1024] = {false};
  glm::vec2 mouse_pos_;
  MouseAction mouse_action_;
  Player* p1_;
  Player* p2_;
  Network* network_;

  bool isCommandValid(int key, std::optional<Card*> active_card);
  void sendCommandOverNetwork(NetworkCommandType command, std::map<std::string, std::string> command_data);
  void runKeyCommand(int key, Player* player, std::optional<std::string> active_card_id, double dt);
  void runMouseCommand(Player* player);

  // callbacks
  void keyCallback(GLFWwindow* window, int key, int scancode, int action, int mode);
  void cursorPositionCallback(GLFWwindow* window, double xpos, double ypos);
  void framebufferSizeCallback(GLFWwindow* window, int width, int height);
  void scrollCallback(GLFWwindow* window, double xoffset, double yoffset);
};

#endif
