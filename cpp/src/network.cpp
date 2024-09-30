#include <sys/socket.h>
#include <unistd.h>
#include <iostream>
#include <stdexcept>
#include <thread>

#include <network.hpp>
#include <config.hpp>

Network::Network(ConnectionType conn_type, std::optional<std::string> server_addr, std::optional<int> server_port) {
  conn_type_ = conn_type;
  server_addr_ = server_addr;
  server_port_ = server_port;

  if (conn_type_ == SERVER) {
    initServer();
  } else if (conn_type_ == CLIENT) {
    initClient();
  }
}

Network::~Network() {
  if (conn_type_ == SERVER) {
    close(client_);
    close(sock_);
  }
}

void Network::initServer() {
  // create socket
  sock_ = socket(AF_INET, SOCK_STREAM, 0);
  if (sock_ == -1) {
    throw std::runtime_error("failed to create socket");
  }

  // reuse ports to avoid "already in use" errors
  int optval = 1;
  setsockopt(sock_, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, &optval, sizeof(optval));

  // specify which port
  sockaddr_.sin_family = AF_INET;
  sockaddr_.sin_addr.s_addr = INADDR_ANY;
  sockaddr_.sin_port = htons(NETWORK_PORT);

  // bind to port
  if (bind(sock_, (struct sockaddr*)&sockaddr_, sizeof(sockaddr_)) < 0) {
    throw std::runtime_error("failed to bind to port");
  }

  // begin listening
  if (listen(sock_, 1) < 0) {
    throw std::runtime_error("failed to listen on socket");
  }

  // wait for client connection
  std::cout << "waiting for client.." << std::endl;
  auto addrlen = sizeof(sockaddr_);
  client_ = accept(sock_, (struct sockaddr*)&sockaddr_, (socklen_t*)&addrlen);
  if (client_ < 0) {
    throw std::runtime_error("failed to connect to client");
  }

  std::string client_ip_ = std::string(inet_ntoa(sockaddr_.sin_addr));
  std::cout << "client " << client_ip_ << " connected" << std::endl;

  // read from client in separate thread
  std::thread recv_th(&Network::receive, this);
  recv_th.detach();
}

void Network::initClient() {
  std::string server_addr = server_addr_.value();
  int server_port = server_port_.value();

  if ((sock_ = socket(AF_INET, SOCK_STREAM, 0)) < 0 ) {
    throw std::runtime_error("failed to creat socket");
  }

  struct sockaddr_in serv_addr;
  serv_addr.sin_family = AF_INET;
  serv_addr.sin_port = htons(server_port);

  // convert ipv4 and ipv6 addresses to binary
  if (inet_pton(AF_INET, server_addr.c_str(), &serv_addr.sin_addr) <= 0) {
    throw std::runtime_error("invalid server address");
  }

  std::cout << "Attempting to connect to " << server_addr << ":" << server_port << std::endl;
  while (connect(sock_, (struct sockaddr*)&serv_addr, sizeof(serv_addr)) < 0) {
    std::cout << "failed so connect to server, retrying...";
    sleep(1);
  }
  std::cout << "Connected to " << server_addr << ":" << server_port << std::endl;

  // read from server in separate thread
  std::thread recv_th(&Network::receive, this);
  recv_th.detach();
}

std::optional<NetworkCommand> Network::getNextCommand() {
  if (command_queue_.empty()) {
    return std::nullopt;
  }
  NetworkCommand cmd = command_queue_.front();
  std::mutex mtx;
  mtx.lock();
  command_queue_.pop();
  mtx.unlock();
  return cmd;
}

void Network::addCommandToQueue(NetworkCommand cmd) {
  std::mutex mtx;
  mtx.lock();
  command_queue_.push(cmd);
  mtx.unlock();
}

