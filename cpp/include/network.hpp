#ifndef NETWORK_H
#define NETWORK_H

#include <arpa/inet.h>

#include <map>
#include <string>
#include <optional>
#include <vector>
#include <mutex>
#include <queue>

#include <ydk.hpp>

enum ConnectionType {
  SERVER,
  CLIENT,
};

enum NetworkCommandType {
  MAIN_DECK_DATA,
  FUSION_DECK_DATA,
  KEY_COMMAND,
  MOUSE_COMMAND,
  RNG_SEED,
};

typedef std::map<std::string, std::string> NetworkCommand;

class Network {
public:
  Network(ConnectionType conn_type, std::optional<std::string> server_addr, std::optional<int> server_port);
  ~Network();
  void sendCommand(NetworkCommandType command, NetworkCommand command_data);
  std::optional<NetworkCommand> getNextCommand();
  std::string waitForSeed();
  void waitForDeck(DeckList& deck_list);

private:
  int sock_;
  int client_;
  sockaddr_in sockaddr_;
  ConnectionType conn_type_;
  std::optional<std::string> server_addr_;
  std::optional<int> server_port_;
  std::queue<NetworkCommand> command_queue_;

  void initServer();
  void initClient();
  void addCommandToQueue(NetworkCommand cmd);
  NetworkCommand parseCommandString(std::string cmd_str);
  std::vector<std::string> parsePasscodeString(std::string pass_str);
  void send(std::string data);
  void receive();
};

#endif
