#include <glad/glad.h>
#include <GLFW/glfw3.h>
#include <glm/gtc/type_ptr.hpp>

#include <thread>

#include <game.hpp>
#include <resource_manager.hpp>
#include <renderer.hpp>
#include <mixer.hpp>
#include <config.hpp>
#include <rng.hpp>

Renderer *renderer;

Game::Game(OptionParser* opts) {
  // window/GL
  initGLFW();
  initGLAD();
  initGL();

  // command line args
  parseOpts(opts);

  // db
  Database::connect();

  // sound
  Mixer::init();
  Mixer::loadSoundFromFile("assets/draw.wav", "draw");
  Mixer::loadSoundFromFile("assets/hand_shuffle.wav", "hand_shuffle");
  Mixer::loadSoundFromFile("assets/generic_move.wav", "generic_move");
  Mixer::loadSoundFromFile("assets/change_position.wav", "change_position");
  std::thread tmixer(&Mixer::startMixer);
  tmixer.detach();

  // main shader
  ResourceManager::loadShader("shader/vert.glsl", "shader/frag.glsl", nullptr, "static_image");
  glm::mat4 projection = glm::ortho(0.0f, SCREEN_SIZE.x, SCREEN_SIZE.y, 0.0f, -100.0f, 100.0f);
  ResourceManager::getShader("static_image").use().setInteger("image", 0);
  ResourceManager::getShader("static_image").setMatrix4("projection", projection);
  Shader shader = ResourceManager::getShader("static_image");
  renderer = new Renderer(shader);

  // bg shader
  ResourceManager::loadShader("shader/vert.glsl", "shader/frag_scroll.glsl", nullptr, "scrolling_image");
  ResourceManager::getShader("scrolling_image").use().setInteger("image", 0);
  ResourceManager::getShader("scrolling_image").setMatrix4("projection", projection);
  bg_ = new Graphic("assets/bricc.jpg", glm::vec2{0, 0}, SCREEN_SIZE, false);
  bg_->setColor(glm::vec4{0.7, 0.95, 0.0, 0.8});

  // playmat
  playmat_ = new Graphic("../netplay/assets/inkscape/playmat_stroke.png", COORD.playmat, PLAYMAT_SIZE, true);
  playmat_fill_ = new Graphic("../netplay/assets/inkscape/playmat_fill.png", COORD.playmat, PLAYMAT_SIZE, true);
  playmat_fill_->setColor(glm::vec4{1.0, 1.0, 1.0, 1.0});
  playmat_shadow_ = new Graphic("../netplay/assets/inkscape/playmat_fill.png", glm::vec2{COORD.playmat.x + 50, COORD.playmat.y + 50}, PLAYMAT_SIZE, true);
  playmat_shadow_->setColor(glm::vec4{1.0, 1.0, 1.0, 0.4});

  // sync RNG seeds with opponent
  if (network_ != nullptr) {
    syncRNG();
  }

  // load p1 deck from file
  YDK ydk(opts->getOptValue("-d"));
  DeckList p1_deck;
  p1_deck.main_deck = ydk.getMainDeck();
  p1_deck.fusion_deck = ydk.getFusionDeck();

  // sync deck with opponent
  DeckList p2_deck;
  if (network_ != nullptr) {
    syncDecks(p1_deck, p2_deck);
  }

  // player init
  p1_ = new Player(1, p1_deck);
  p2_ = new Player(2, p1_deck);
  mag_card_ = new MagCard();

  input_ = new Input(window_, p1_, p2_, network_);
}

Game::~Game() {
  ResourceManager::clear();
  glfwTerminate();
  delete renderer;
  delete bg_;
  delete playmat_;
  delete playmat_fill_;
  delete playmat_shadow_;
  delete p1_;
  delete mag_card_;
  delete input_;
  delete network_;
}

void Game::initGLFW() {
  glfwInit();
  glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
  glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
  glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
  #ifdef __APPLE__
  glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE);
  #endif
  glfwWindowHint(GLFW_RESIZABLE, false);
  window_ = glfwCreateWindow(SCREEN_SIZE.x, SCREEN_SIZE.y, "ygo", nullptr, nullptr);
  glfwMakeContextCurrent(window_);
}

