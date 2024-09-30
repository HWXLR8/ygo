#include <input.hpp>

#include <algorithm>

Input::Input(GLFWwindow* window, Player* p1, Player* p2, Network* network) {
  p1_ = p1;
  p2_ = p2;
  network_ = network;

  // hack GLFW to accept a c++ member function as a callback
  glfwSetWindowUserPointer(window, this);
  auto keyCallbackAlias = [](GLFWwindow* window, int key, int scancode, int action, int mode) {
    static_cast<Input*>(glfwGetWindowUserPointer(window))->keyCallback(window, key, scancode, action, mode);
  };
  auto cursorPositionCallbackAlias = [](GLFWwindow* window, double xpos, double ypos) {
    static_cast<Input*>(glfwGetWindowUserPointer(window))->cursorPositionCallback(window, xpos, ypos);
  };
  auto framebufferSizeCallbackAlias = [](GLFWwindow* window, int width, int height) {
    static_cast<Input*>(glfwGetWindowUserPointer(window))->framebufferSizeCallback(window, width, height);
  };
  auto scrollCallbackAlias = [](GLFWwindow* window, double xoffset, double yoffset) {
    static_cast<Input*>(glfwGetWindowUserPointer(window))->scrollCallback(window, xoffset, yoffset);
  };
  glfwSetKeyCallback(window, keyCallbackAlias);
  glfwSetCursorPosCallback(window, cursorPositionCallbackAlias);
  glfwSetFramebufferSizeCallback(window, framebufferSizeCallbackAlias);
  glfwSetScrollCallback(window, scrollCallbackAlias);
}

bool Input::isCommandValid(int key, std::optional<Card*> active_card) {
  // key commands which require an active card
  std::vector<int> keys = {
    GLFW_KEY_A,
    GLFW_KEY_B,
    GLFW_KEY_C,
    GLFW_KEY_F,
    GLFW_KEY_G,
    GLFW_KEY_H,
    GLFW_KEY_N,
    GLFW_KEY_S,
    GLFW_KEY_X,
  };
  // if there is no active card, command is invalid
  if (std::find(keys.begin(), keys.end(), key) != keys.end() &&
      !active_card.has_value()) {
    return false;
  }
  return true;
}

void Input::processLocalInput(std::optional<Card*> active_card, double dt) {
  std::vector<int> keys = {
    GLFW_KEY_A,
    GLFW_KEY_B,
    GLFW_KEY_C,
    GLFW_KEY_D,
    GLFW_KEY_F,
    GLFW_KEY_G,
    GLFW_KEY_H,
    GLFW_KEY_M,
    GLFW_KEY_N,
    GLFW_KEY_S,
    GLFW_KEY_X,
    GLFW_KEY_Z,
  };
  for (int key : keys) {
    if (keys_[key]) {
      // if command is not valid, abort
      if (!isCommandValid(key, active_card)) {
	return;
      }

      // send command over net
      std::map<std::string, std::string> command_data;
      command_data["KEY"] = std::to_string(key);
      std::optional<std::string> card_id = std::nullopt;
      if (active_card.has_value()) {
	card_id = active_card.value()->getID();
	command_data["ACTIVE_CARD_ID"] = card_id.value();
      }
      if (network_ != nullptr) {
	sendCommandOverNetwork(KEY_COMMAND, command_data);
      }

      // run command locally
      runKeyCommand(key, p1_, card_id, dt);
    }
  }

  if (mouse_action_ != NONE) {
    runMouseCommand(p1_);
  }
}

void Input::processNetworkInput(double dt) {
  std::optional<NetworkCommand> cmd;
  cmd = network_->getNextCommand();

  if (!cmd.has_value()) {
    return;
  }

  if (std::stoi(cmd.value()["COMMAND_TYPE"]) == KEY_COMMAND) {
    int key = std::stoi(cmd.value()["KEY"]);
    runKeyCommand(key, p2_, cmd.value()["ACTIVE_CARD_ID"], dt);
  }
}

void Input::runKeyCommand(int key, Player* player, std::optional<std::string> active_card_id, double dt) {
  Card* active_card;
  if (active_card_id.has_value()) {
    active_card = player->getCardByCardID(active_card_id.value());
  }

  keys_[key] = false;
  switch(key) {

  // [a]ctivate
  case GLFW_KEY_A:
    player->activateCard(active_card, dt);
    break;

  // [b]anish
  case GLFW_KEY_B:
    player->banishCard(active_card, dt);
    break;

  // [c]hange battle position
  case GLFW_KEY_C:
    player->changeCardBattlePosition(active_card, dt);
    break;

  // [d]raw
  case GLFW_KEY_D:
    player->draw(dt);
    break;

  // [f]lip
  case GLFW_KEY_F:
    player->flipCard(active_card, dt);
    break;

  // to [g]raveyard
  case GLFW_KEY_G:
    player->sendCardToGY(active_card, dt);
    break;

  // to [h]and
  case GLFW_KEY_H:
    player->returnCardToHand(active_card, dt);
    break;

  // [m]ill
  case GLFW_KEY_M:
    player->mill(dt);
    break;

  // [n]ormal summon
  case GLFW_KEY_N:
    player->normalSummonCard(active_card, dt);
    break;

  // [s]et card
  case GLFW_KEY_S:
    player->setCard(active_card, dt);
    break;

  // [x] tsuk
  case GLFW_KEY_X:
    player->tsukCard(active_card, dt);
    break;

  // [z] shuffle hand
  case GLFW_KEY_Z:
    player->shuffleHand(dt);
    break;
  }
}

void Input::runMouseCommand(Player* player) {
  switch(mouse_action_) {

  // spread MultiCardZone
  case SCROLL_DOWN:
    player->spreadCards(mouse_pos_);
    break;

  // collapse MultiCardZone
  case SCROLL_UP:
    player->collapseCards(mouse_pos_);
    break;
  }
  mouse_action_ = NONE;
}

void Input::keyCallback(GLFWwindow* window, int key, int scancode, int action, int mode) {
  // supress warning for unused parameters
  (void)window;
  (void)scancode;
  (void)mode;

  // when a user presses the escape key, we set the WindowShouldClose property to true, closing the application
  if (key == GLFW_KEY_ESCAPE && action == GLFW_PRESS) {
    glfwSetWindowShouldClose(window, true);
  }

  if (key >= 0 && key < 1024){
      if (action == GLFW_PRESS)
	keys_[key] = true;
      else if (action == GLFW_RELEASE)
	keys_[key] = false;
    }
}

glm::vec2 Input::getMousePosition() {
  return mouse_pos_;
}

void Input::cursorPositionCallback(GLFWwindow* window, double xpos, double ypos) {
  // supress warning for unused parameters
  (void)window;

  mouse_pos_.x = xpos;
  mouse_pos_.y = ypos;
}

void Input::framebufferSizeCallback(GLFWwindow* window, int width, int height) {
  // supress warning for unused parameters
  (void)window;

  glViewport(0, 0, width, height);
}

void Input::scrollCallback(GLFWwindow* window, double xoffset, double yoffset) {
  // supress warning for unused parameters
  (void)window;
  (void)xoffset;
  if (yoffset == -1) {
    mouse_action_ = SCROLL_DOWN;
  } else if (yoffset == 1) {
    mouse_action_ = SCROLL_UP;
  }
}

void Input::sendCommandOverNetwork(NetworkCommandType command, std::map<std::string, std::string> command_data) {
  network_->sendCommand(command, command_data);
}