NetworkCommand Network::parseCommandString(std::string cmd_str) {
  size_t pos = 0;
  std::string delim = ";";
  std::string token;
  NetworkCommand cmd;
  int parity = 1;
  std::string prev;

  while ((pos = cmd_str.find(delim)) != std::string::npos) {
    token = cmd_str.substr(0, pos);
    cmd_str.erase(0, pos + 1);

    if (parity % 2 == 0) {
      cmd[prev] = token;
    } else {
      prev = token;
    }
    parity++;
  }
  return cmd;
}

std::vector<std::string> Network::parsePasscodeString(std::string pass_str) {
  size_t pos = 0;
  std::string delim = ",";
  std::string token;
  std::string prev;
  std::vector<std::string> passcodes;

  while ((pos = pass_str.find(delim)) != std::string::npos) {
    token = pass_str.substr(0, pos);
    pass_str.erase(0, pos + 1);
    passcodes.push_back(token);
  }
  return passcodes;
}

void Network::sendCommand(NetworkCommandType command, NetworkCommand command_data) {
  std::string msg = "COMMAND_TYPE;" + std::to_string(command) + ";";
  for (auto const& [key, val] : command_data) {
    msg += key + ";" + val + ";";
  }
  this->send(msg);
}

void Network::send(std::string data) {
  int conn;
  if (conn_type_ == SERVER) {
    conn = client_;
  } else if (conn_type_ == CLIENT) {
    conn = sock_;
  }

  // convert to network byte order
  uint32_t len = htonl(data.length());
  // send length first
  ::send(conn, &len, sizeof(len), 0);
  // now send the actual message
  ::send(conn, data.c_str(), data.size(), 0);
}

void Network::receive() {
  int conn;
  if (conn_type_ == SERVER) {
    conn = client_;
  } else if (conn_type_ == CLIENT) {
    conn = sock_;
  }

  uint32_t len;
  int result;
  while (true) {
    // read msg length first (4 bytes)
    result = ::read(conn, &len, sizeof(len));
    if (!result) {
      throw std::runtime_error("lost connection to server");
    }
    // change byte order from network->host
    len = ntohl(len);
    // read actual message
    char cmsg[len];
    result = ::read(conn, cmsg, len);
    if (!result) {
      throw std::runtime_error("lost connection to server");
    }

    std::string msg(cmsg, len);
    std::cout << msg << std::endl;
    addCommandToQueue(parseCommandString(msg));
  }
}

std::string Network::waitForSeed() {
  std::optional<NetworkCommand> cmd;
  while (!cmd.has_value()) {
    cmd = getNextCommand();
  }
  // did we receive an RNG_SEED command?
  int cmd_type = std::stoi(cmd.value()["COMMAND_TYPE"]);
  if (cmd_type != RNG_SEED) {
    throw std::runtime_error("received unexpected command while waiting for RNG seed");
  }
  return cmd.value()["SEED"];
}

void Network::waitForDeck(DeckList& deck_list) {
  std::optional<NetworkCommand> cmd;

  // wait for main deck to arrive
  while (!cmd.has_value()) {
    cmd = getNextCommand();
  }
  // did we receive a MAIN_DECK_DATA command?
  int cmd_type = std::stoi(cmd.value()["COMMAND_TYPE"]);
  if (cmd_type != MAIN_DECK_DATA) {
    throw std::runtime_error("recieved unexpected command while waiting for opponent main deck");
  }

  deck_list.main_deck = parsePasscodeString(cmd.value()["PASSCODES"]);

  // wait for fusion deck to arrive
  cmd = std::nullopt;
  while (!cmd.has_value()) {
    cmd = getNextCommand();
  }
  // did we receive a FUSION_DECK_DATA command?
  cmd_type = std::stoi(cmd.value()["COMMAND_TYPE"]);
  if (cmd_type != FUSION_DECK_DATA) {
    throw std::runtime_error("recieved unexpected command while waiting for opponent fusion deck");
  }

  deck_list.fusion_deck = parsePasscodeString(cmd.value()["PASSCODES"]);
}