void Game::initGLAD() {
  if (!gladLoadGLLoader((GLADloadproc)glfwGetProcAddress)) {
    throw std::runtime_error("Failed to initialize GLAD");
    return;
  }
}

void Game::initGL() {
  glViewport(0, 0, SCREEN_SIZE.x, SCREEN_SIZE.y);
  // glEnable(GL_CULL_FACE);
  glEnable(GL_BLEND);
  glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
}

// ensure screen coordinates matches pixel coordinates
void Game::setViewport() {
  int width, height;
  glfwGetFramebufferSize(window_, &width, &height);
  glViewport(0, 0, width, height);
}

void Game::update(double dt) {
  p1_->update(dt);
  p2_->update(dt);
  getActiveCard();
  mag_card_->update(active_card_);
}

void Game::render() {
  Shader static_image = ResourceManager::getShader("static_image");
  Shader scrolling_image = ResourceManager::getShader("scrolling_image");
  renderer->setShader(scrolling_image);
  bg_->render(renderer);
  renderer->setShader(static_image);

  playmat_shadow_->render(renderer);
  playmat_fill_->render(renderer);
  playmat_->render(renderer);

  p1_->render(renderer);
  p2_->render(renderer);
  mag_card_->render(renderer);
}

void Game::run() {
  double dt = 0.0;
  double lastFrame = glfwGetTime();
  while (!glfwWindowShouldClose(window_)) {
    double currentFrame = glfwGetTime();
    dt = currentFrame - lastFrame;
    lastFrame = currentFrame;
    glfwPollEvents();
    input_->processLocalInput(active_card_, dt);
    if (network_ != nullptr) {
      input_->processNetworkInput(dt);
    }
    update(dt);
    glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);
    render();
    glfwSwapBuffers(window_);
  }
}

void Game::getActiveCard() {
  active_card_ = p1_->getActiveCard(input_->getMousePosition());
  if (active_card_.has_value()) {
    return;
  }
}

void Game::parseOpts(OptionParser* opts) {
  if (!opts->optExists("-s") &&
      !opts->optExists("-c") &&
      !opts->optExists("-g")) {
    throw std::runtime_error("either option -s[erver] or -c[lient] must be specified");
  }

  if (opts->optExists("-s") &&
      opts->optExists("-c")) {
    throw std::runtime_error("options '-s' and '-c' cannot be used simultaneously");
  }

  // deck
  if (!opts->optExists("-d")) {
    throw std::runtime_error("please specify a deck using -d");
  }

  // server
  if (opts->optExists("-s")) {
    network_ = new Network(SERVER, std::nullopt, std::nullopt);
  }

  // client
  if (opts->optExists("-c")) {
    std::string server_ip = opts->getOptValue("-c");
    network_ = new Network(CLIENT, server_ip, NETWORK_PORT);
  }

  // debug mode
  if (opts->optExists("-g")) {
    network_ = nullptr;
  }
}

void Game::syncRNG() {
  std::cout << "synchronizing RNG between players..." << std::endl;;

  std::string seed1 = RNG::randID(8);
  RNG::seedRNG(1, seed1);
  NetworkCommand cmd;
  cmd["SEED"] = seed1;
  std::cout << "sending random seed(" << seed1 << ") to opponent" << std::endl;
  network_->sendCommand(RNG_SEED, cmd);

  std::string seed2 = network_->waitForSeed();
  std::cout << "received random seed(" << seed2 << ") from opponent" << std::endl;
  RNG::seedRNG(2, seed2);
}

void Game::syncDecks(DeckList p1_deck, DeckList& p2_deck) {
  NetworkCommand cmd;
  std::string passcodes = "";

  // send p1 main deck to opponent
  for (std::string passcode : p1_deck.main_deck) {
    passcodes += passcode;
    passcodes += ",";
  }
  cmd["PASSCODES"] = passcodes;
  network_->sendCommand(MAIN_DECK_DATA, cmd);

  // send p1 fusion deck to opponent
  cmd.clear();
  passcodes = "";
  for (std::string passcode : p1_deck.fusion_deck) {
    passcodes += passcode;
    passcodes += ",";
  }
  cmd["PASSCODES"] = passcodes;
  network_->sendCommand(FUSION_DECK_DATA, cmd);

  // wait for p2 deck to arrive over the net
  network_->waitForDeck(p2_deck);
}
