#ifndef DATABASE_H
#define DATABASE_H

#include <sqlite3.h>
#include <string>
#include <iostream>

struct CardInfo {
  std::string passcode;
  std::string card_name;
  std::string card_type;
  std::string card_subtype;
  std::string card_attribute;
  std::string monster_type;
  std::string monster_class;
  std::string monster_level;
  std::string monster_atk;
  std::string monster_def;
  std::string card_text;

  void print() {
    std::cout << "PASSCODE\n" << passcode << "\n" << std::endl;
    std::cout << "CARD NAME\n" << card_name << "\n" << std::endl;
    std::cout << "CARD TYPE\n" << card_type << "\n" << std::endl;
    std::cout << "CARD SUBTYPE\n" << card_subtype << "\n" << std::endl;
    std::cout << "CARD ATTRIBUTE\n" << card_attribute << "\n" << std::endl;
    std::cout << "MONSTER TYPE\n" << monster_type << "\n" << std::endl;
    std::cout << "MONSTER CLASS\n" << monster_class << "\n" << std::endl;
    std::cout << "MONSTER LEVEL\n" << monster_level << "\n" << std::endl;
    std::cout << "MONSTER ATK\n" << monster_atk << "\n" << std::endl;
    std::cout << "MONSTER DEF\n" << monster_def << "\n" << std::endl;
    std::cout << "CARD TEXT\n" << card_text << "\n" << std::endl;
  }
};

class Database {

 public:
  static void connect();
  static void close();
  static CardInfo queryCardInfoByPasscode(std::string passcode);

 private:
  static sqlite3* db_;
  static int r_;
  static CardInfo card_info_;

  Database() {}
  static void checkErrors();

};

#endif
