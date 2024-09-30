#ifndef FIELD_H
#define FIELD_H

#include <vector>

#include <singlecardzone.hpp>
#include <renderer.hpp>
#include <graphic.hpp>
#include <config.hpp>

class Field {
public:
  Field(unsigned int player_num);
  void update(double dt);
  void render(Renderer* renderer);
  std::optional<SingleCardZone*> getFreeMZone();
  std::optional<SingleCardZone*> getFreeSTZone();
  std::optional<SingleCardZone*> getOccupiedZoneByCardID(std::string id);
  std::optional<Card*> getActiveCard(glm::vec2 mouse_pos);
  void removeCard(Card* card);
  std::optional<Card*> getCardByCardID(std::string card_id);

private:
  std::vector<SingleCardZone> mzones_;
  std::vector<SingleCardZone> stzones_;
  std::vector<std::string> token_passcodes_ {
    "73915052", // sheep token
    "29843092", // ojama green
    "29843093", // ojama yellow
    "29843094", // ojama black
  };
};

#endif
