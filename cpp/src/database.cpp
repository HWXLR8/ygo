#include <database.hpp>

sqlite3* Database::db_;
int Database::r_;
CardInfo Database::card_info_;

void Database::connect() {
  r_ = sqlite3_open("../netplay/sql/cards.db", &db_);
}

CardInfo Database::queryCardInfoByPasscode(std::string passcode) {
  sqlite3_stmt* stmt = 0;
  std::string q = "SELECT * FROM cards WHERE card_id=?;";
  r_ = sqlite3_prepare_v2(db_, q.c_str(), q.length(), &stmt, nullptr);
  r_ = sqlite3_exec(db_, "BEGIN TRANSACTION", 0, 0, 0 );
  sqlite3_bind_text(stmt, 1, passcode.c_str(), passcode.length(), SQLITE_TRANSIENT);

  while (sqlite3_step(stmt) == SQLITE_ROW ) {
    card_info_.passcode = std::to_string(sqlite3_column_int(stmt, 0));
    card_info_.card_name = std::string(reinterpret_cast<const char*>(sqlite3_column_text(stmt, 1)));
    card_info_.card_type = std::string(reinterpret_cast<const char*>(sqlite3_column_text(stmt, 2)));
    card_info_.card_subtype = std::string(reinterpret_cast<const char*>(sqlite3_column_text(stmt, 3)));
    card_info_.card_attribute = std::string(reinterpret_cast<const char*>(sqlite3_column_text(stmt, 4)));
    card_info_.monster_type = std::string(reinterpret_cast<const char*>(sqlite3_column_text(stmt, 5)));
    card_info_.monster_class = std::string(reinterpret_cast<const char*>(sqlite3_column_text(stmt, 6)));
    card_info_.monster_level = std::string(reinterpret_cast<const char*>(sqlite3_column_text(stmt, 7)));
    card_info_.monster_atk = std::string(reinterpret_cast<const char*>(sqlite3_column_text(stmt, 8)));
    card_info_.monster_def = std::string(reinterpret_cast<const char*>(sqlite3_column_text(stmt, 9)));
    card_info_.card_text = std::string(reinterpret_cast<const char*>(sqlite3_column_text(stmt, 10)));
  }
  r_ = sqlite3_step(stmt);
  r_ = sqlite3_clear_bindings(stmt);
  r_ = sqlite3_reset(stmt);
  return card_info_;
}

void Database::close() {
  sqlite3_close(db_);
}

void Database::checkErrors() {
  if (r_) {
    throw std::runtime_error(std::string("DB Error: ") + sqlite3_errmsg(db_));
    close();
  }
}
